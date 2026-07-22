import json
import random

_MEALS = None

# Goal -> which dish_types / protein emphasis to favor
GOAL_MEAL_TIME_SPLIT = {
    "breakfast": ["breakfast", "breakfast/dinner"],
    "lunch": ["lunch", "lunch/dinner"],
    "dinner": ["dinner", "lunch/dinner", "breakfast/dinner"],
    "snack": ["snack"],
}


def load_meals(path):
    global _MEALS
    if _MEALS is None:
        with open(path, "r", encoding="utf-8") as f:
            _MEALS = json.load(f)
    return _MEALS


def _diet_filter(meals, diet_preference):
    if not diet_preference or diet_preference == "any":
        return meals
    return [m for m in meals if m["diet"] == diet_preference]


def get_meals_for_slot(path, slot, diet_preference="vegetarian", goal="general_fitness", limit=3):
    meals = load_meals(path)
    valid_times = GOAL_MEAL_TIME_SPLIT.get(slot, [slot])
    matches = [m for m in meals if m["meal_time"] in valid_times]
    matches = _diet_filter(matches, diet_preference) or matches

    # For muscle gain/bodybuilding, favor higher protein; for fat loss, favor lower calorie
    if goal in ("muscle_gain", "bodybuilding"):
        matches.sort(key=lambda m: m["protein"], reverse=True)
    elif goal in ("fat_loss", "weight_loss", "six_pack"):
        matches.sort(key=lambda m: m["calories"])
    else:
        random.shuffle(matches)

    return matches[:limit]


def build_daily_diet_plan(path, diet_preference="vegetarian", goal="general_fitness", calorie_target=None):
    plan = {}
    for slot in ["breakfast", "lunch", "snack", "dinner"]:
        plan[slot] = get_meals_for_slot(path, slot, diet_preference, goal, limit=2)

    total_cal = sum(m["calories"] for slot in plan.values() for m in slot[:1])
    total_protein = round(sum(m["protein"] for slot in plan.values() for m in slot[:1]), 1)

    return {
        "plan": plan,
        "estimated_calories": round(total_cal),
        "estimated_protein": total_protein,
        "calorie_target": calorie_target,
    }
