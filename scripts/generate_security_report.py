#!/usr/bin/env python3
"""Public-source security assessments. Requires OPENAI_API_KEY for generation."""
import argparse, datetime as dt, hashlib, json, os, re, sys, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
INPUT=ROOT/"data/articles.json"
OUTPUT=ROOT/"data/security_reports.json"
TOPICS={
 "east-asia": {"name":"동아시아 안보정세","terms":["중국","대만","북한","일본","한미","한반도","taiwan","china","japan","north korea","south korea","indo-pacific","missile","military","defense","security"]},
 "us-china":{"name":"미중 전략경쟁","terms":["미중","미국","중국","관세","반도체","taiwan","china","united states","tariff","semiconductor","sanction"]},
 "middle-east":{"name":"중동 안보정세","terms":["중동","이스라엘","이란","가자","레바논","시리아","israel","iran","gaza","hamas","hezbollah","syria"]},
 "europe":{"name":"유럽 안보정세","terms":["우크라이나","러시아","나토","유럽","ukraine","russia","nato","europe"]},
}
ALLOWED={"외교·국제","분쟁·군사","정치"}
def load():
    if not INPUT.exists(): return []
    obj=json.loads(INPUT.read_text(encoding="utf-8"))
    return obj.get("articles",[]) if isinstance(obj,dict) else []
def select(topic, hours, now):
    chosen=[]
    for a in load():
        if not isinstance(a,dict) or not a.get("url") or not a.get("source"): continue
        try: published=dt.datetime.fromisoformat(a["published"].replace("Z","+00:00"))
        except (ValueError,KeyError,TypeError): continue
        if not 0 <= (now-published).total_seconds() <= hours*3600: continue
        title=a.get("title_ko") or a.get("title") or ""
        raw=" ".join(str(a.get(k) or "") for k in ("title","title_ko","summary","category","countries")).lower()
        if not any(t in raw for t in TOPICS[topic]["terms"]): continue
        if a.get("category") not in ALLOWED and not any(t in raw for t in ("military","defense","missile","군사","안보","전쟁","분쟁")): continue
        chosen.append({"title":title,"source":a["source"],"url":a["url"],"published":a["published"],"excerpt":str(a.get("summary") or "")[:450]})
    seen=set(); unique=[]
    for a in sorted(chosen,key=lambda a:a["published"],reverse=True):
        key=re.sub(r"\W+","",a["title"].lower())
        if key in seen: continue
        seen.add(key);unique.append(a)
    return unique[:35]
def generate(topic,mode,articles):
    key=os.environ.get("OPENAI_API_KEY","")
    if not key: raise RuntimeError("OPENAI_API_KEY is not configured; no report will be published")
    model=os.environ.get("SECURITY_REPORT_MODEL","gpt-4.1-mini")
    instructions=("한국어 공개정보(OSINT) 국제안보 분석가. 국가기관을 사칭하지 마라. "
      "제공된 제목·발췌문에 없는 사실을 만들어내지 마라. 기사 본문을 읽었다고 주장하지 마라. "
      "기사 제목과 짧은 발췌문만 있으므로 심층 사실검증을 했다고 주장하지 마라. "
      "독립 출처의 교차검증이 불가능하거나 실질적 정세 변화가 불명확하면 publish=false. "
      "사실·분석·전망을 구분하고 불확실성을 명시하라. "
      "위험 단계는 충분한 증거가 없으면 '평가 불가'로 표기. "
      "아래 JSON 형식만 반환: "
      '{"publish":boolean,"headline":string,"key_judgments":[string],"situation":[string],'
      '"implications":[string],"outlook_7d":[string],"outlook_30d":[string],'
      '"indicators":[string],"confidence":"높음|보통|낮음","risk":"안정|관찰|주의|경계|심각|평가 불가",'
      '"limitations":string,"source_indices":[integer]}. '
      "source_indices는 입력 기사 번호(0부터 시작), 실제 판단 근거만 기재. "
      "과도한 추측이나 기사 제목만으로 사건이 확인된 것처럼 쓰지 마라.")
    payload={"model":model,"temperature":0.2,"response_format":{"type":"json_object"},
             "messages":[{"role":"system","content":instructions},
             {"role":"user","content":json.dumps({"topic":TOPICS[topic]["name"],"mode":mode,"articles":articles},ensure_ascii=False)}]}
    req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},method="POST")
    with urllib.request.urlopen(req,timeout=90) as response: result=json.load(response)
    return json.loads(result["choices"][0]["message"]["content"])
def valid(report,articles):
    if report.get("publish") is not True:return False
    ids=report.get("source_indices",[])
    if not isinstance(ids,list) or any(type(i)!=int or i<0 or i>=len(articles) for i in ids):return False
    selected=[articles[i] for i in set(ids)]
    if len(selected)<3 or len({a["source"].strip().lower() for a in selected})<3:return False
    if report.get("confidence") not in ("높음","보통","낮음"):return False
    if report.get("risk") not in ("안정","관찰","주의","경계","심각","평가 불가"):return False
    if not isinstance(report.get("headline"),str) or len(report["headline"])<10:return False
    for key in ("key_judgments","situation","implications","outlook_7d","outlook_30d","indicators"):
        if not isinstance(report.get(key),list) or not report[key] or not all(isinstance(s,str) and len(s)>12 for s in report[key]):return False
    return True
def main():
    p=argparse.ArgumentParser();p.add_argument("--mode",choices=["daily","weekly","special"],required=True)
    p.add_argument("--dry-run",action="store_true");args=p.parse_args()
    now=dt.datetime.now(dt.timezone.utc)
    existing={"updated":None,"reports":[]}
    if OUTPUT.exists():
        try:existing=json.loads(OUTPUT.read_text(encoding="utf-8"))
        except (ValueError,OSError):pass
    if not isinstance(existing,dict) or not isinstance(existing.get("reports"),list):existing={"updated":None,"reports":[]}
    reports=existing["reports"]
    created=0
    for topic in TOPICS:
        articles=select(topic,168 if args.mode=="weekly" else 72,now)
        if len({a["source"].lower() for a in articles})<3:
            print(topic,": insufficient independent sources");continue
        date_key=(now-dt.timedelta(hours=9)).strftime("%Y-%m-%d") if False else (now+dt.timedelta(hours=9)).strftime("%Y-%m-%d")
        if args.mode=="weekly":date_key=(now+dt.timedelta(hours=9)).strftime("%G-W%V")
        # Special reports only on substantive new source sets, not every poll.
        fingerprint=hashlib.sha256(json.dumps(sorted(a["url"] for a in articles),ensure_ascii=False).encode()).hexdigest()[:16]
        uid=f"{args.mode}:{topic}:{fingerprint if args.mode=='special' else date_key}"
        if any(r.get("id")==uid for r in reports):continue
        if args.dry_run:print("eligible",uid,"sources",len(articles));continue
        try:assessment=generate(topic,args.mode,articles)
        except Exception as e:
            print(f"{topic}: generation failed: {e}",file=sys.stderr);continue
        if not valid(assessment,articles):
            print(topic,": failed validation / no meaningful change");continue
        indices=sorted(set(assessment.pop("source_indices")))
        reports.insert(0,{"id":uid,"topic":topic,"topic_name":TOPICS[topic]["name"],"type":args.mode,
                          "created_at":now.isoformat(),"assessment":assessment,
                          "sources":[articles[i] for i in indices]})
        created+=1
    if created:
        existing["updated"]=now.isoformat()
        existing["reports"]=reports[:200]
        OUTPUT.parent.mkdir(parents=True,exist_ok=True)
        OUTPUT.write_text(json.dumps(existing,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("created",created)
if __name__=="__main__":main()
