def calculate_bmi(weight_kg, height_cm):
    if not weight_kg or not height_cm:
        return None
    h_m = height_cm / 100
    return round(weight_kg / (h_m * h_m), 1)


def bmi_category(bmi):
    if bmi is None:
        return "unknown"
    if bmi < 18.5:
        return "underweight"
    if bmi < 25:
        return "normal"
    if bmi < 30:
        return "overweight"
    return "obese"


BMI_ADVICE = {
    "underweight": "You're below the healthy range — focus on a calorie surplus, strength training, and protein-rich meals to build lean mass.",
    "normal": "You're in a healthy range — great base to train for strength, definition, or performance goals.",
    "overweight": "A moderate calorie deficit plus consistent strength + cardio training will help you move toward the healthy range sustainably.",
    "obese": "Start with low-impact cardio and full-body strength work, paired with a sustainable calorie deficit. Small consistent steps compound fast.",
}


def estimate_daily_calories(weight_kg, height_cm, age, gender, activity_level, goal):
    """Mifflin-St Jeor BMR -> TDEE -> goal-adjusted calorie target."""
    if not all([weight_kg, height_cm, age]):
        return None

    if (gender or "").lower().startswith("f"):
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5

    activity_multipliers = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very_active": 1.9,
    }
    tdee = bmr * activity_multipliers.get(activity_level, 1.55)

    goal_adjustments = {
        "fat_loss": -0.20,
        "weight_loss": -0.20,
        "six_pack": -0.15,
        "muscle_gain": 0.12,
        "bodybuilding": 0.15,
        "general_fitness": 0.0,
    }
    tdee *= 1 + goal_adjustments.get(goal, 0.0)
    return round(tdee)


def protein_target_g(weight_kg, goal):
    """Grams of protein/day, scaled to bodyweight and goal."""
    if not weight_kg:
        return None
    multiplier = {
        "muscle_gain": 2.0,
        "bodybuilding": 2.2,
        "six_pack": 1.9,
        "fat_loss": 1.8,
        "weight_loss": 1.8,
        "general_fitness": 1.6,
    }.get(goal, 1.6)
    return round(weight_kg * multiplier)
