import re

GREETING_WORDS = {"hi", "hello", "hey", "yo", "sup", "hola", "namaste", "good morning", "good evening"}

MOTIVATION_TRIGGERS = ["motivate", "motivation", "inspire", "quote", "encourage", "give up", "lazy", "tired of trying"]

BMI_TRIGGERS = ["bmi", "body mass index", "am i overweight", "am i fat", "my weight status"]

WEEKLY_PLAN_TRIGGERS = [
    "day to day", "daily plan", "weekly plan", "weekly schedule", "full week",
    "workout plan", "training plan", "week plan", "schedule for the week", "routine for the week",
]

DIET_TRIGGERS = ["diet", "meal", "food", "eat", "nutrition", "calorie", "protein intake", "what should i eat"]

# goal -> trigger phrases (checked as substrings, ordered by specificity)
GOAL_PATTERNS = [
    ("six_pack", [r"six.?pack", r"6.?pack", r"flat stomach", r"abs\b.*\b(cut|visible|shred)"]),
    ("bodybuilding", [r"bodybuilding", r"body building", r"bulk(ing)?\b", r"mass gain"]),
    ("muscle_gain", [r"bigger (chest|arms|back|shoulders|legs|biceps)", r"build muscle", r"gain muscle",
                      r"muscle gain", r"get (bigger|stronger)", r"tone up", r"get toned"]),
    ("fat_loss", [r"lose weight", r"weight loss", r"fat loss", r"lose fat", r"burn fat", r"get lean",
                   r"slim down", r"cut(ting)? (weight|fat)"]),
    ("general_fitness", [r"general fitness", r"stay fit", r"overall fitness", r"get fit", r"be healthy"]),
]

BODY_PART_PATTERNS = {
    "chest": [r"\bchest\b", r"\bpecs?\b"],
    "back": [r"\bback\b", r"\blats?\b"],
    "shoulders": [r"\bshoulders?\b", r"\bdelts?\b"],
    "arms": [r"\barms?\b"],
    "biceps": [r"\bbiceps?\b"],
    "triceps": [r"\btriceps?\b"],
    "forearms": [r"\bforearms?\b"],
    "legs": [r"\blegs?\b"],
    "thighs": [r"\bthighs?\b", r"\bquads?\b"],
    "hamstrings": [r"\bhamstrings?\b"],
    "glutes": [r"\bglutes?\b", r"\bbutt\b"],
    "calves": [r"\bcalves\b", r"\bcalf\b"],
    "abs": [r"\babs?\b", r"\bcore\b", r"\bstomach\b", r"\bbelly\b"],
    "cardio": [r"\bcardio\b", r"\brunning\b", r"\bendurance\b"],
    "full body": [r"full body", r"whole body", r"total body"],
}

EQUIPMENT_PATTERNS = {
    "body weight": [r"no equipment", r"bodyweight", r"body weight", r"without equipment", r"at home", r"no gym"],
    "dumbbell": [r"dumbbells?"],
    "barbell": [r"\bbarbell\b"],
    "kettlebell": [r"kettlebells?"],
    "band": [r"resistance bands?", r"\bbands?\b"],
    "cable": [r"\bcable\b"],
    "smith machine": [r"smith machine"],
    "leverage machine": [r"machine"],
}


def _find_first(text, patterns_dict):
    for key, patterns in patterns_dict.items():
        for pat in patterns:
            if re.search(pat, text):
                return key
    return None


def detect_equipment(text):
    found = []
    for key, patterns in EQUIPMENT_PATTERNS.items():
        for pat in patterns:
            if re.search(pat, text):
                found.append(key)
                break
    return list(dict.fromkeys(found))  # de-dup, preserve order


def detect_intent(message, user_goal=None, user_equipment=None):
    text = message.lower().strip()

    if any(text == g or text.startswith(g) for g in GREETING_WORDS) and len(text.split()) <= 4:
        return {"intent": "greeting"}

    if any(t in text for t in MOTIVATION_TRIGGERS):
        return {"intent": "motivation"}

    if any(t in text for t in BMI_TRIGGERS):
        return {"intent": "bmi"}

    equipment = detect_equipment(text)

    if any(t in text for t in WEEKLY_PLAN_TRIGGERS):
        goal = _detect_goal(text) or user_goal or "general_fitness"
        return {"intent": "weekly_plan", "goal": goal, "equipment": equipment or user_equipment}

    if any(t in text for t in DIET_TRIGGERS):
        goal = _detect_goal(text) or user_goal or "general_fitness"
        return {"intent": "diet", "goal": goal}

    body_part = _find_first(text, BODY_PART_PATTERNS)
    goal = _detect_goal(text)

    if body_part:
        return {"intent": "exercise_bodypart", "body_part": body_part, "goal": goal or user_goal,
                 "equipment": equipment or user_equipment}

    if goal:
        return {"intent": "exercise_goal", "goal": goal, "equipment": equipment or user_equipment}

    if equipment and not body_part and not goal:
        return {"intent": "exercise_goal", "goal": user_goal or "general_fitness", "equipment": equipment}

    # try a direct exercise-name search e.g. "show me push ups"
    search_match = re.search(r"(?:show|find|search)(?: me)? (.+)", text)
    if search_match:
        return {"intent": "search", "query": search_match.group(1).strip()}

    return {"intent": "unknown"}


def _detect_goal(text):
    for goal, patterns in GOAL_PATTERNS:
        for pat in patterns:
            if re.search(pat, text):
                return goal
    return None
