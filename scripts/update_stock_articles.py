#!/usr/bin/env python3
"""Fetch Korean-language investment reporting from Google News RSS. Stdlib only."""
import datetime as dt
import email.utils
import html
import json
import pathlib
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'stock' / 'data' / 'articles.json'
# Search queries deliberately require Korean reporting, including international topics.
SEARCHES = [
 ('미국','공시','미국 SEC 기업 공시 10-K 10-Q'),
 ('미국','실적','미국 기업 실적 가이던스 매출 EPS'),
 ('미국','기관','미국 13F 기관투자자 보유 지분'),
 ('미국','산업','미국 반도체 AI 산업 투자 전망'),
 ('한국','공시','금융감독원 DART 기업 공시 주요사항'),
 ('한국','실적','코스피 코스닥 기업 실적 영업이익'),
 ('한국','기관','국내 주식 외국인 기관 수급'),
 ('한국','산업','한국 반도체 배터리 산업 투자'),
 ('글로벌','거시경제','미국 연준 금리 인플레이션 국채금리'),
 ('글로벌','거시경제','글로벌 경제 유동성 달러 환율'),
 ('글로벌','기관','글로벌 ETF 자금 유입 유출'),
 ('글로벌','산업','글로벌 공급망 에너지 원자재 투자'),
]
HANGUL = re.compile(r'[가-힣]')
TAG = re.compile(r'<[^>]*>')
MAX_AGE_DAYS = 14

def get_rss(query):
    params = urllib.parse.urlencode({'q':query+' when:14d','hl':'ko','gl':'KR','ceid':'KR:ko'})
    url='https://news.google.com/rss/search?'+params
    req=urllib.request.Request(url,headers={'User-Agent':'NEXTBIO-Stock-Research/1.0 (public news aggregator)'})
    with urllib.request.urlopen(req,timeout=20) as resp:
        return ET.fromstring(resp.read(2_000_000))

def clean(value):
    return re.sub(r'\s+',' ',html.unescape(TAG.sub('',value or ''))).strip()

def main():
    now=dt.datetime.now(dt.timezone.utc)
    found={}
    failures=[]
    for region,category,query in SEARCHES:
        try:
            tree=get_rss(query)
            for item in tree.findall('./channel/item')[:25]:
                title=clean(item.findtext('title'))
                link=(item.findtext('link') or '').strip()
                source=clean(item.findtext('source')) or '언론사'
                if not HANGUL.search(title) or not link.startswith('https://'):
                    continue
                try:
                    published=email.utils.parsedate_to_datetime(item.findtext('pubDate'))
                    if published.tzinfo is None:published=published.replace(tzinfo=dt.timezone.utc)
                    if not (now-dt.timedelta(days=MAX_AGE_DAYS)<=published<=now+dt.timedelta(hours=1)):continue
                except (TypeError,ValueError,OverflowError):continue
                # Google News titles often append the publisher; avoid duplication.
                if title.endswith(' - '+source):title=title[:-(len(source)+3)].strip()
                if len(title)<12 or not HANGUL.search(title):continue
                key=re.sub(r'\W+','',title).lower()
                if key not in found:
                    found[key]={'title':title,'url':link,'source':source,'region':region,'category':category,'published':published.isoformat()}
        except Exception as exc:
            failures.append(f'{region}/{category}: {type(exc).__name__}: {exc}')
        time.sleep(.3)
    # Preserve the last good dataset if all sources fail.
    if not found:
        print('No new articles; existing file preserved. Errors:',failures)
        if not OUT.exists():raise RuntimeError('No article data available')
        return
    payload={'updated_at':now.isoformat(),'articles':sorted(found.values(),key=lambda x:x['published'],reverse=True)[:240],'source':'Google News RSS (Korean-language news search)','failures':failures}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Saved',len(payload['articles']),'Korean articles; errors:',len(failures))

if __name__=='__main__':main()
