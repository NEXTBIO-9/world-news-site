#!/usr/bin/env python3
"""Fetch official disease-outbreak notices; never infer active outbreak risk."""
import json, re, urllib.request, xml.etree.ElementTree as ET
from pathlib import Path
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
OUT=Path('data/bio-official.json')
SOURCES=[('WHO Disease Outbreak News','https://www.who.int/feeds/entity/csr/don/en/rss.xml'),('WHO News','https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml')]
KEYWORDS=re.compile(r'outbreak|disease|virus|cholera|measles|ebola|influenza|infection|epidemic|pandemic|infectious|health emergency',re.I)
def tagtext(node,name):
    for child in node:
        if child.tag.rsplit('}',1)[-1]==name:return ''.join(child.itertext()).strip()
    return ''
def main():
    items=[]
    for source,url in SOURCES:
        try:
            req=urllib.request.Request(url,headers={'User-Agent':'NEXTBIO-OfficialNoticeMonitor/1.0'})
            with urllib.request.urlopen(req,timeout=18) as response:raw=response.read(2_000_000)
            xml=ET.fromstring(raw)
            entries=[x for x in xml.iter() if x.tag.rsplit('}',1)[-1] in ('item','entry')]
            for e in entries[:60]:
                title=tagtext(e,'title');link=tagtext(e,'link');published=tagtext(e,'pubDate') or tagtext(e,'published') or tagtext(e,'updated')
                if not link:
                    for c in e:
                        if c.tag.rsplit('}',1)[-1]=='link':link=c.attrib.get('href','');break
                if not title or not link.startswith('https://') or not KEYWORDS.search(title):continue
                try:stamp=parsedate_to_datetime(published).astimezone(timezone.utc).isoformat()
                except Exception:
                    try:stamp=datetime.fromisoformat(published.replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
                    except Exception:stamp=''
                items.append({'title':title[:240],'url':link,'source':source,'published':stamp})
        except Exception as e:print('source unavailable:',source,str(e)[:180])
    seen=set();unique=[]
    for a in sorted(items,key=lambda x:x['published'],reverse=True):
        if a['url'] not in seen:seen.add(a['url']);unique.append(a)
    if not unique and OUT.exists():
        print('No new official data; retaining previous verified source snapshot')
        return
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({'updated':datetime.now(timezone.utc).isoformat(),'items':unique[:50]},ensure_ascii=False,indent=2)+'\n')
    print('official notices:',len(unique))
if __name__=='__main__':main()
