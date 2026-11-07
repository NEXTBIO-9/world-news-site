#!/usr/bin/env python3
"""Translate collected English news titles, without changing the collector or site UI."""
import html
import json
import os
import re
import subprocess
import time
import urllib.parse
import urllib.request
from pathlib import Path

DATA = Path('data/articles.json')
KEY = os.getenv('GOOGLE_TRANSLATE_API_KEY', '').strip()
LIMIT = max(0, min(int(os.getenv('TRANSLATE_MAX_NEW', '60')), 150))

def load_old():
    try:
        previous = subprocess.run(['git','show','HEAD:data/articles.json'], capture_output=True, text=True, check=True)
        return json.loads(previous.stdout).get('articles', [])
    except (subprocess.CalledProcessError, ValueError, OSError):
        return []

def main():
    if not DATA.exists():
        print('No articles.json: skipping translation'); return
    payload = json.loads(DATA.read_text(encoding='utf-8'))
    articles = payload.get('articles', [])
    if not isinstance(articles, list):
        raise ValueError('articles field must be a list')
    cache = {}
    for item in load_old():
        if isinstance(item, dict) and item.get('title_ko'):
            cache[(item.get('url'), item.get('title'))] = item['title_ko']
    count=0
    for a in articles:
        if not isinstance(a,dict): continue
        title = str(a.get('title') or '').strip()
        if not title: continue
        if re.search('[가-힣]',title):
            a['title_ko'] = title
            continue
        if a.get('title_ko'): continue
        previous = cache.get((a.get('url'),title))
        if previous:
            a['title_ko'] = previous
            continue
        if not KEY or count>=LIMIT: continue
        try:
            body = urllib.parse.urlencode({'q':title,'source':'en','target':'ko','format':'text'}).encode()
            url = 'https://translation.googleapis.com/language/translate/v2?key=' + urllib.parse.quote(KEY, safe='')
            req = urllib.request.Request(url,body,headers={'Content-Type':'application/x-www-form-urlencoded'},method='POST')
            with urllib.request.urlopen(req,timeout=12) as res:
                data=json.load(res)
            result=html.unescape(data['data']['translations'][0]['translatedText']).strip()
            if result:
                a['title_ko']=result
                count+=1
            time.sleep(.1)
        except Exception as e:
            print('Translation API failed; original titles kept:', type(e).__name__,str(e)[:120])
            break
    if count or any(a.get('title_ko') for a in articles if isinstance(a,dict)):
        DATA.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(f'New translations: {count}, Korean titles available: {sum(bool(a.get("title_ko")) for a in articles if isinstance(a,dict))}')
    if not KEY: print('Translation disabled: add GOOGLE_TRANSLATE_API_KEY GitHub Actions secret')

if __name__=='__main__': main()
