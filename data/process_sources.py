# data/process_sources.py
# Ingests pdf / web / youtube (with local transcript support) and builds Chroma.
import os, csv, yaml
from pathlib import Path

# ---- LangChain loaders ----
try:
    from langchain_community.document_loaders import (
        PyPDFLoader, WebBaseLoader, YoutubeLoader, TextLoader
    )
except ModuleNotFoundError:
    from langchain.document_loaders import (
        PyPDFLoader, WebBaseLoader, YoutubeLoader, TextLoader
    )

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

CFG = yaml.safe_load(open("config.yaml"))
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"  # safe default UA

# ---------- YouTube Handling ----------
def canonical_youtube(u: str) -> str:
    """Return clean https://youtu.be/<video_id>."""
    if "watch?v=" in u:
        vid = u.split("watch?v=")[-1].split("&")[0]
    else:
        vid = u.split("/")[-1].split("?")[0]
    return f"https://youtu.be/{vid}"

def load_youtube(url: str, fallback_txt_dir: str = "data/raw"):
    """Transcript-only YouTube load; fallback to local .txt if no captions."""
    clean = canonical_youtube(url)
    try:
        loader = YoutubeLoader.from_youtube_url(
            clean, add_video_info=False, language=["en","en-US"]
        )
        docs = loader.load()
        if docs:
            for d in docs:
                d.metadata.setdefault("source", clean)
                d.metadata.setdefault("type", "youtube")
            return docs
    except Exception as e:
        print(f"[YouTube error] {clean}: {e}")

    vid = clean.split("/")[-1]
    candidate = Path(fallback_txt_dir) / f"{vid}.txt"
    if candidate.exists():
        tloader = TextLoader(str(candidate), encoding="utf-8")
        docs = tloader.load()
        for d in docs:
            d.metadata.update({"source": clean, "type": "youtube_fallback", "video_id": vid})
        print(f"[YouTube fallback] Used {candidate}")
        return docs

    print(f"[YouTube missing transcript] {clean} (no captions and no {vid}.txt)")
    return []

# ---------- CSV Loader ----------
def load_from_csv(csv_path: str) -> list:
    """Load and normalize all sources (pdf, web, youtube, txt)."""
    csv_path = Path(csv_path)
    if not csv_path.exists():
        raise SystemExit(f"[Fatal] CSV not found: {csv_path}")

    docs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            t = (row["type"] or "").strip().lower()
            src = (row["url_or_path"] or "").strip()
            meta = {k: row[k] for k in row}

            try:
                if t == "pdf":
                    p = Path(src)
                    if not p.exists():
                        print(f"[PDF missing] {p}")
                        continue
                    loader = PyPDFLoader(str(p))
                    new = loader.load()

                elif t == "web":
                    loader = WebBaseLoader(web_paths=[src], header_template={"User-Agent": UA})
                    new = loader.load()

                elif t == "youtube":
                    p = Path(src)
                    if p.suffix.lower() == ".txt" and p.exists():
                        loader = TextLoader(str(p), encoding="utf-8")
                        new = loader.load()
                        for d in new:
                            d.metadata.setdefault("type", "youtube_fallback")
                            d.metadata.setdefault("source", str(p))
                    else:
                        new = load_youtube(src)

                else:
                    print(f"[Skip] Unsupported type: {t} for {src}")
                    continue

                for d in new:
                    d.metadata.update(meta)
                    d.metadata.setdefault(
                        "id",
                        f"{meta.get('title','?')}@{d.metadata.get('page', d.metadata.get('source','?'))}"
                    )
                docs.extend(new)

            except Exception as e:
                print(f"[Load error] {t} {src}: {e}")

    return docs

# ---------- Main Build ----------
def main():
    print("Loading sources...")
    csv_path = "data/sources 2.csv"
    docs = load_from_csv(csv_path)
    print(f"Loaded {len(docs)} documents.")

    print("Splitting...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CFG["chunk_size"],
        chunk_overlap=CFG["chunk_overlap"]
    )
    splits = splitter.split_documents(docs)
    print(f"Created {len(splits)} chunks.")

    print("Embedding & writing Chroma...")
    embeddings = HuggingFaceEmbeddings(model_name=CFG["embedding_model"])
    Chroma.from_documents(
        documents=splits,
        embedding=embeddings,
        persist_directory=CFG["persist_directory"]
    )
    print(f"✅ Done. Chroma DB built at {CFG['persist_directory']}")

if __name__ == "__main__":
    main()
