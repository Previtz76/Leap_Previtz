#!/usr/bin/env python3
"""Fetch the B10 OTA history, extract entries, translate them, and retain source links."""
import os, re, json, hashlib, html
from datetime import datetime, timezone
from pathlib import Path
import requests
from bs4 import BeautifulSoup

URL = "https://leapmotor.bwwb.de/modelle/b10/"
OUT = Path("data/ota.json")
DEEPL_KEY = os.getenv("DEEPL_API_KEY", "").strip()
DEEPL_URL = "https://api-free.deepl.com/v2/translate"
HEADERS = {"User-Agent": "B10-OTA-Italian-Monitor/1.0 (independent personal project)"}

def clean(s):
    return re.sub(r"\\s+", " ", html.unescape(s or "")).strip()

def translate(text):
    text = clean(text)
    if not text:
        return ""
    if not DEEPL_KEY:
        return "[Traduzione automatica non configurata] " + text
    try:
        r = requests.post(DEEPL_URL, data={
            "auth_key": DEEPL_KEY, "text": text, "source_lang": "DE",
            "target_lang": "IT", "preserve_formatting": "1"
        }, timeout=25)
        r.raise_for_status()
        return r.json()["translations"][0]["text"]
    except Exception as exc:
        print("DeepL translation failed:", exc)
        return "[Traduzione non disponibile; testo originale] " + text

def infer_status(title, text, links):
    low = (title + " " + text).lower()
    if any("media.stellantis.com" in x.get("url","") or "leapmotor.com" in x.get("url","") and "forum" not in x.get("url","") for x in links):
        return "official"
    if any(w in low for w in ("gerücht", "hörensagen", "nicht bestätigt", "unbestätigt", "soll")):
        return "rumor"
    return "community"

def infer_model(title, text):
    t=(title+" "+text).upper()
    has_bev=bool(re.search(r"\\bBEV\\b|3\\.41\\.", t))
    has_reev=bool(re.search(r"\\bREEV\\b|3\\.51\\.", t))
    if has_bev and not has_reev: return "BEV"
    if has_reev and not has_bev: return "REEV"
    return "both"

def infer_version(title, text):
    m=re.search(r"(?<!\\d)(\\d\\.\\d{2}\\.\\d{2})(?!\\d)", title+" "+text)
    return m.group(1) if m else ""

def infer_date(title, text):
    for pattern in [r"(\\d{1,2}\\.\\s*[A-Za-zÄÖÜäöü]+\\s+\\d{4})", r"(\\d{1,2}\\.\\d{1,2}\\.\\d{4})", r"(\\d{1,2}\\.\\s*[A-Za-zÄÖÜäöü]+\\s*\\d{4})"]:
        m=re.search(pattern,title)
        if m: return m.group(1)
    return "Data non indicata"

def translate_long(text):
    # DeepL accepts bounded text sizes; translate in paragraph-sized chunks.
    chunks = re.split(r"(?<=[.!?])\\s+", text)
    out=[]
    current=""
    for c in chunks:
        if len(current)+len(c)>3500 and current:
            out.append(translate(current)); current=c
        else:
            current=(current+" "+c).strip()
    if current: out.append(translate(current))
    return " ".join(out)

def main():
    response=requests.get(URL, headers=HEADERS, timeout=45)
    response.raise_for_status()
    soup=BeautifulSoup(response.text,"html.parser")
    old={}
    if OUT.exists():
        try:
            old={e["id"]:e for e in json.loads(OUT.read_text(encoding="utf-8")).get("entries",[])}
        except Exception: pass

    # Entries are h3 headings in the source page. Capture content until next h3.
    headings=soup.find_all("h3")
    entries=[]
    for idx,h in enumerate(headings):
        title=clean(h.get_text(" ",strip=True))
        if not title or not re.search(r"LeapOS|OTA|Gerücht|Patch|Update|Verbrauchsanzeige|Rollout",title,re.I):
            continue
        parts=[]
        sources=[]
        node=h
        # Traverse following siblings in document order until next h3.
        for sib in h.find_all_next():
            if sib is not h and sib.name=="h3":
                break
            if sib.name in ("p","li"):
                txt=clean(sib.get_text(" ",strip=True))
                if txt and (not parts or txt != parts[-1]): parts.append(txt)
            if sib.name=="a" and sib.get("href"):
                href=sib.get("href")
                if href.startswith("/"): href=requests.compat.urljoin(URL,href)
                label=clean(sib.get_text(" ",strip=True)) or "Fonte originale"
                if href.startswith("http") and href != URL and not any(x["url"]==href for x in sources):
                    sources.append({"label":label[:100],"url":href})
        body="\\n".join(parts[:180])
        if len(body)<30: continue
        # Prefer the entry's own direct-link / source link, but always include source overview.
        if not any(x["url"]==URL for x in sources): sources.append({"label":"Pagina di riferimento B10","url":URL})
        identity=re.sub(r"[^a-z0-9]+","-", (title+"-"+infer_date(title,body)).lower()).strip("-")[:100]
        digest=hashlib.sha256((title+"\\n"+body+"\\n"+json.dumps(sources,sort_keys=True)).encode()).hexdigest()
        prev=old.get(identity,{})
        changed=bool(prev and prev.get("content_hash")!=digest)
        is_new=identity not in old
        body_de=body
        summary_source=parts[0] if parts else body
        # Avoid spending translation quota every day on unchanged entries.
        if prev and prev.get("content_hash")==digest and prev.get("title_it") and prev.get("body_it"):
            title_it=prev["title_it"]
            body_it=prev["body_it"]
            summary_it=prev.get("summary_it","")
            changed=False
        else:
            title_it=translate(title)
            body_it=translate_long(body)
            summary_it=translate(summary_source[:900])
        status=infer_status(title,body,sources)
        entries.append({
            "id":identity, "title_de":title, "title_it":title_it,
            "body_de":body_de, "body_it":body_it, "summary_it":summary_it,
            "date":infer_date(title,body), "version":infer_version(title,body),
            "model":infer_model(title,body), "status":status, "market":"",
            "sources":sources[:12], "content_hash":digest,
            "changed":changed or is_new, "first_seen":prev.get("first_seen") or datetime.now(timezone.utc).date().isoformat()
        })

    # Keep old entries if the source page temporarily omits one, avoiding accidental history loss.
    current_ids={e["id"] for e in entries}
    for identity, old_entry in old.items():
        if identity not in current_ids:
            old_entry["changed"]=False
            entries.append(old_entry)

    # Keep the source's heading order: the original page normally lists newest entries first.
    versions={"BEV":"","REEV":""}
    for e in entries:
        if e.get("version") and e["model"] in versions and not versions[e["model"]]:
            versions[e["model"]]=e["version"]
    payload={
        "source_url":URL,
        "checked_at":datetime.now().astimezone().strftime("%d/%m/%Y %H:%M %Z"),
        "generated_at":datetime.now(timezone.utc).isoformat(),
        "latest_versions":versions,
        "entries":entries
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"Saved {len(entries)} entries to {OUT}")

if __name__=="__main__":
    main()
