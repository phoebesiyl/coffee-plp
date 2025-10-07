# agents.py — Multi-agent orchestration aligned with ChatOpenAI (OpenAI)
# Fix: ChatOpenAI.invoke returns AIMessage; we now extract .content safely.

from typing import List, Dict, Any, Tuple
from langchain_rag import qa_chain, LLM  # LLM is ChatOpenAI

# --------------------------- Utilities ---------------------------

def _llm_text(resp) -> str:
    """Return plain text from a LangChain message/response."""
    return getattr(resp, "content", str(resp)) or ""

def generate_related_queries(q: str) -> List[str]:
    """Heuristic expansion for coverage without going off-topic (kept small for speed)."""
    ql = q.lower()
    if any(k in ql for k in ["why", "cause", "reason", "sour", "bitter", "channel"]):
        return [q, f"{q} cause"]  # keep it to 2 to avoid long runs
    if any(k in ql for k in ["difference", "vs", "compare", "comparison"]):
        return [q, f"{q} key differences"]
    return [q, f"{q} overview"]

def _doc_key(d: Any) -> Tuple[str, str]:
    title = d.metadata.get("title") or d.metadata.get("source", "Unknown")
    sid = d.metadata.get("id", "?")
    return (title, sid)

def build_evidence(results: List[Dict[str, Any]], max_chars: int = 450) -> str:
    """Flatten and de-duplicate source documents into a numbered EVIDENCE block."""
    seen = set()
    flat_docs = []
    for r in results:
        for d in r.get("source_documents", []) or []:
            k = _doc_key(d)
            if k in seen:
                continue
            seen.add(k)
            title, sid = k
            excerpt = (d.page_content or "")[:max_chars]
            flat_docs.append((title, sid, excerpt))

    lines = []
    for i, (title, sid, excerpt) in enumerate(flat_docs, start=1):
        lines.append(f"[{i}] {title} (id:{sid})\n{excerpt}")
    return "EVIDENCE (use only what follows; cite by bracket number):\n" + "\n\n".join(lines)

# --------------------------- Agents ------------------------------

def researcher(query: str) -> Dict[str, Any]:
    """Agent 1 — RAG lookup (grounded answer + docs)."""
    return qa_chain(query)  # {"result": str, "source_documents": [...]}

def synthesizer(question: str, results: List[Dict[str, Any]]) -> str:
    """Agent 2 — Merge several RAG passes into one concise, grounded draft."""
    evidence = build_evidence(results)
    mini_summaries = []
    for i, r in enumerate(results, start=1):
        ans = (r.get("result") or "").strip()
        if ans:
            mini_summaries.append(f"Q{i}: {question}\nA{i}: {ans}")
    summaries = "\n\n".join(mini_summaries)

    prompt = f"""
[C] CONCISE
You are a precise coffee educator. Produce a single, clear explanation.

[L] LOGICAL
Organize as short bullets or numbered steps when procedural.

[E] EXPLICIT
Use ONLY the EVIDENCE block below. Cite as [1], [2] matching the evidence numbers.
Do not invent sources or facts. Keep to 4–8 sentences.

[A] ADAPTIVE
If the question implies 'why/how', give cause→effect→fix. If 'compare', show A vs B.

[R] REFLECTIVE
Before finalizing, ensure every claim is supported by EVIDENCE and citations are present.

Question:
{question}

{evidence}

Relevant mini-summaries (for orientation only; do not cite these):
{summaries}

Final, grounded draft with bracket citations:
""".strip()

    return _llm_text(LLM.invoke(prompt))

def critic(question: str, draft: str, results: List[Dict[str, Any]]) -> str:
    """Agent 3 — Light review for clarity/completeness; keep it grounded."""
    evidence = build_evidence(results)
    prompt = f"""
You are reviewing a draft answer to ensure clarity and grounding.

Rules:
- Use ONLY the EVIDENCE block; do not add external facts.
- Keep or improve citations [1], [2].
- Prefer concise, instructional language (2–6 short paragraphs or steps).

Question:
{question}

{evidence}

Draft:
{draft}

Provide a 'Revised Answer' that is clearer and fully supported by the evidence.
Revised Answer:
""".strip()
    return _llm_text(LLM.invoke(prompt))

# ------------------------ Orchestrator ---------------------------

def agent_run(question: str) -> str:
    """
    Orchestrates: Researcher -> Synthesizer -> Critic.
    Returns the final polished answer (string).
    """
    # 1) Research: original + short expansion
    queries = generate_related_queries(question)
    results: List[Dict[str, Any]] = []
    for q in queries:
        try:
            results.append(researcher(q))
        except Exception as e:
            results.append({"result": f"(lookup failed for '{q}': {e})", "source_documents": []})

    # 2) Synthesize
    draft = synthesizer(question, results).strip()

    # 3) Critique / refine
    final = critic(question, draft, results).strip()

    # Prefer the revised portion if present
    lowered = final.lower()
    if "revised answer" in lowered:
        try:
            after = final[lowered.index("revised answer"):]
            return after.split(":", 1)[-1].strip() or final
        except Exception:
            return final
    return final or draft
