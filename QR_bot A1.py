import os
import qrcode
from PIL import Image
import requests
from io import BytesIO
from flask import Flask
from threading import Thread
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler

# Your bot token - get this from BotFather
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Your channel info (optional - you can remove if causing issues)
CHANNEL_USERNAME = "@your_channel_username"
CHANNEL_LINK = "https://t.me/your_channel_username"

# Conversation states
LANGUAGE, PLATFORM, WEBSITE_COLOR, GET_LINK = range(4)

# Platform configuration
PLATFORM_CONFIG = {
    "Website": {
        "color_choice": True,
        "default_color": "black",
        "icon": None
    },
    "Facebook": {
        "color_choice": False,
        "default_color": "#1877F2",
        "icon": None  # Simplified for Replit
    },
    "Instagram": {
        "color_choice": False,
        "default_color": "#E4405F",
        "icon": None  # Simplified for Replit
    },
    "Twitter": {
        "color_choice": False,
        "default_color": "#1DA1F2",
        "icon": None  # Simplified for Replit
    }
}

# Messages in different languages
MESSAGES = {
    "en": {
        "welcome": "Welcome! Please choose your language:",
        "choose_platform": "Choose the platform for your QR code:",
        "choose_color": "Choose a color for your QR code:",
        "enter_link":
        "Please send me the link you want to convert to QR code:",
        "processing": "🔄 Processing your QR code...",
        "invalid_link":
        "❌ Please send a valid link (starting with http:// or https://)",
        "error": "❌ An error occurred. Please try again.",
        "success": "✅ Here's your QR code!",
        "cancel": "Operation cancelled."
    },
    "ar": {
        "welcome": "مرحباً! الرجاء اختيار اللغة:",
        "choose_platform": "اختر المنصة لرمز الاستجابة السريعة (QR) الخاص بك:",
        "choose_color": "اختر لوناً لرمز الاستجابة السريعة (QR) الخاص بك:",
        "enter_link":
        "الرجاء إرسال الرابط الذي تريد تحويله إلى رمز استجابة سريعة (QR):",
        "processing": "🔄 جاري معالجة رمز الاستجابة السريعة (QR) الخاص بك...",
        "invalid_link":
        "❌ الرجاء إرسال رابط صحيح (يبدأ بـ http:// أو https://)",
        "error": "❌ حدث خطأ. الرجاء المحاولة مرة أخرى.",
        "success": "✅ هذا هو رمز الاستجابة السريعة (QR) الخاص بك!",
        "cancel": "تم إلغاء العملية."
    }
}


# Simplified start function (removed channel check for now)
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the conversation."""
    keyboard = [["English 🇺🇸", "العربية 🇸🇦"]]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)

    await update.message.reply_text("Welcome! Please choose your language:",
                                    reply_markup=reply_markup)
    return LANGUAGE


async def choose_language(update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the selected language and ask for platform."""
    user_choice = update.message.text

    if user_choice == "العربية 🇸🇦":
        context.user_data['language'] = "ar"
    else:
        context.user_data['language'] = "en"

    lang_code = context.user_data['language']
    messages = MESSAGES[lang_code]

    if lang_code == "ar":
        platforms = ["موقع ويب", "فيسبوك", "انستغرام", "تويتر"]
    else:
        platforms = ["Website", "Facebook", "Instagram", "Twitter"]

    context.user_data['platforms_display'] = platforms

    keyboard = [[platform] for platform in platforms]
    reply_markup = ReplyKeyboardMarkup(keyboard,
                                       one_time_keyboard=True,
                                       resize_keyboard=True)

    await update.message.reply_text(messages["choose_platform"],
                                    reply_markup=reply_markup)
    return PLATFORM


async def choose_platform(update: Update,
                          context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the selected platform."""
    user_platform = update.message.text
    lang_code = context.user_data.get('language', 'en')

    platform_mapping = {
        "en": {
            "Website": "Website",
            "Facebook": "Facebook",
            "Instagram": "Instagram",
            "Twitter": "Twitter"
        },
        "ar": {
            "موقع ويب": "Website",
            "فيسبوك": "Facebook",
            "انستغرام": "Instagram",
            "تويتر": "Twitter"
        }
    }

    context.user_data['platform'] = platform_mapping[lang_code].get(
        user_platform, "Website")
    messages = MESSAGES[lang_code]

    platform_config = PLATFORM_CONFIG.get(context.user_data['platform'],
                                          PLATFORM_CONFIG["Website"])

    if platform_config["color_choice"]:
        if lang_code == "ar":
            colors = ["أسود", "أزرق", "أحمر", "أخضر", "بنفسجي"]
        else:
            colors = ["Black", "Blue", "Red", "Green", "Purple"]

        context.user_data['colors_display'] = colors

        keyboard = [[color] for color in colors]
        reply_markup = ReplyKeyboardMarkup(keyboard,
                                           one_time_keyboard=True,
                                           resize_keyboard=True)

        await update.message.reply_text(messages["choose_color"],
                                        reply_markup=reply_markup)
        return WEBSITE_COLOR
    else:
        await update.message.reply_text(messages["enter_link"],
                                        reply_markup=ReplyKeyboardRemove())
        return GET_LINK


async def choose_color(update: Update,
                       context: ContextTypes.DEFAULT_TYPE) -> int:
    """Store the selected color."""
    color_name = update.message.text
    lang_code = context.user_data.get('language', 'en')

    color_mapping = {
        "en": {
            "Black": "black",
            "Blue": "blue",
            "Red": "red",
            "Green": "green",
            "Purple": "purple"
        },
        "ar": {
            "أسود": "black",
            "أزرق": "blue",
            "أحمر": "red",
            "أخضر": "green",
            "بنفسجي": "purple"
        }
    }

    context.user_data['color'] = color_mapping[lang_code].get(
        color_name, "black")
    messages = MESSAGES[lang_code]

    await update.message.reply_text(messages["enter_link"],
                                    reply_markup=ReplyKeyboardRemove())
    return GET_LINK


def generate_qr_code(link, color, platform=None):
    """Generate QR code without icons for simplicity."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(link)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color=color, back_color="white").convert('RGB')
    return qr_img


async def generate_qr(update: Update,
                      context: ContextTypes.DEFAULT_TYPE) -> int:
    """Generate QR code from the provided link."""
    link = update.message.text

    if not link.startswith(('http://', 'https://')):
        lang_code = context.user_data.get('language', 'en')
        await update.message.reply_text(MESSAGES[lang_code]["invalid_link"])
        return GET_LINK

    lang_code = context.user_data.get('language', 'en')
    messages = MESSAGES[lang_code]

    await update.message.reply_text(messages["processing"])

    try:
        platform = context.user_data.get('platform', 'Website')
        platform_config = PLATFORM_CONFIG.get(platform,
                                              PLATFORM_CONFIG["Website"])

        if platform_config["color_choice"]:
            color = context.user_data.get('color', 'black')
        else:
            color = platform_config["default_color"]

        qr_img = generate_qr_code(link, color, platform)

        bio = BytesIO()
        qr_img.save(bio, 'PNG')
        bio.seek(0)

        await update.message.reply_photo(photo=bio,
                                         caption=messages["success"])

    except Exception as e:
        print(f"Error generating QR code: {e}")
        await update.message.reply_text(messages["error"])

    context.user_data.clear()
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the conversation."""
    lang_code = context.user_data.get('language', 'en')
    await update.message.reply_text(MESSAGES[lang_code]["cancel"],
                                    reply_markup=ReplyKeyboardRemove())
    context.user_data.clear()
    return ConversationHandler.END


# Flask server to keep Replit alive
app = Flask(__name__)


@app.route('/')
def home():
    return "🤖 QR Code Bot is running!"


def run_flask():
    app.run(host='0.0.0.0', port=8080)


def main() -> None:
    """Run the bot."""
    # Create application
    application = Application.builder().token(TOKEN).build()

    # Create conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            LANGUAGE:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_language)],
            PLATFORM:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_platform)],
            WEBSITE_COLOR:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, choose_color)],
            GET_LINK:
            [MessageHandler(filters.TEXT & ~filters.COMMAND, generate_qr)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)

    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    print("🤖 Bot is running on Replit...")
    application.run_polling()


if __name__ == '__main__':
    main()
