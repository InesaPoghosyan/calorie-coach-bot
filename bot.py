# === 📦 Standard Library & Third-Party Imports ===
import os
import re
import requests
from io import BytesIO
from PIL import Image
import torch
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from transformers import ViTFeatureExtractor, ViTForImageClassification
from nlp import generate_conversational_reply, generate_feedback_with_gpt

# === 🔐 Load Environment Variables ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_ID = os.getenv("APP_ID")
APP_KEY = os.getenv("APP_KEY")

# === 🧠 Load Vision Transformer (ViT) for Food Classification ===
feature_extractor = ViTFeatureExtractor.from_pretrained("nateraw/vit-base-food101")
model = ViTForImageClassification.from_pretrained("nateraw/vit-base-food101")
model.eval()

# === 🍳 Parse Ingredient Descriptions ===
def parse_ingredients(text):
    """
    Extract quantities and food names from user-written meal descriptions.
    """
    parts = re.split(r',|with|and', text.lower())
    ingredients = []
    for part in parts:
        part = part.strip()
        match = re.match(r'(\d*\.?\d+|one|two|three|four|five)?\s*(\w+)?\s*(.+)', part)
        if match:
            qty = match.group(1)
            if qty is None:
                qty = 1
            else:
                text_nums = {"one":1,"two":2,"three":3,"four":4,"five":5}
                qty = text_nums.get(qty, qty)
                try:
                    qty = float(qty)
                except:
                    qty = 1
            unit = match.group(2) or "unit"
            name = match.group(3).strip()
            ingredients.append({'quantity': qty, 'unit': unit, 'name': name})
    return ingredients

# === 📊 Query Nutritionix API for Calories and Macros ===
def get_nutrition(query):
    """
    Fetch nutrition information using Nutritionix's natural language API.
    """
    url = "https://trackapi.nutritionix.com/v2/natural/nutrients"
    headers = {
        "x-app-id": APP_ID,
        "x-app-key": APP_KEY,
        "Content-Type": "application/json"
    }
    data = {"query": query}
    res = requests.post(url, headers=headers, json=data)
    if res.status_code == 200:
        return res.json().get('foods', [])
    return []

# === 🤖 Telegram Command: /start ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hi! Send me a **food photo** or type what you ate!")

# === 📖 Telegram Command: /help ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 Send a photo or write something like:\n'I ate 2 boiled eggs and toast.'")

# === 💬 Telegram Command: /quote ===
async def quote_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from main.nlp import QUOTES
    await update.message.reply_text(random.choice(QUOTES))

# === 🖼️ Handle Food Photo Uploads ===
async def handle_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Detect food in an image, classify it using ViT, and return nutrition + GPT advice.
    """
    photo = update.message.photo[-1]
    file = await context.bot.get_file(photo.file_id)
    image_bytes = await file.download_as_bytearray()

    image = Image.open(BytesIO(image_bytes)).convert("RGB")
    inputs = feature_extractor(images=image, return_tensors="pt")

    with torch.no_grad():
        outputs = model(**inputs)
        logits = outputs.logits
        predicted_class_idx = logits.argmax(-1).item()
        food_name = model.config.id2label[predicted_class_idx]

    await update.message.reply_text(f"📸 I think this is *{food_name}*. Let me analyze it...")

    foods = get_nutrition(food_name)
    if not foods:
        await update.message.reply_text("⚠️ Couldn't find nutrition info.")
        return

    total_calories = sum(f.get('nf_calories', 0) for f in foods)

    # Fake ingredient list for GPT context
    fake_ingredients = [{'quantity': 1, 'unit': 'unit', 'name': food_name}]
    advice = generate_feedback_with_gpt(fake_ingredients, total_calories, foods)

    nutrition_summary = (
        f"Calories: {int(total_calories)} kcal\n"
        f"Protein: {sum(f.get('nf_protein', 0) for f in foods):.1f}g\n"
        f"Fat: {sum(f.get('nf_total_fat', 0) for f in foods):.1f}g\n"
        f"Sugar: {sum(f.get('nf_sugars', 0) for f in foods):.1f}g"
    )

    await update.message.reply_text(
        f"🧾 *Nutrition Summary for {food_name}:*\n```{nutrition_summary}```\n\n{advice}",
        parse_mode="Markdown"
    )

# === ✍️ Handle Text Input (Ingredient Description or Chat) ===
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle user text: Try chatbot response first, then analyze ingredients.
    """
    user_text = update.message.text

    # Try to generate a casual reply
    conv_reply = generate_conversational_reply(user_text)
    if conv_reply:
        await update.message.reply_text(conv_reply)
        return

    # Try to parse food and give feedback
    ingredients = parse_ingredients(user_text)
    if not ingredients:
        await update.message.reply_text("❌ I couldn't understand. Please describe your meal more clearly.")
        return

    query = ', '.join(f"{i['quantity']} {i['unit']} {i['name']}" for i in ingredients)
    foods = get_nutrition(query)
    if not foods:
        await update.message.reply_text("⚠️ Sorry, I couldn't find nutrition data for that.")
        return

    total_calories = sum(f.get('nf_calories', 0) for f in foods)
    advice = generate_feedback_with_gpt(ingredients, total_calories, foods)

    nutrition_summary = (
        f"Calories: {int(total_calories)} kcal\n"
        f"Protein: {sum(f.get('nf_protein', 0) for f in foods):.1f}g\n"
        f"Fat: {sum(f.get('nf_total_fat', 0) for f in foods):.1f}g\n"
        f"Sugar: {sum(f.get('nf_sugars', 0) for f in foods):.1f}g"
    )

    await update.message.reply_text(
        f"🧾 *Nutrition Summary:*\n```{nutrition_summary}```\n\n{advice}",
        parse_mode="Markdown"
    )

# === ❓ Handle Unknown Commands ===
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❓ Unknown command. Use /help to learn how to use me!")

# === 🚀 Main Entrypoint: Run Telegram Bot ===
if __name__ == "__main__":
    import random  # Used for /quote

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Register command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("quote", quote_command))

    # Register message handlers
    app.add_handler(MessageHandler(filters.PHOTO, handle_image))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.COMMAND, unknown))

    print("🤖 GPT-powered Calorie Coach is running...")
    app.run_polling()
