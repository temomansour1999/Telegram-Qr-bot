import os
import qrcode
from PIL import Image
import requests
from io import BytesIO
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, ConversationHandler
)

# Load Bot Token
TOKEN = os.getenv("BOT_TOKEN")
print("Loaded Token:", TOKEN)

# States
LANGUAGE, PLATFORM, WEBSITE_COLOR, GET_LINK = range(4)

# Platform configuration
PLATFORM_CONFIG = {
    "Website": {
        "color_choice": True,
        "default_color": "black",
    },
    "Facebook": {
        "color_choice": False,
        "default_color": "#1877F2",
    },
    "Instagram": {
        "color_choice": False,
        "default_color": "#E4405F",
    },
    "Twitter": {
        "color_choice": False,
        "default_color": "#1DA1F2",
    }
}

# Messages
MESSAGES = {
    "en": {
        "welcome": "Welcome! Please choose your language:",
        "choose_platform": "Choose the platform:",
        "choose_color": "Choose a color:",
        "enter_link": "Send the link to convert to QR:",
        "processing": "Processing...",
        "invalid_link": "Invalid link! Must start with http or https",
        "success": "Here is your QR:",
        "cancel": "Cancelled.",
        "error": "Error occurred."
    },
    "ar": {
        "welcome": "مرحباً! اختر لغتك:",
        "choose_platform": "اختر المنصة:",
        "choose_color": "اختر اللون:",
        "enter_link": "أرسل الرابط لتحويله إلى QR:",
        "processing": "جاري المعالجة...",
        "invalid_link": "رابط غير صالح!",
        "success": "إليك رمز QR:",
        "cancel": "تم الإلغاء.",
        "error": "حدث خطأ."
    }
}

# Start Command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [["English 🇺🇸", "العربية 🇸🇦"]]
    await update.message.reply_text(
        "Welcome! Please choose your language:",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True)
    )
    return LANGUAGE


async def choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = "ar" if "العربية" in update.message.text else "en"
    context.user_data["language"] = lang
    msg = MESSAGES[lang]

    if lang == "ar":
        platforms = ["موقع ويب", "فيسبوك", "انستغرام", "تويتر"]
    else:
        platforms = ["Website", "Facebook", "Instagram", "Twitter"]

    context.user_data["platforms"] = platforms

    await update.message.reply_text(
        msg["choose_platform"],
        reply_markup=ReplyKeyboardMarkup([[p] for p in platforms], one_time_keyboard=True)
    )
    return PLATFORM


async def choose_platform(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_platform = update.message.text
    lang = context.user_data["language"]

    mapping = {
        "ar": {"موقع ويب": "Website", "فيسبوك": "Facebook", "انستغرام": "Instagram", "تويتر": "Twitter"},
        "en": {"Website": "Website", "Facebook": "Facebook", "Instagram": "Instagram", "Twitter": "Twitter"}
    }

    platform = mapping[lang].get(user_platform, "Website")
    context.user_data["platform"] = platform

    msg = MESSAGES[lang]
    cfg = PLATFORM_CONFIG[platform]

    if cfg["color_choice"]:
        colors = ["Black", "Blue", "Red", "Green", "Purple"] if lang == "en" else ["أسود", "أزرق", "أحمر", "أخضر", "بنفسجي"]
        context.user_data["colors"] = colors

        await update.message.reply_text(
            msg["choose_color"],
            reply_markup=ReplyKeyboardMarkup([[c] for c in colors], one_time_keyboard=True)
        )
        return WEBSITE_COLOR

    else:
        await update.message.reply_text(msg["enter_link"], reply_markup=ReplyKeyboardRemove())
        return GET_LINK


async def choose_color(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_color = update.message.text
    lang = context.user_data["language"]

    mapping = {
        "en": {"Black": "black", "Blue": "blue", "Red": "red", "Green": "green", "Purple": "purple"},
        "ar": {"أسود": "black", "أزرق": "blue", "أحمر": "red", "أخضر": "green", "بنفسجي": "purple"}
    }

    context.user_data["color"] = mapping[lang].get(user_color, "black")
    msg = MESSAGES[lang]

    await update.message.reply_text(msg["enter_link"], reply_markup=ReplyKeyboardRemove())
    return GET_LINK


def generate_qr_code(link, color):
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
    qr.add_data(link)
    qr.make(fit=True)
    return qr.make_image(fill_color=color, back_color="white").convert("RGB")


async def generate_qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = update.message.text
    lang = context.user_data["language"]
    msg = MESSAGES[lang]

    if not link.startswith(("http://", "https://")):
        await update.message.reply_text(msg["invalid_link"])
        return GET_LINK

    await update.message.reply_text(msg["processing"])

    platform = context.user_data["platform"]
    config = PLATFORM_CONFIG[platform]

    color = context.user_data.get("color", config["default_color"])

    qr_img = generate_qr_code(link, color)

    output = BytesIO()
    qr_img.save(output, "PNG")
    output.seek(0)

    await update.message.reply_photo(photo=output, caption=msg["success"])

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("language", "en")
    await update.message.reply_text(MESSAGES[lang]["cancel"])
    return ConversationHandler.END


# Flask server for Railway
app = Flask(__name__)

@app.route("/")
def home():
    return "QR Bot is running!"


def run_web():
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)


def main():
    application = Application.builder().token(TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LANGUAGE: [MessageHandler(filters.TEXT, choose_language)],
            PLATFORM: [MessageHandler(filters.TEXT, choose_platform)],
            WEBSITE_COLOR: [MessageHandler(filters.TEXT, choose_color)],
            GET_LINK: [MessageHandler(filters.TEXT, generate_qr)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    application.add_handler(conv)

    # Run flask server
    Thread(target=run_web, daemon=True).start()

    print("Bot running on Railway...")
    application.run_polling()


if __name__ == "__main__":
    main()
