import random

# Motivational & wellness quotes
QUOTES = [
    "Remember, every healthy choice is a step toward a happier you! 🌟",
    "Small changes can make a big impact. Keep it up! 💪",
    "Your body deserves the best fuel — treat it well! 🥦",
    "Balance is key: enjoy your food and nourish your soul. 🍽️",
    "Health is a journey, not a sprint. One step at a time! 🚶‍♀️",
]

# Fun food facts
FOOD_FACTS = [
    "Did you know? Carrots were originally purple! 🥕",
    "Honey never spoils — archaeologists found edible honey in ancient Egyptian tombs! 🍯",
    "Tomatoes are fruits, botanically speaking. 🍅",
    "Broccoli contains more vitamin C than oranges! 🥦",
    "Apples float because they are 25% air! 🍏",
]

# Food jokes
JOKES = [
    "Why did the tomato turn red? Because it saw the salad dressing! 🍅😄",
    "What did the lettuce say to the celery? Quit stalking me! 🥬😂",
    "Why don’t eggs tell jokes? They’d crack each other up! 🥚🤣",
]

# Basic conversational intents and replies
CONVERSATIONS = {
    "hello": ["Hi there! 👋 How can I help you with your nutrition today?", "Hello! Ready to talk food and health? 😊"],
    "hi": ["Hey! Send me a food photo or describe your meal!", "Hi! What did you eat today? 🥗"],
    "thank you": ["You're welcome! Happy to help! 😊", "Anytime! Keep eating well! 🍎"],
    "thanks": ["My pleasure! Stay healthy! 🍀", "Glad to help! Let me know if you want advice."],
    "how are you": ["I’m great, thanks for asking! How about you?", "Feeling healthy and ready to help! What about you?"],
    "help": ["You can send me a food photo or describe your meal, and I'll give nutrition advice!"],
    "bye": ["Goodbye! Stay healthy! 👋", "See you later! Keep making great food choices!"],
    "fun fact": FOOD_FACTS,
    "joke": JOKES,
    "quote": QUOTES,
}

def generate_conversational_reply(user_text):
    """
    Checks if user text matches a known conversational phrase
    and returns a friendly reply, joke, fact, or quote.
    """
    text = user_text.lower()
    for key in CONVERSATIONS:
        if key in text:
            return random.choice(CONVERSATIONS[key])
    return None


def generate_feedback_with_gpt(ingredients, total_calories, nutrition_data):
    """
    Generates supportive, rule-based nutritional feedback, enriched with varied responses.
    """

    feedback_parts = []

    # General calorie advice
    if total_calories < 400:
        feedback_parts.append("🥣 That’s a light meal — great if you’re having a snack or watching your intake.")
    elif total_calories < 700:
        feedback_parts.append("✅ This seems like a well-balanced meal in terms of calories.")
    else:
        feedback_parts.append("🍽️ A high-calorie meal — be sure it fits into your daily goals!")

    # Protein check
    total_protein = sum(f.get('nf_protein', 0) for f in nutrition_data)
    if total_protein < 10:
        feedback_parts.append("💡 You could boost your protein with eggs, beans, yogurt, or lean meat.")
    elif total_protein > 20:
        feedback_parts.append("💪 Great protein intake — helps keep you full and supports your muscles!")

    # Fat check
    total_fat = sum(f.get('nf_total_fat', 0) for f in nutrition_data)
    if total_fat > 30:
        feedback_parts.append("⚠️ A bit high in fat — try grilling or steaming instead of frying.")
    elif total_fat < 10:
        feedback_parts.append("👍 Low in fat — clean and light!")

    # Sugar check
    total_sugar = sum(f.get('nf_sugars', 0) for f in nutrition_data)
    if total_sugar > 25:
        feedback_parts.append("🍭 Watch out for the sugar — consider reducing sweets or sugary drinks.")
    elif total_sugar < 5:
        feedback_parts.append("✅ Low sugar — excellent for balanced energy levels!")

    # Veggies suggestion
    food_names = [f.get("food_name", "").lower() for f in nutrition_data]
    veggies_keywords = ["vegetable", "salad", "spinach", "broccoli", "carrot", "lettuce", "kale", "cucumber"]
    if not any(any(v in name for v in veggies_keywords) for name in food_names):
        feedback_parts.append("🌱 Adding veggies next time would be great for fiber and nutrients!")

    # Add a random motivational quote to end nicely
    feedback_parts.append(random.choice(QUOTES))

    feedback = "\n".join(feedback_parts)
    return f"🧠 *Nutrition Tips Based on Your Meal:*\n{feedback}"

