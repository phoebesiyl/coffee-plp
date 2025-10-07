import os
import yaml
from typing import Dict, Any, List

# Silence HF tokenizers fork warnings
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")

# Use the HuggingFace embedding instead of OpenAI one
from langchain_huggingface import HuggingFaceEmbeddings

#  Vector store
from langchain_community.vectorstores import Chroma

#  OpenAI chat model for generation
from langchain_openai import ChatOpenAI

#  Prompt router (your file)
from prompts import route_prompt


# ----------------------------
# 1) Defaults & config loader
# ----------------------------
DEFAULT_CFG = {
    "llm_model": "gpt-4o-mini",                           # fast & economical
    "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
    "persist_directory": "./chroma_db",
    "retrieval_k": 3,
    "chunk_size": 1000,                                   # used at ingest time
    "chunk_overlap": 200,                                 # used at ingest time
}

def load_cfg(path: str = "config.yaml") -> Dict[str, Any]:
    try:
        with open(path, "r") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        data = {}
    return {**DEFAULT_CFG, **data}

CFG = load_cfg()


# ----------------------------
# 2) Core components
# ----------------------------
# Embeddings must match what you used at ingest time
EMB = HuggingFaceEmbeddings(model_name=CFG["embedding_model"])

# Load the persisted DB (built by data/process_sources.py)
VSTORE = Chroma(
    embedding_function=EMB,
    persist_directory=CFG["persist_directory"],
)

# Create a retriever
RETR = VSTORE.as_retriever(search_kwargs={"k": CFG["retrieval_k"]})

# OpenAI chat model
LLM = ChatOpenAI(
    model=CFG["llm_model"],
    temperature=0.2,
    timeout=60,
    max_retries=2,
)


# ----------------------------
# 3) Helpers
# ----------------------------
def _ctx(docs: List[Any]) -> str:
    """Format top-k documents into a short, citeable context block."""
    parts = []
    k = int(CFG.get("retrieval_k", 3)) or 3
    for i, d in enumerate(docs[:k]):
        meta = getattr(d, "metadata", {}) or {}
        title = meta.get("title") or meta.get("source") or "Unknown"
        sid = meta.get("id", "?")
        # keep snippets short to reduce hallucinations/latency
        snippet = (d.page_content or "")[:900]
        parts.append(f"[{i+1}] ({title} - id:{sid})\n{snippet}")
    return "\n\n".join(parts)

def refresh_retriever(k: int = None):
    """Optionally change k at runtime (useful for a settings sidebar)."""
    if k is not None:
        CFG["retrieval_k"] = int(k)
    global RETR
    RETR = VSTORE.as_retriever(search_kwargs={"k": CFG["retrieval_k"]})


# ----------------------------
# 4) Main Q&A function
# ----------------------------
def qa_chain(question: str) -> Dict[str, Any]:
    """Retrieve → build prompt → query LLM → return answer + docs."""
    docs = RETR.get_relevant_documents(question)

    if not docs:
        return {
            "result": (
                "No documents found in the vector store. "
                "Run `python data/process_sources.py` to ingest your sources into ./chroma_db."
            ),
            "source_documents": [],
        }

    prompt_tmpl = route_prompt(question)
    prompt_text = prompt_tmpl.format(
        question=question,
        context=_ctx(docs),
    )

    resp = LLM.invoke(prompt_text)
    answer = getattr(resp, "content", str(resp))
    return {"result": answer, "source_documents": docs}


# ----------------------------
# 5) Optional: tiny health check
# ----------------------------
def healthcheck() -> Dict[str, Any]:
    """Quick status info you can print in a diagnostics tab."""
    try:
        n = VSTORE._collection.count()  # type: ignore[attr-defined]
    except Exception:
        n = "unknown"
    return {
        "persist_directory": CFG["persist_directory"],
        "embedding_model": CFG["embedding_model"],
        "llm_model": CFG["llm_model"],
        "retrieval_k": CFG["retrieval_k"],
        "chroma_count": n,
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
    }
