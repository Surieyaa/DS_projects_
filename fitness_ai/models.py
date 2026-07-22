from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship("Profile", backref="user", uselist=False, cascade="all, delete-orphan")
    chats = db.relationship("ChatLog", backref="user", cascade="all, delete-orphan")
    progress = db.relationship("ProgressLog", backref="user", cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    __tablename__ = "profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)

    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    height_cm = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    activity_level = db.Column(db.String(30), default="moderate")  # sedentary/light/moderate/active
    diet_preference = db.Column(db.String(20), default="vegetarian")  # vegetarian/non_vegetarian
    goal = db.Column(db.String(30), default="general_fitness")
    available_equipment = db.Column(db.String(200), default="body weight")

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def bmi(self):
        if not self.height_cm or not self.weight_kg:
            return None
        h_m = self.height_cm / 100
        return round(self.weight_kg / (h_m * h_m), 1)


class ChatLog(db.Model):
    __tablename__ = "chat_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    sender = db.Column(db.String(10))  # user / bot
    message = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class ProgressLog(db.Model):
    __tablename__ = "progress_logs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    log_date = db.Column(db.Date, default=date.today)
    workouts_completed = db.Column(db.Integer, default=0)
    exercises_viewed = db.Column(db.Text)  # comma separated exercise names
    calories_target = db.Column(db.Float)
    weight_kg = db.Column(db.Float)
    notes = db.Column(db.String(255))
