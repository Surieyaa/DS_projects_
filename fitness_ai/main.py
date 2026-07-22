from functools import wraps
from datetime import date
from flask import (
    Blueprint, render_template, request, redirect, url_for, session, flash,
    jsonify, current_app, send_file
)

from extensions import db
from models import User, Profile, ChatLog, ProgressLog
from engines import bmi as bmi_engine
from engines import exercise_engine, diet_engine, pdf_report
from chatbot import nlp_engine, quotes

main_bp = Blueprint("main", __name__)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "error")
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)
    return wrapped


def current_user():
    uid = session.get("user_id")
    return User.query.get(uid) if uid else None


@main_bp.route("/")
def landing():
    if session.get("user_id"):
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = current_user()
    prof = user.profile

    if request.method == "POST":
        prof.age = int(request.form.get("age") or 0) or None
        prof.gender = request.form.get("gender")
        prof.height_cm = float(request.form.get("height_cm") or 0) or None
        prof.weight_kg = float(request.form.get("weight_kg") or 0) or None
        prof.activity_level = request.form.get("activity_level", "moderate")
        prof.diet_preference = request.form.get("diet_preference", "vegetarian")
        prof.goal = request.form.get("goal", "general_fitness")
        equipment = request.form.getlist("equipment")
        prof.available_equipment = ",".join(equipment) if equipment else "body weight"
        db.session.commit()
        flash("Profile saved! Your recommendations are now personalized.", "success")
        return redirect(url_for("main.dashboard"))

    return render_template("profile.html", profile=prof)


@main_bp.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    prof = user.profile

    bmi = prof.bmi()
    bmi_cat = bmi_engine.bmi_category(bmi)
    bmi_advice = bmi_engine.BMI_ADVICE.get(bmi_cat)

    calorie_target = bmi_engine.estimate_daily_calories(
        prof.weight_kg, prof.height_cm, prof.age, prof.gender, prof.activity_level, prof.goal
    )
    protein_target = bmi_engine.protein_target_g(prof.weight_kg, prof.goal)

    logs = ProgressLog.query.filter_by(user_id=user.id).order_by(ProgressLog.log_date.desc()).limit(14).all()
    total_workouts = sum(l.workouts_completed or 0 for l in logs)

    quote = quotes.random_quote()

    return render_template(
        "dashboard.html", user=user, profile=prof, bmi=bmi, bmi_category=bmi_cat,
        bmi_advice=bmi_advice, calorie_target=calorie_target, protein_target=protein_target,
        logs=list(reversed(logs)), total_workouts=total_workouts, quote=quote,
    )


@main_bp.route("/chat")
@login_required
def chat_page():
    return render_template("chat.html", user=current_user())


@main_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    user = current_user()
    prof = user.profile
    message = (request.json or {}).get("message", "").strip()
    if not message:
        return jsonify({"reply": "Type something and I'll help you out!", "cards": []})

    db.session.add(ChatLog(user_id=user.id, sender="user", message=message))

    user_equipment = prof.available_equipment.split(",") if prof.available_equipment else None
    intent = nlp_engine.detect_intent(message, user_goal=prof.goal, user_equipment=user_equipment)

    reply_text = ""
    cards = []
    card_type = "exercise"

    if intent["intent"] == "greeting":
        reply_text = quotes.random_greeting()

    elif intent["intent"] == "motivation":
        reply_text = quotes.random_quote()

    elif intent["intent"] == "bmi":
        bmi = prof.bmi()
        cat = bmi_engine.bmi_category(bmi)
        if bmi:
            reply_text = f"Your current BMI is **{bmi}** ({cat}). {bmi_engine.BMI_ADVICE.get(cat)}"
        else:
            reply_text = "I don't have your height/weight yet — please complete your profile first!"

    elif intent["intent"] == "weekly_plan":
        goal = intent.get("goal") or prof.goal
        equip = intent.get("equipment") or user_equipment
        weekly = exercise_engine.get_weekly_plan(current_app.config["EXERCISES_JSON"], goal, equip, per_day=3)
        reply_text = (f"Here's your day-to-day plan for **{goal.replace('_', ' ')}** 🗓️ "
                       f"Suggested tempo: {exercise_engine.suggested_sets_reps(goal)}.")
        card_type = "weekly_plan"
        cards = [{"day": d, "title": info["title"], "exercises": info["exercises"]} for d, info in weekly.items()]

    elif intent["intent"] == "diet":
        goal = intent.get("goal") or prof.goal
        calorie_target = bmi_engine.estimate_daily_calories(
            prof.weight_kg, prof.height_cm, prof.age, prof.gender, prof.activity_level, goal
        )
        diet_plan = diet_engine.build_daily_diet_plan(
            current_app.config["MEALS_JSON"], prof.diet_preference, goal, calorie_target
        )
        reply_text = (f"Here's a {prof.diet_preference.replace('_',' ')} meal plan for your "
                       f"**{goal.replace('_',' ')}** goal (~{calorie_target or '—'} kcal/day target).")
        card_type = "diet"
        cards = diet_plan["plan"]

    elif intent["intent"] in ("exercise_bodypart", "exercise_goal"):
        goal = intent.get("goal") or prof.goal
        equip = intent.get("equipment") or user_equipment
        if intent["intent"] == "exercise_bodypart":
            bp = intent["body_part"]
            results = exercise_engine.get_by_body_part(current_app.config["EXERCISES_JSON"], bp, equip)
            reply_text = f"Here are some great **{bp}** exercises for you 💪 ({exercise_engine.suggested_sets_reps(goal)})"
        else:
            results = exercise_engine.get_by_goal(current_app.config["EXERCISES_JSON"], goal, equip)
            reply_text = f"Here's a workout aimed at **{goal.replace('_',' ')}** 🔥 ({exercise_engine.suggested_sets_reps(goal)})"
        cards = results

    elif intent["intent"] == "search":
        results = exercise_engine.search_by_name(current_app.config["EXERCISES_JSON"], intent["query"])
        if results:
            reply_text = f"Found {len(results)} exercise(s) matching \"{intent['query']}\":"
            cards = results
        else:
            reply_text = f"I couldn't find an exercise matching \"{intent['query']}\". Try a body part like chest, back, or legs."

    else:
        reply_text = quotes.random_fallback()

    db.session.add(ChatLog(user_id=user.id, sender="bot", message=reply_text))
    db.session.commit()

    return jsonify({"reply": reply_text, "cards": cards, "card_type": card_type})


@main_bp.route("/progress", methods=["GET", "POST"])
@login_required
def progress():
    user = current_user()
    if request.method == "POST":
        log = ProgressLog(
            user_id=user.id,
            log_date=date.today(),
            workouts_completed=int(request.form.get("workouts_completed") or 0),
            weight_kg=float(request.form.get("weight_kg") or 0) or None,
            notes=request.form.get("notes", "")[:255],
        )
        db.session.add(log)
        db.session.commit()
        flash("Progress logged! Keep up the streak. 🔥", "success")
        return redirect(url_for("main.progress"))

    logs = ProgressLog.query.filter_by(user_id=user.id).order_by(ProgressLog.log_date.asc()).all()
    return render_template("progress.html", logs=logs, profile=user.profile)


@main_bp.route("/report/download")
@login_required
def download_report():
    user = current_user()
    prof = user.profile
    bmi = prof.bmi()
    bmi_cat = bmi_engine.bmi_category(bmi)
    calorie_target = bmi_engine.estimate_daily_calories(
        prof.weight_kg, prof.height_cm, prof.age, prof.gender, prof.activity_level, prof.goal
    )
    protein_target = bmi_engine.protein_target_g(prof.weight_kg, prof.goal)

    equip = prof.available_equipment.split(",") if prof.available_equipment else None
    weekly = exercise_engine.get_weekly_plan(current_app.config["EXERCISES_JSON"], prof.goal, equip, per_day=3)
    weekly_summary = {
        d: {"title": info["title"], "exercise_names": [e["name"] for e in info["exercises"]]}
        for d, info in weekly.items()
    }

    diet_plan = diet_engine.build_daily_diet_plan(
        current_app.config["MEALS_JSON"], prof.diet_preference, prof.goal, calorie_target
    )["plan"]

    logs = ProgressLog.query.filter_by(user_id=user.id).order_by(ProgressLog.log_date.desc()).limit(10).all()

    path = pdf_report.generate_progress_report(
        current_app.config["REPORTS_DIR"], user, prof, bmi, bmi_cat, calorie_target,
        protein_target, diet_plan, weekly_summary, logs
    )
    return send_file(path, as_attachment=True)
