"""
Skill taxonomy used for resume parsing, JD parsing, skill-gap analysis,
and interview question generation. Organized by category so the
question generator can pick relevant technical questions per skill.
"""

SKILL_TAXONOMY = {
    "Programming Languages": [
        "python", "java", "c++", "c", "javascript", "typescript", "go", "rust",
        "r", "sql", "kotlin", "swift", "php", "matlab", "scala"
    ],
    "Web Development": [
        "html", "css", "react", "angular", "vue", "flask", "django", "fastapi",
        "node.js", "express", "next.js", "rest api", "graphql", "bootstrap",
        "tailwind"
    ],
    "Data & ML": [
        "machine learning", "deep learning", "nlp", "computer vision",
        "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy",
        "opencv", "bert", "transformers", "llm", "generative ai", "mlops",
        "data analysis", "data visualization", "statistics", "feature engineering"
    ],
    "Databases": [
        "mysql", "postgresql", "mongodb", "sqlite", "redis", "oracle",
        "firebase", "cassandra", "dynamodb"
    ],
    "Cloud & DevOps": [
        "aws", "azure", "gcp", "docker", "kubernetes", "ci/cd", "jenkins",
        "terraform", "linux", "git", "github actions", "nginx"
    ],
    "Core CS": [
        "data structures", "algorithms", "oop", "operating systems",
        "computer networks", "system design", "dbms", "software engineering"
    ],
    "Soft Skills": [
        "communication", "teamwork", "leadership", "problem solving",
        "time management", "adaptability", "collaboration"
    ],
}

# Flat lookup: skill -> category
SKILL_TO_CATEGORY = {
    skill: category
    for category, skills in SKILL_TAXONOMY.items()
    for skill in skills
}

ALL_SKILLS = sorted(SKILL_TO_CATEGORY.keys(), key=len, reverse=True)
