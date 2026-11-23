#!/usr/bin/env python3
"""Daily public Korean Red Cross red-cell inventory snapshot; fail closed on parsing."""
import datetime as dt
import html
import json
import pathlib
import re
import urllib.request

ROOT=pathlib.Path(__file__).resolve().parents[1]
OUT=ROOT/'data'/'blood-supply.json'
URL='https://www.bloodinfo.net/knrcbs/bi/info/bldHoldSttus.do?mi=1046'
HEADERS={'User-Agent':'Mozilla/5.0 (compatible; NEXTBIO-public-data/1.0)','Accept-Language':'ko-KR,ko;q=0.9'}
now=dt.datetime.now(dt.timezone.utc)
old={}
if OUT.exists():
 try:old=json.loads(OUT.read_text(encoding='utf-8'))
 except (ValueError,OSError):pass
result={'source':'대한적십자사 혈액관리본부','source_url':URL,'last_checked':now.isoformat(timespec='seconds'),'observation_date':old.get('observation_date'),'total_days':old.get('total_days'),'blood_types':old.get('blood_types',{}),'history':old.get('history',[]),'status':'unavailable'}
try:
 request=urllib.request.Request(URL,headers=HEADERS)
 with urllib.request.urlopen(request,timeout=25) as response:
  raw=response.read(2000000).decode('utf-8','replace')
 clean=html.unescape(re.sub(r'<[^>]*>',' ',re.sub(r'<(script|style)\\b[^>]*>.*?</\\1>',' ',raw,flags=re.I|re.S)))
 clean=re.sub(r'\\s+',' ',clean)
 date_match=re.search(r'(20\\d{2})[.\\-/]\\s*(\\d{1,2})[.\\-/]\\s*(\\d{1,2})\\s*기준',clean)
 # The Red Cross page lists red-cell inventory as a 5-column table:
 # 보유상태 | 합계 | A형 | B형 | O형 | AB형
 match=re.search(r'보유상태\\s*(\\d+(?:\\.\\d+)?)\\s*일?\\s*(\\d+(?:\\.\\d+)?)\\s*일?\\s*(\\d+(?:\\.\\d+)?)\\s*일?\\s*(\\d+(?:\\.\\d+)?)\\s*일?\\s*(\\d+(?:\\.\\d+)?)\\s*일?',clean)
 if not date_match or not match:raise ValueError('Red-cell holdings fields not found; site markup may have changed')
 day=dt.date(*map(int,date_match.groups())).isoformat()
 vals=list(map(float,match.groups()))
 if any(not 0<=v<=30 for v in vals):raise ValueError('Out-of-range holdings')
 result.update(observation_date=day,total_days=vals[0],blood_types=dict(zip(('A','B','O','AB'),vals[1:])),status='ok')
 history=[x for x in result['history'] if isinstance(x,dict) and x.get('date')!=day]
 history.append({'date':day,'days':vals[0]})
 result['history']=sorted(history,key=lambda x:x['date'])[-30:]
except Exception as exc:
 result['error']=str(exc)[:150]
 print('Unable to refresh Red Cross inventory:',exc)
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\\n',encoding='utf-8')
print('status:',result['status'],'observation:',result['observation_date'])
