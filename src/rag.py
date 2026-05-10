import os
import logging
from typing import List, Dict, Tuple


from src.search import _search_local

logger = logging.getLogger(__name__)


def _build_context_snippets(query: str, top_k: int = 3) -> List[Dict]:
    results, _ = _search_local(query, source_mode="all", top_k=top_k)
    return results


def ask(question: str, top_k: int = 3, model: str = "gpt-3.5-turbo") -> Tuple[bool, Dict]:
    """Run a simple RAG: retrieve top_k local snippets, then call OpenAI chat.

    Returns (success, payload) where payload contains `answer`, `sources`, and `error`.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False, {"error": "OPENAI_API_KEY not set in environment"}

    # Import openai lazily so tests / environments without the package don't fail on import
    try:
        import openai
    except Exception:
        return False, {"error": "openai package not installed in the environment"}

    openai.api_key = api_key

    try:
        snippets = _build_context_snippets(question, top_k=top_k)
        if not snippets:
            return False, {"error": "No local context found for RAG."}

        # Build context text
        context_parts = []
        sources = []
        for i, s in enumerate(snippets, start=1):
            text = s.get("text", "")
            src = s.get("source", "local")
            context_parts.append(f"Snippet {i} (source={src}):\n{text}")
            sources.append({"index": i, "source": src, "score": s.get("score")})

        context_text = "\n\n---\n\n".join(context_parts)

        system_prompt = (
            "You are an assistant that answers user questions using the provided context. "
            "Prefer to use the context snippets; if the answer is not contained, say 'I don't know'."
        )

        user_prompt = (
            f"Context:\n{context_text}\n\nQuestion: {question}\n\n"
            "Answer concisely and cite the snippet numbers used, e.g. [Snippet 1]."
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=512,
            temperature=0.0,
        )

        answer = resp["choices"][0]["message"]["content"].strip()

        return True, {"answer": answer, "sources": sources}

    except Exception as e:
        logger.exception("rag_call_failed")
        return False, {"error": str(e)}
