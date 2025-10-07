# data/validate_sources.py
# Validates PDF/Web/YouTube rows from your CSV:
# - pdf: file exists + minimally readable
# - web: HTTP reachable (200-range)
# - youtube: OK if local .txt provided, otherwise checks caption availability

import os, csv, yaml
from pathlib import Path

# Minimal deps for checks
import requests
from requests.exceptions import RequestException
from pypdf import PdfReader
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

UA = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) CoffeePLP/1.0 Safari/537.36"
)

DEFAULT_CFG = {
    "sources_csv": "data/sources 2.csv"  # <- matches your filename
}

def load_cfg(path="config.yaml"):
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    return {**DEFAULT_CFG, **data}

CFG = load_cfg()

def canonical_youtube(u: str) -> str:
    if "watch?v=" in u:
        vid = u.split("watch?v=")[-1].split("&")[0]
    else:
        vid = u.split("/")[-1].split("?")[0]
    return f"https://youtu.be/{vid}"

def yt_id(u: str) -> str:
    return canonical_youtube(u).split("/")[-1]

def check_pdf(path: str):
    p = Path(path)
    if not p.exists():
        return False, "missing"
    if p.suffix.lower() != ".pdf":
        return False, "not a .pdf"
    try:
        PdfReader(str(p))  # minimal parse
        return True, "ok"
    except Exception as e:
        return False, f"read-failed: {e}"

def check_web(url: str):
    try:
        r = requests.get(url, headers={"User-Agent": UA}, timeout=12)
        if 200 <= r.status_code < 300 and r.text.strip():
            return True, f"HTTP {r.status_code}"
        return False, f"HTTP {r.status_code}"
    except RequestException as e:
        return False, f"req-failed: {e}"

def check_youtube(src: str):
    p = Path(src)
    # If local transcript .txt provided, accept if non-empty
    if p.suffix.lower() == ".txt":
        if p.exists() and p.stat().st_size > 0:
            return True, f"local-transcript {p.name}"
        return False, "local-transcript-missing-or-empty"

    # Otherwise treat as URL and look for captions
    vid = yt_id(src)
    try:
        YouTubeTranscriptApi.list_transcripts(vid)
        return True, "transcript-available"
    except (TranscriptsDisabled, NoTranscriptFound):
        # Also accept fallback transcript at data/raw/<id>.txt if present
        fallback = Path("data/raw") / f"{vid}.txt"
        if fallback.exists() and fallback.stat().st_size > 0:
            return True, f"fallback {fallback.name}"
        return False, "no-transcript-no-fallback"
    except Exception as e:
        return False, f"yt-error: {e}"

def main():
    csv_path = Path(CFG["sources_csv"])
    if not csv_path.exists():
        print(f"[fatal] CSV not found: {csv_path}")
        return

    rows = list(csv.DictReader(open(csv_path, newline="", encoding="utf-8")))
    print(f"Validating {len(rows)} rows from {csv_path} …\n")

    totals = {"pdf":[0,0], "web":[0,0], "youtube":[0,0]}
    failures = []

    for row in rows:
        t = (row.get("type") or "").strip().lower()
        src = (row.get("url_or_path") or "").strip()
        title = row.get("title") or "(untitled)"
        if t not in totals: totals[t] = [0,0]
        totals[t][1] += 1

        if t == "pdf":
            ok, msg = check_pdf(src)
        elif t == "web":
            ok, msg = check_web(src)
        elif t == "youtube":
            ok, msg = check_youtube(src)
        else:
            ok, msg = False, f"unsupported-type: {t}"

        print(f"[{'OK' if ok else 'FAIL'}] {t:7} | {title} -> {msg}")
        if ok:
            totals[t][0] += 1
        else:
            failures.append((t, title, src, msg))

    print("\nSummary:")
    for t, (ok, total) in totals.items():
        if total:
            print(f"  {t:7}: {ok}/{total} OK")

    if failures:
        print("\nFailures to review:")
        for t, title, src, msg in failures:
            print(f"  - {t:7} | {title} | {src} | {msg}")

if __name__ == "__main__":
    main()
