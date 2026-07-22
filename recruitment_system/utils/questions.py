"""
AI-generated HR & Technical Interview Questions
-------------------------------------------------
Builds a personalized question set from the candidate's matched
skills + skill gaps. Uses a curated technical question bank per
skill (grounded, reviewable, no hallucination risk) plus a standard
HR question bank. If an LLM is configured (utils/llm.py) it is used
to generate a few additional tailored questions.
"""
from .llm import generate_text
from .skills_data import SKILL_TO_CATEGORY

HR_QUESTIONS = [
    "Tell me about yourself and what draws you to this role.",
    "Describe a challenging project you worked on and how you handled obstacles.",
    "How do you prioritize tasks when working under tight deadlines?",
    "Tell me about a time you disagreed with a teammate. How was it resolved?",
    "Where do you see yourself professionally in the next few years?",
    "Why do you want to work with us specifically?",
    "Describe a time you had to learn a new skill quickly.",
]

TECHNICAL_QUESTION_BANK = {
    "python": [
        "Explain the difference between a list and a tuple in Python.",
        "What are Python decorators and when would you use one?",
        "How does Python's garbage collection work?",
    ],
    "sql": [
        "What's the difference between INNER JOIN and LEFT JOIN?",
        "How would you optimize a slow-running SQL query?",
        "Explain normalization and why it matters in database design.",
    ],
    "machine learning": [
        "How would you handle an imbalanced dataset?",
        "Explain the bias-variance tradeoff.",
        "Walk me through how you'd validate a model before deployment.",
    ],
    "deep learning": [
        "What's the difference between a CNN and an RNN, and when do you use each?",
        "Explain what backpropagation does.",
        "How do you prevent a neural network from overfitting?",
    ],
    "bert": [
        "How does BERT's attention mechanism differ from earlier NLP models?",
        "What's the difference between BERT and Sentence-BERT?",
        "Explain how you'd fine-tune a pretrained transformer for a classification task.",
    ],
    "nlp": [
        "What's the difference between stemming and lemmatization?",
        "How would you handle out-of-vocabulary words in an NLP pipeline?",
    ],
    "react": [
        "Explain the difference between state and props in React.",
        "What are React hooks and why were they introduced?",
    ],
    "flask": [
        "How does Flask handle routing internally?",
        "How would you structure a large Flask application?",
    ],
    "aws": [
        "What's the difference between an EC2 instance and a Lambda function?",
        "How would you secure an S3 bucket that stores sensitive data?",
    ],
    "docker": [
        "What's the difference between a Docker image and a container?",
        "How would you reduce the size of a Docker image?",
    ],
    "data structures": [
        "When would you use a hash map over a binary search tree?",
        "Explain the time complexity difference between an array and a linked list for insertion.",
    ],
    "system design": [
        "How would you design a URL shortening service?",
        "How would you scale a service to handle 10x traffic overnight?",
    ],
}

GENERIC_TECHNICAL_FALLBACK = [
    "Walk me through a project where you used {skill}.",
    "What's a challenging problem you solved using {skill}?",
    "How would you explain {skill} to someone non-technical?",
]


def _questions_for_skill(skill: str) -> list:
    if skill in TECHNICAL_QUESTION_BANK:
        return TECHNICAL_QUESTION_BANK[skill]
    return [q.format(skill=skill) for q in GENERIC_TECHNICAL_FALLBACK[:1]]


def generate_questions(matched_skills: list, role_title: str = "this role", n_technical: int = 6, n_hr: int = 4) -> dict:
    technical = []
    for skill in matched_skills:
        if len(technical) >= n_technical:
            break
        for q in _questions_for_skill(skill):
            if q not in technical:
                technical.append(q)
            if len(technical) >= n_technical:
                break

    if not technical:
        technical = [q.format(skill=role_title) for q in GENERIC_TECHNICAL_FALLBACK]

    hr = HR_QUESTIONS[:n_hr]

    # Optional: augment with LLM-generated tailored questions if configured
    if matched_skills:
        prompt = (
            f"Generate 2 concise, specific technical interview questions for a candidate "
            f"applying to '{role_title}' skilled in: {', '.join(matched_skills[:6])}. "
            f"Return only the questions, one per line, no numbering."
        )
        llm_out = generate_text(prompt)
        if llm_out:
            extra = [l.strip("-• ").strip() for l in llm_out.split("\n") if l.strip()]
            technical.extend(extra[:2])

    return {"technical": technical, "hr": hr}
