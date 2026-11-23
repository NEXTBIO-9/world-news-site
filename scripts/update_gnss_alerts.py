#!/usr/bin/env python3
"""Index publicly reported Northeast Asian GNSS aviation safety advisories."""
import datetime as dt
import email.utils
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'gnss-alerts.json'
NOW=dt.datetime.now(dt.timezone.utc)
QUERIES=[
 'site:aim.koca.go.kr NOTAM GPS interference RKRR',
 'site:icao.int GNSS interference Incheon Korea',
 'site:easa.europa.eu GNSS interference Japan Korea',
 'site:mlit.go.jp GNSS interference NOTAM Japan',
 'site:mofa.go.kr GPS interference ICAO'
]
region=re.compile(r'korea|korean|incheon|rkrr|japan|japanese|okinawa|한국|일본|인천|오키나와',re.I)
subject=re.compile(r'GNSS|GPS|jamming|spoofing|interference|전파간섭|교란',re.I)
items={}
for query in QUERIES:
 try:
  url='https://news.google.com/rss/search?'+urllib.parse.urlencode({'q':query,'hl':'en-US','gl':'US','ceid':'US:en'})
  req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
  with urllib.request.urlopen(req,timeout=25) as response: root=ET.fromstring(response.read(1500000))
  for entry in root.findall('./channel/item'):
   title=(entry.findtext('title') or '').strip()
   description=re.sub(r'<[^>]+>',' ',entry.findtext('description') or '')
   if not (region.search(title+' '+description) and subject.search(title)):continue
   src=entry.find('source');publisher=(src.text or '').strip() if src is not None else ''
   if not any(v in publisher.lower() for v in ('icao','easa','ministry','government','civil aviation','korea','japan')):continue
   link=(entry.findtext('link') or '').strip()
   if not link.startswith('https://'):continue
   try: published=email.utils.parsedate_to_datetime(entry.findtext('pubDate') or '').astimezone(dt.timezone.utc)
   except Exception:continue
   if published>NOW or published<NOW-dt.timedelta(days=365):continue
   key=re.sub(r'\W+','',title.lower())
   items[key]={'title':title,'published':published.date().isoformat(),'source':publisher,'url':link,'type':'공식 발표 관련 보도'}
 except Exception as exc:print('Feed unavailable',type(exc).__name__,str(exc)[:100])
seed={'title':'인천 FIR GPS 신호 불안정 경고 — NOTAM RKRR Z0817/26','published':'2026-10-30','source':'대한민국 항공고시 재게시 (Safe Airspace)','url':'https://safeairspace.net/south-korea/','type':'공고 (유효기간 2026-11-30까지 · 원문 확인 필요)'}
result=sorted([seed]+list(items.values()),key=lambda x:x['published'],reverse=True)[:10]
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps({'last_checked':NOW.isoformat(timespec='seconds'),'items':result},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('Indexed',len(result),'GNSS notices')
