#!/usr/bin/env python3
"""Collect verified WHO Disease Outbreak News via WHO's own JSON API."""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen

OUT = Path("data/bio-official.json")
ROOT = "https://www.who.int"
ENDPOINTS = [
    ROOT + "/api/news/diseaseoutbreaknews?$top=50&$orderby=PublicationDate%20desc",
    ROOT + "/api/default/diseaseoutbreaknews?$top=50&$orderby=PublicationDate%20desc",
    ROOT + "/api/emergencies/diseaseoutbreaknews?$top=50&$orderby=PublicationDate%20desc",
]
def get_json(url):
    req = Request(url, headers={"User-Agent":"Mozilla/5.0 NEXTBIO/3.0",
        "Accept":"application/json"})
    with urlopen(req, timeout=25) as response:
        return json.load(response)

def records(data):
    if isinstance(data, list): return data
    if isinstance(data, dict):
        for key in ("value","items","Items","results","Results"):
            if isinstance(data.get(key),list): return data[key]
        if isinstance(data.get("d"),dict): return records(data["d"])
    return []

def text_field(obj, *keys):
    for key in keys:
        v=obj.get(key)
        if isinstance(v,str) and v.strip(): return v.strip()
        if isinstance(v,dict):
            for k in ("Value","value","en","English"):
                if isinstance(v.get(k),str) and v[k].strip(): return v[k].strip()
    return ""

def parse(data):
    found={}
    for obj in records(data):
        if not isinstance(obj,dict): continue
        title=text_field(obj,"Title","title","Headline","headline")
        slug=text_field(obj,"UrlName","urlName","urlname")
        url=text_field(obj,"Url","url","ItemDefaultUrl","itemDefaultUrl")
        if not url and slug:
            url="/emergencies/disease-outbreak-news/item/"+slug
        if url.startswith("/"): url=ROOT+url
        if not url.startswith(ROOT+"/emergencies/disease-outbreak-news/item/"): continue
        if not title or len(title)<6: continue
        date=text_field(obj,"PublicationDate","publicationDate","DateCreated","dateCreated")
        if date.startswith("/Date("):
            match=re.search(r"\d{10,13}",date)
            if match:
                stamp=int(match.group())
                date=datetime.fromtimestamp(stamp/(1000 if stamp>10**11 else 1),timezone.utc).isoformat()
        found[url]={"title":re.sub(r"<[^>]+>","",title)[:240],"url":url,
            "source":"WHO Disease Outbreak News","published":date}
    return list(found.values())

def main():
    new=[]
    for url in ENDPOINTS:
        try:
            result=parse(get_json(url))
            print("WHO API:",url,"articles:",len(result))
            if result:
                new=result
                break
        except Exception as exc:
            print("WHO API unavailable:",url,str(exc)[:180],file=sys.stderr)
    if not new:
        print("ERROR: WHO API returned no verified announcements. Existing data preserved.",file=sys.stderr)
        sys.exit(1)
    old=[]
    if OUT.exists():
        try:
            old=[x for x in json.loads(OUT.read_text(encoding="utf-8")).get("items",[])
                 if isinstance(x,dict) and str(x.get("url","")).startswith(
                     ROOT+"/emergencies/disease-outbreak-news/item/")]
        except (ValueError,OSError): pass
    merged={x["url"]:x for x in old}
    for x in new:
        if x["url"] in merged and merged[x["url"]].get("title")==x["title"] and merged[x["url"]].get("title_ko"):
            x["title_ko"]=merged[x["url"]]["title_ko"]
        merged[x["url"]]=x
    items=sorted(merged.values(),key=lambda x:x.get("published",""),reverse=True)[:100]
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps({"updated":datetime.now(timezone.utc).isoformat(),
         "items":items},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("WHO official announcements saved:",len(items))
if __name__=="__main__": main()
