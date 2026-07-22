"""
Optional LLM hook.
------------------
The project brief calls for Llama 3 / Gemma / GPT for resume summaries
and interview-question generation. Running a full local LLM isn't
practical for a lightweight Flask deployment, so this module gives you
a plug for a hosted API (OpenAI, Groq, Google Gemini, etc). If no key
is configured, every function here returns None and callers fall back
to the offline BERT-based / template-based logic (summarizer.py,
questions.py) — so the app works fully out of the box either way.

To enable real LLM generation:
  1. pip install openai   (or groq / google-generativeai)
  2. Set the API key as an environment variable, e.g.
         export OPENAI_API_KEY="sk-..."
  3. Set LLM_PROVIDER=openai (or "groq") as an environment variable.
"""
import os

PROVIDER = os.environ.get("LLM_PROVIDER", "").lower()


def llm_available() -> bool:
    if PROVIDER == "openai":
        return bool(os.environ.get("OPENAI_API_KEY"))
    if PROVIDER == "groq":
        return bool(os.environ.get("GROQ_API_KEY"))
    return False


def generate_text(prompt: str, max_tokens: int = 300):
    """Returns generated text, or None if no LLM is configured / call fails."""
    if not llm_available():
        return None
    try:
        if PROVIDER == "openai":
            from openai import OpenAI
            client = OpenAI()
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
        if PROVIDER == "groq":
            from groq import Groq
            client = Groq()
            resp = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content.strip()
    except Exception:
        return None
    return None
