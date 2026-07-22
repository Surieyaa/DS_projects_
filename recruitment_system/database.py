from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class HRUser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # demo only — plaintext for simplicity
    company = db.Column(db.String(120), default="Your Company")


class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_skills_json = db.Column(db.Text, default="[]")
    required_experience = db.Column(db.Float, default=0.0)
    created_by = db.Column(db.Integer, db.ForeignKey("hr_user.id"))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def required_skills(self):
        return json.loads(self.required_skills_json or "[]")

    @required_skills.setter
    def required_skills(self, value):
        self.required_skills_json = json.dumps(value)


class Candidate(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    phone = db.Column(db.String(50))
    resume_path = db.Column(db.String(300))
    skills_json = db.Column(db.Text, default="[]")
    education_json = db.Column(db.Text, default="[]")
    experience_years = db.Column(db.Float, default=0.0)
    raw_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def skills(self):
        return json.loads(self.skills_json or "[]")

    @skills.setter
    def skills(self, value):
        self.skills_json = json.dumps(value)

    @property
    def education(self):
        return json.loads(self.education_json or "[]")

    @education.setter
    def education(self, value):
        self.education_json = json.dumps(value)


class Application(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    candidate_id = db.Column(db.Integer, db.ForeignKey("candidate.id"), nullable=False)

    ats_score = db.Column(db.Float, default=0.0)
    semantic_score = db.Column(db.Float, default=0.0)
    keyword_score = db.Column(db.Float, default=0.0)
    experience_score = db.Column(db.Float, default=0.0)
    verdict = db.Column(db.String(50))

    matched_skills_json = db.Column(db.Text, default="[]")
    missing_skills_json = db.Column(db.Text, default="[]")
    summary = db.Column(db.Text)

    hr_questions_json = db.Column(db.Text, default="[]")
    technical_questions_json = db.Column(db.Text, default="[]")
    voice_eval_json = db.Column(db.Text, default="{}")

    interview_datetime = db.Column(db.String(100))
    status = db.Column(db.String(30), default="Screened")  # Screened, Interview Scheduled, Selected, Rejected
    recommendation = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    job = db.relationship("Job", backref="applications")
    candidate = db.relationship("Candidate", backref="applications")

    def _prop(name):
        def getter(self):
            return json.loads(getattr(self, f"{name}_json") or "[]")
        def setter(self, value):
            setattr(self, f"{name}_json", json.dumps(value))
        return property(getter, setter)

    matched_skills = _prop("matched_skills")
    missing_skills = _prop("missing_skills")
    hr_questions = _prop("hr_questions")
    technical_questions = _prop("technical_questions")

    @property
    def voice_eval(self):
        return json.loads(self.voice_eval_json or "{}")

    @voice_eval.setter
    def voice_eval(self, value):
        self.voice_eval_json = json.dumps(value)
