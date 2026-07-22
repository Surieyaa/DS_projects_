"""
AI Resume Summary
------------------
Offline extractive summarizer: splits resume text into sentences,
embeds each with Sentence-BERT, and picks the most "central"
(representative) sentences by cosine similarity to the document mean
embedding. This avoids needing a paid LLM API key while still being a
genuine embedding-based (deep learning) technique.

If an LLM API key is configured (see utils/llm.py), that is used
instead for a more fluent abstractive summary.
"""
import re
from .matcher import get_model


def _split_sentences(text: str) -> list:
    text = re.sub(r"\s+", " ", text).strip()
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if 6 <= len(s.split()) <= 60]


def summarize_resume(resume_text: str, name: str, top_k: int = 4) -> str:
    sentences = _split_sentences(resume_text)
    if len(sentences) <= top_k:
        body = " ".join(sentences)
        return body or f"{name}'s resume did not contain enough extractable text to summarize."

    model = get_model()
    if model is None:
        # No Sentence-BERT available (offline) — fall back to lead sentences
        return f"{name} — " + " ".join(sentences[:top_k])

    from sentence_transformers import util
    embeddings = model.encode(sentences, convert_to_tensor=True, normalize_embeddings=True)
    doc_embedding = embeddings.mean(dim=0)
    scores = util.cos_sim(doc_embedding, embeddings)[0]

    top_indices = sorted(range(len(sentences)), key=lambda i: scores[i], reverse=True)[:top_k]
    top_indices.sort()  # preserve original order for readability
    summary_sentences = [sentences[i] for i in top_indices]

    return f"{name} — " + " ".join(summary_sentences)
