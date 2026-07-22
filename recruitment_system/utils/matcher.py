"""
Semantic Skill Matching (Sentence-BERT) + ATS Score + Skill Gap Analysis
-------------------------------------------------------------------------
Loads a Sentence-BERT model once (singleton) and exposes:
  - semantic_similarity(text_a, text_b)      -> float 0..1
  - ats_score(resume, job)                   -> dict with sub-scores
  - skill_gap(resume_skills, jd_skills)      -> dict
"""
from .skills_data import SKILL_TO_CATEGORY

_MODEL = None
_MODEL_LOAD_FAILED = False
MODEL_NAME = "all-MiniLM-L6-v2"  # lightweight Sentence-BERT, 384-dim


def get_model():
    """Lazily load Sentence-BERT. If it can't be downloaded (no internet /
    first run without cached weights), fall back to TF-IDF similarity so
    the app keeps working instead of crashing."""
    global _MODEL, _MODEL_LOAD_FAILED
    if _MODEL is None and not _MODEL_LOAD_FAILED:
        try:
            from sentence_transformers import SentenceTransformer
            _MODEL = SentenceTransformer(MODEL_NAME)
        except Exception as e:
            print(f"[matcher] Could not load Sentence-BERT ({e}). "
                  f"Falling back to TF-IDF similarity. Fix internet access "
                  f"or pre-download the model to use real BERT embeddings.")
            _MODEL_LOAD_FAILED = True
    return _MODEL


def _tfidf_similarity(text_a: str, text_b: str) -> float:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    vect = TfidfVectorizer(stop_words="english")
    try:
        tfidf = vect.fit_transform([text_a, text_b])
        return float(cosine_similarity(tfidf[0], tfidf[1])[0][0])
    except ValueError:
        return 0.0


def semantic_similarity(text_a: str, text_b: str) -> float:
    model = get_model()
    if model is None:
        return max(0.0, min(1.0, _tfidf_similarity(text_a, text_b)))
    from sentence_transformers import util
    emb = model.encode([text_a, text_b], convert_to_tensor=True, normalize_embeddings=True)
    score = util.cos_sim(emb[0], emb[1]).item()
    # cos sim in [-1,1] -> clamp/scale to [0,1]
    return max(0.0, min(1.0, (score + 1) / 2 if score < 0 else score))


def skill_overlap_score(resume_skills: list, jd_skills: list) -> float:
    if not jd_skills:
        return 0.0
    matched = set(resume_skills) & set(jd_skills)
    return len(matched) / len(set(jd_skills))


def skill_gap(resume_skills: list, jd_skills: list) -> dict:
    resume_set, jd_set = set(resume_skills), set(jd_skills)
    matched = sorted(resume_set & jd_set)
    missing = sorted(jd_set - resume_set)
    extra = sorted(resume_set - jd_set)

    missing_by_category = {}
    for s in missing:
        cat = SKILL_TO_CATEGORY.get(s, "Other")
        missing_by_category.setdefault(cat, []).append(s)

    return {
        "matched_skills": matched,
        "missing_skills": missing,
        "extra_skills": extra,
        "missing_by_category": missing_by_category,
        "match_percentage": round(100 * len(matched) / len(jd_set), 1) if jd_set else 0.0,
    }


def compute_ats_score(resume_text: str, resume_skills: list, jd_text: str, jd_skills: list,
                       experience_years: float = 0.0, required_experience: float = 0.0) -> dict:
    """
    Weighted ATS score combining:
      - Semantic similarity between full resume & JD text (40%)
      - Skill keyword overlap (40%)
      - Experience match (20%)
    """
    sem_score = semantic_similarity(resume_text, jd_text)
    kw_score = skill_overlap_score(resume_skills, jd_skills)

    if required_experience > 0:
        exp_score = min(1.0, experience_years / required_experience)
    else:
        exp_score = 1.0 if experience_years > 0 else 0.5

    final = 0.40 * sem_score + 0.40 * kw_score + 0.20 * exp_score
    final_pct = round(final * 100, 1)

    return {
        "ats_score": final_pct,
        "semantic_score": round(sem_score * 100, 1),
        "keyword_score": round(kw_score * 100, 1),
        "experience_score": round(exp_score * 100, 1),
        "verdict": _verdict(final_pct),
    }


def _verdict(score: float) -> str:
    if score >= 80:
        return "Excellent Match"
    if score >= 65:
        return "Strong Match"
    if score >= 45:
        return "Moderate Match"
    return "Weak Match"


def rank_candidates(candidates: list) -> list:
    """candidates: list of dicts each containing 'ats_score'. Returns sorted desc with rank added."""
    ranked = sorted(candidates, key=lambda c: c["ats_score"], reverse=True)
    for i, c in enumerate(ranked, start=1):
        c["rank"] = i
    return ranked
