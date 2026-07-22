import json
import random

_EXERCISES = None

# Maps user-facing body part / goal keywords to the dataset's body_part & target values
BODY_PART_ALIASES = {
    "chest": ["chest"],
    "back": ["back"],
    "lats": ["back"],
    "shoulders": ["shoulders"],
    "delts": ["shoulders"],
    "arms": ["upper arms", "lower arms"],
    "biceps": ["upper arms"],
    "triceps": ["upper arms"],
    "forearms": ["lower arms"],
    "legs": ["upper legs", "lower legs"],
    "thighs": ["upper legs"],
    "quads": ["upper legs"],
    "hamstrings": ["upper legs"],
    "glutes": ["upper legs"],
    "calves": ["lower legs"],
    "abs": ["waist"],
    "core": ["waist"],
    "waist": ["waist"],
    "six pack": ["waist"],
    "cardio": ["cardio"],
    "neck": ["neck"],
    "full body": ["chest", "back", "upper legs", "waist", "shoulders", "upper arms"],
}

# Goal -> ordered list of body parts to prioritize + workout split
GOAL_BODY_PARTS = {
    "muscle_gain": ["chest", "back", "shoulders", "upper legs", "upper arms"],
    "bodybuilding": ["chest", "back", "shoulders", "upper legs", "upper arms", "lower legs"],
    "fat_loss": ["cardio", "waist", "upper legs", "back", "chest"],
    "weight_loss": ["cardio", "waist", "upper legs", "back", "chest"],
    "six_pack": ["waist", "cardio"],
    "general_fitness": ["chest", "back", "upper legs", "waist", "shoulders", "cardio"],
}

# A simple 5-day split for "day to day" plans
WEEKLY_SPLIT = {
    "Monday": {"title": "Push Day (Chest, Shoulders, Triceps)", "body_parts": ["chest", "shoulders"]},
    "Tuesday": {"title": "Pull Day (Back, Biceps)", "body_parts": ["back"]},
    "Wednesday": {"title": "Leg Day (Quads, Hamstrings, Glutes, Calves)", "body_parts": ["upper legs", "lower legs"]},
    "Thursday": {"title": "Core & Cardio", "body_parts": ["waist", "cardio"]},
    "Friday": {"title": "Upper Body Strength", "body_parts": ["chest", "back", "shoulders"]},
    "Saturday": {"title": "Full Body + Cardio", "body_parts": ["upper legs", "chest", "cardio"]},
    "Sunday": {"title": "Active Recovery / Rest", "body_parts": []},
}


def load_exercises(path):
    global _EXERCISES
    if _EXERCISES is None:
        with open(path, "r", encoding="utf-8") as f:
            _EXERCISES = json.load(f)
    return _EXERCISES


def _equipment_filter(exercises, equipment_list):
    if not equipment_list:
        return exercises
    allowed = {e.strip().lower() for e in equipment_list}
    return [ex for ex in exercises if ex["equipment"].lower() in allowed]


def get_by_body_part(path, body_part_keyword, equipment_list=None, limit=6):
    exercises = load_exercises(path)
    targets = BODY_PART_ALIASES.get(body_part_keyword.lower(), [body_part_keyword.lower()])
    matches = [ex for ex in exercises if ex["body_part"].lower() in targets]
    matches = _equipment_filter(matches, equipment_list)
    if not matches:
        matches = [ex for ex in exercises if ex["body_part"].lower() in targets]
    random.shuffle(matches)
    return matches[:limit]


def get_by_goal(path, goal, equipment_list=None, limit=6):
    exercises = load_exercises(path)
    body_parts = GOAL_BODY_PARTS.get(goal, GOAL_BODY_PARTS["general_fitness"])
    matches = [ex for ex in exercises if ex["body_part"].lower() in body_parts]
    matches = _equipment_filter(matches, equipment_list)
    if not matches:
        matches = [ex for ex in exercises if ex["body_part"].lower() in body_parts]
    random.shuffle(matches)
    return matches[:limit]


def search_by_name(path, query, limit=6):
    exercises = load_exercises(path)
    q = query.lower()
    matches = [ex for ex in exercises if q in ex["name"].lower()]
    return matches[:limit]


def get_weekly_plan(path, goal, equipment_list=None, per_day=4):
    """Builds a full day-to-day (Mon-Sun) exercise plan."""
    plan = {}
    for day, info in WEEKLY_SPLIT.items():
        if not info["body_parts"]:
            plan[day] = {"title": info["title"], "exercises": []}
            continue
        exercises = load_exercises(path)
        matches = [ex for ex in exercises if ex["body_part"].lower() in info["body_parts"]]
        matches = _equipment_filter(matches, equipment_list) or matches
        random.shuffle(matches)
        plan[day] = {"title": info["title"], "exercises": matches[:per_day]}
    return plan


SETS_REPS_BY_GOAL = {
    "muscle_gain": "4 sets x 8-10 reps, 60-90s rest",
    "bodybuilding": "4-5 sets x 8-12 reps, 60-90s rest",
    "fat_loss": "3 sets x 15-20 reps, 30-45s rest",
    "weight_loss": "3 sets x 15-20 reps, 30-45s rest",
    "six_pack": "3-4 sets x 15-25 reps, 30s rest",
    "general_fitness": "3 sets x 12-15 reps, 45-60s rest",
}


def suggested_sets_reps(goal):
    return SETS_REPS_BY_GOAL.get(goal, SETS_REPS_BY_GOAL["general_fitness"])
