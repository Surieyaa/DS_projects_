import random

MOTIVATIONAL_QUOTES = [
    "The only bad workout is the one that didn't happen. Let's get moving! 💪",
    "Your body can stand almost anything. It's your mind you have to convince.",
    "Progress, not perfection. Every rep counts.",
    "Discipline is choosing between what you want now and what you want most.",
    "Small daily improvements lead to staggering long-term results.",
    "Sweat is just fat crying. Keep going!",
    "You don't have to be extreme, just consistent.",
    "The pain of discipline is far less than the pain of regret.",
    "Push yourself, because no one else is going to do it for you.",
    "A one-hour workout is 4% of your day. No excuses.",
    "Champions train, losers complain. Which one are you today?",
    "Strength doesn't come from what you can do. It comes from overcoming what you thought you couldn't.",
    "Wake up. Work out. Look hot. Kick ass.",
    "Take care of your body. It's the only place you have to live.",
    "The body achieves what the mind believes.",
]

GREETING_RESPONSES = [
    "Hey there, champion! 🔥 Ready to crush today's goals? Tell me what you're working toward — chest, abs, weight loss, or a full plan?",
    "Welcome back! 💪 I'm your AI trainer — ask me for exercises by body part, a full day plan, or a diet recommendation.",
    "Let's get to work! What are we training today?",
]

FALLBACK_RESPONSES = [
    "I can help with workouts, body-part exercises, diet plans, or your BMI. Try: \"I want a bigger chest\" or \"give me a leg day plan\".",
    "Not quite sure what you mean — but I've got you. Ask me things like \"I want six pack abs\" or \"suggest a high protein diet\".",
]


def random_quote():
    return random.choice(MOTIVATIONAL_QUOTES)


def random_greeting():
    return random.choice(GREETING_RESPONSES)


def random_fallback():
    return random.choice(FALLBACK_RESPONSES)
