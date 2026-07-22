"""
Resume Parsing & Information Extraction
----------------------------------------
Extracts raw text from PDF/DOCX resumes (PyMuPDF), then pulls out
structured fields: name, email, phone, skills, education keywords,
years-of-experience estimate, using regex + the skill taxonomy.
"""
import re
import os
import fitz  # PyMuPDF
import docx
from .skills_data import ALL_SKILLS, SKILL_TO_CATEGORY

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3,5}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}")
EXPERIENCE_RE = re.compile(r"(\d+(?:\.\d+)?)\s*\+?\s*(?:years|yrs|year)\s*(?:of)?\s*experience", re.I)

EDUCATION_KEYWORDS = [
    "b.tech", "btech", "bachelor", "m.tech", "mtech", "master", "phd",
    "b.sc", "m.sc", "mba", "bca", "mca", "diploma", "university", "college"
]


def extract_text(filepath: str) -> str:
    """Extract raw text from a PDF or DOCX resume."""
    ext = os.path.splitext(filepath)[1].lower()
    if ext == ".pdf":
        text = []
        with fitz.open(filepath) as doc:
            for page in doc:
                text.append(page.get_text())
        return "\n".join(text)
    elif ext in (".docx", ".doc"):
        d = docx.Document(filepath)
        return "\n".join(p.text for p in d.paragraphs)
    elif ext == ".txt":
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def extract_name(text: str) -> str:
    """Heuristic: first non-empty line that looks like a name (2-4 capitalised words)."""
    lines = [l.strip() for l in text.split("\n") if l.strip()]
    for line in lines[:8]:
        words = line.split()
        if 1 < len(words) <= 4 and all(w.replace(".", "").isalpha() for w in words):
            if not EMAIL_RE.search(line) and not PHONE_RE.search(line):
                return line.title()
    return "Candidate"


def extract_skills(text: str) -> list:
    """Match known skills (from taxonomy) against resume text, longest-match first."""
    lowered = text.lower()
    found = set()
    for skill in ALL_SKILLS:
        pattern = r"(?<![a-zA-Z0-9])" + re.escape(skill) + r"(?![a-zA-Z0-9])"
        if re.search(pattern, lowered):
            found.add(skill)
    return sorted(found)


def extract_education(text: str) -> list:
    lowered = text.lower()
    return sorted({kw for kw in EDUCATION_KEYWORDS if kw in lowered})


def estimate_experience_years(text: str) -> float:
    matches = EXPERIENCE_RE.findall(text)
    if matches:
        return max(float(m) for m in matches)
    return 0.0


def parse_resume(filepath: str) -> dict:
    text = extract_text(filepath)
    skills = extract_skills(text)
    skill_categories = {}
    for s in skills:
        cat = SKILL_TO_CATEGORY.get(s, "Other")
        skill_categories.setdefault(cat, []).append(s)

    email_match = EMAIL_RE.search(text)
    phone_match = PHONE_RE.search(text)

    return {
        "name": extract_name(text),
        "email": email_match.group() if email_match else None,
        "phone": phone_match.group().strip() if phone_match else None,
        "skills": skills,
        "skill_categories": skill_categories,
        "education": extract_education(text),
        "experience_years": estimate_experience_years(text),
        "raw_text": text,
        "word_count": len(text.split()),
    }
