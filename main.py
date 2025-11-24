import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from flask import Flask
from threading import Thread

# Your bot token - use environment variable for security
TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

ADMIN_ID = 6434820732

# Your channel info - REPLACE WITH YOUR ACTUAL CHANNEL
CHANNEL_USERNAME = "@tunderscore1999"  # Replace with your channel username
CHANNEL_LINK = "https://t.me/tunderscore1999"  # Replace with your channel link

# Flask server to keep Replit alive
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Service Bot is running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# ===============================
# Channel Membership Check
# ===============================
async def check_channel_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Check if user is a member of the required channel"""
    try:
        user_id = update.effective_user.id
        chat_member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)

        # Check if user is member
        if chat_member.status in ['creator', 'administrator', 'member']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False


# ===============================
# /start with Channel Check
# ===============================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if user is in channel
    is_member = await check_channel_membership(update, context)

    if not is_member:
        # Show join channel requirement
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "📢 **Please join our channel to use this bot!**\n\n"
            "Join the channel first, then click 'I've Joined' to continue.\n\n"
            "If you have any problem ask @Tammam19",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
        return

    # User is member, show language selection
    keyboard = [
        [
            InlineKeyboardButton("🌍 English", callback_data="lang_en"),
            InlineKeyboardButton("🌍 العربية", callback_data="lang_ar")
        ]
    ]
    await update.message.reply_text(
        "👋 Welcome! Please choose your language: if you have any problem ask @Tammam19",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===============================
# Membership Check Callback
# ===============================
async def check_membership_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    is_member = await check_channel_membership(update, context)

    if is_member:
        # Show language selection
        keyboard = [
            [
                InlineKeyboardButton("🌍 English", callback_data="lang_en"),
                InlineKeyboardButton("🌍 العربية", callback_data="lang_ar")
            ]
        ]
        await query.edit_message_text(
            "✅ Thank you for joining! Please choose your language:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        keyboard = [
            [InlineKeyboardButton("📢 Join Our Channel", url=CHANNEL_LINK)],
            [InlineKeyboardButton("✅ I've Joined", callback_data="check_membership")]
        ]
        await query.edit_message_text(
            "❌ I still can't see you in the channel. Please make sure you've joined and try again.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


# ===============================
# LANGUAGE SELECTED
# ===============================
async def language_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]
    context.user_data["lang"] = lang

    if lang == "en":
        text = "✨ Choose a service category: "
        keyboard = [
            [
                InlineKeyboardButton("💼 Professional", callback_data="cat_prof"),
                InlineKeyboardButton("🎨 Creative", callback_data="cat_design")
            ]
        ]
    else:
        text = "✨ اختر فئة الخدمة:"
        keyboard = [
            [
                InlineKeyboardButton("💼 خدمات مهنية", callback_data="cat_prof"),
                InlineKeyboardButton("🎨 خدمات تصميم", callback_data="cat_design")
            ]
        ]

    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ===============================
# CATEGORY SELECTED
# ===============================
async def category_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    cat = query.data
    context.user_data["category"] = cat
    lang = context.user_data.get("lang", "en")

    # PROFESSIONAL SERVICES
    if cat == "cat_prof":
        if lang == "en":
            text = "💼 Choose a professional service:"
            options = [
                ("🌐 Website Development", "service_web"),
                ("📱 Mobile Apps", "service_mobile"),
                ("🤖 Telegram Bot", "service_bot"),
                ("📄 CV / Portfolio", "service_cv")
            ]
        else:
            text = "💼 اختر خدمة مهنية:"
            options = [
                ("🌐 مواقع ويب", "service_web"),
                ("📱 تطبيقات موبايل", "service_mobile"),
                ("🤖 بوت تيليجرام", "service_bot"),
                ("📄 سيرة ذاتية / بورتفوليو", "service_cv")
            ]

    # DESIGN SERVICES
    elif cat == "cat_design":
        if lang == "en":
            text = "🎨 Choose a design service:"
            options = [
                ("🔵 Logo Design", "design_logo"),
                ("🟣 Poster / Flyer", "design_poster"),
                ("🟠 Commercial Ads", "design_ads"),
                ("🟢 UI / UX design", "design_uiux"),
                ("🖼 Image Editing", "design_edit")
            ]
        else:
            text = "🎨 اختر خدمة تصميم:"
            options = [
                ("🔵 تصميم شعار", "design_logo"),
                ("🟣 بوستر / فلاير", "design_poster"),
                ("🟠 إعلانات", "design_ads"),
                ("🟢 UI / UX", "design_uiux"),
                ("🖼 تعديل صور", "design_edit")
            ]

    keyboard = [[InlineKeyboardButton(o[0], callback_data=o[1])] for o in options]
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


# ===============================
# SERVICE TYPE SELECTED
# ===============================
async def service_type_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    service_data = query.data
    context.user_data["service_type"] = service_data

    lang = context.user_data.get("lang", "en")

    # Map service codes to readable names
    service_names = {
        "en": {
            "service_web": "Website Development",
            "service_mobile": "Mobile Apps", 
            "service_bot": "Telegram Bot",
            "service_cv": "CV / Portfolio",
            "design_logo": "Logo Design",
            "design_poster": "Poster / Flyer",
            "design_ads": "Commercial Ads",
            "design_uiux": "UI / UX Design",
            "design_edit": "Image Editing"
        },
        "ar": {
            "service_web": "تطوير مواقع ويب",
            "service_mobile": "تطبيقات موبايل",
            "service_bot": "بوت تيليجرام", 
            "service_cv": "سيرة ذاتية / بورتفوليو",
            "design_logo": "تصميم شعار",
            "design_poster": "بوستر / فلاير",
            "design_ads": "إعلانات تجارية",
            "design_uiux": "تصميم واجهات",
            "design_edit": "تعديل الصور"
        }
    }

    context.user_data["service_name"] = service_names[lang].get(service_data, "Service")

    # SPECIAL HANDLING FOR IMAGE EDITING
    if service_data == "design_edit":
        if lang == "en":
            text = "🖼 **Image Editing Service**\n\n📸 Please send the photo you want to edit:"
        else:
            text = "🖼 **خدمة تعديل الصور**\n\n📸 من فضلك أرسل الصورة التي تريد تعديلها:"

        await query.edit_message_text(text, parse_mode="Markdown")
        context.user_data["awaiting_photo"] = True
        return

    # REGULAR TEXT DESCRIPTION FOR OTHER SERVICES
    if lang == "en":
        if service_data.startswith("service_"):
            text = f"💼 {service_names[lang][service_data]}\n\n✏️ Please describe your project requirements:"
        else:
            text = f"🎨 {service_names[lang][service_data]}\n\n✏️ Please describe your design requirements:"
    else:
        if service_data.startswith("service_"):
            text = f"💼 {service_names[lang][service_data]}\n\n✏️ من فضلك اكتب متطلبات المشروع:"
        else:
            text = f"🎨 {service_names[lang][service_data]}\n\n✏️ من فضلك اكتب متطلبات التصميم:"

    await query.edit_message_text(text)
    context.user_data["awaiting_description"] = True


# ===============================
# HANDLE PHOTO UPLOAD
# ===============================
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("awaiting_photo"):
        return

    photo = update.message.photo[-1]  # Get highest quality photo
    context.user_data["awaiting_photo"] = False

    lang = context.user_data.get("lang", "en")

    if lang == "en":
        text = "📸 Photo received! Now please describe what edits you want:"
    else:
        text = "📸 تم استلام الصورة! الآن من فضلك اصف التعديلات المطلوبة:"

    await update.message.reply_text(text)
    context.user_data["awaiting_photo_description"] = True
    context.user_data["photo_file_id"] = photo.file_id


# ===============================
# USER DESCRIPTION
# ===============================
async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    username = user.username or "NoUsername"
    user_id = user.id
    first_name = user.first_name or "No Name"

    lang = context.user_data.get("lang", "en")
    category = context.user_data.get("category")
    service_type = context.user_data.get("service_type", "unknown")
    service_name = context.user_data.get("service_name", "Unknown Service")

    # Handle photo description
    if context.user_data.get("awaiting_photo_description"):
        context.user_data["awaiting_photo_description"] = False
        description = update.message.text
        photo_file_id = context.user_data.get("photo_file_id")

        # Summary to user
        if lang == "en":
            text = "✅ Your photo and edit request have been received! We will contact you soon.\n\nIf you have any problem ask @Tammam19"
        else:
            text = "✅ تم استلام الصورة وطلب التعديل! سنتواصل معك قريباً.\n\nان واجهتك مشكلة اتصل ب @Tammam19"

        await update.message.reply_text(text)

        # ADMIN MESSAGE WITH PHOTO
        category_names = {
            "cat_prof": "Professional Services",
            "cat_design": "Design Services"
        }

        category_names_ar = {
            "cat_prof": "خدمات مهنية",
            "cat_design": "خدمات التصميم"
        }

        admin_category = category_names.get(category, "Unknown Category")
        if lang == "ar":
            admin_category = category_names_ar.get(category, "فئة غير معروفة")

        admin_message = (
            f"📥 *New Image Editing Request*\n\n"
            f"👤 *Client Info:*\n"
            f"   Name: {first_name}\n"
            f"   Username: @{username}\n"
            f"   ID: `{user_id}`\n\n"
            f"📦 *Service Details:*\n"
            f"   Category: {admin_category}\n"
            f"   Service: {service_name}\n"
            f"   Language: {'English' if lang == 'en' else 'Arabic'}\n\n"
            f"📝 *Edit Instructions:*\n{description}\n\n"
            f"⏰ _Received at: {update.message.date}_"
        )

        # Send photo first, then message with buttons
        await context.bot.send_photo(
            chat_id=ADMIN_ID,
            photo=photo_file_id,
            caption="🖼 **Photo to Edit**"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Accept", callback_data=f"admin_accept_{user_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{user_id}")
            ],
            [
                InlineKeyboardButton("📞 Contact Client", url=f"https://t.me/{username}") if username != "NoUsername" else InlineKeyboardButton("📞 Cannot Contact", callback_data="none")
            ]
        ]

        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return

    # Handle regular description
    if not context.user_data.get("awaiting_description"):
        return

    context.user_data["awaiting_description"] = False
    description = update.message.text

    # Summary to user
    if lang == "en":
        text = "✅ Your request has been received! We will contact you soon.\n\nIf you have any problem ask @Tammam19"
    else:
        text = "✅ تم استلام طلبك! سنتواصل معك قريباً.\n\nان واجهتك مشكلة اتصل ب @Tammam19"

    await update.message.reply_text(text)

    # ADMIN MESSAGE - REGULAR SERVICE
    category_names = {
        "cat_prof": "Professional Services",
        "cat_design": "Design Services"
    }

    category_names_ar = {
        "cat_prof": "خدمات مهنية",
        "cat_design": "خدمات التصميم"
    }

    admin_category = category_names.get(category, "Unknown Category")
    if lang == "ar":
        admin_category = category_names_ar.get(category, "فئة غير معروفة")

    admin_message = (
        f"📥 *New Service Request*\n\n"
        f"👤 *Client Info:*\n"
        f"   Name: {first_name}\n"
        f"   Username: @{username}\n"
        f"   ID: `{user_id}`\n\n"
        f"📦 *Service Details:*\n"
        f"   Category: {admin_category}\n"
        f"   Service: {service_name}\n"
        f"   Language: {'English' if lang == 'en' else 'Arabic'}\n\n"
        f"📝 *Project Description:*\n{description}\n\n"
        f"⏰ _Received at: {update.message.date}_"
    )

    keyboard = [
        [
            InlineKeyboardButton("✅ Accept", callback_data=f"admin_accept_{user_id}"),
            InlineKeyboardButton("❌ Reject", callback_data=f"admin_reject_{user_id}")
        ],
        [
            InlineKeyboardButton("📞 Contact Client", url=f"https://t.me/{username}") if username != "NoUsername" else InlineKeyboardButton("📞 Cannot Contact", callback_data="none")
        ]
    ]

    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_message,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===============================
# ADMIN ACCEPT/REJECT
# ===============================
async def admin_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, action, uid = query.data.split("_")
    uid = int(uid)

    if action == "accept":
        await context.bot.send_message(
            uid, 
            "🎉 Your request has been *ACCEPTED*! \n\nOur team will contact you soon to discuss the details.\n\nThank you for choosing our services! 💫"
        )
        await query.edit_message_text(
            "✅ Request accepted and client notified.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("📞 Contact Client", url=f"tg://user?id={uid}")
            ]])
        )
    else:
        await context.bot.send_message(
            uid, 
            "❌ Your request has been *REJECTED*. \n\nYou may submit a new request with more details.\n\nIf you have questions, contact @Tammam19"
        )
        await query.edit_message_text("❌ Request rejected and client notified.")


# ===============================
# MAIN
# ===============================
def main():
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()

    # Create Telegram bot application
    bot_app = Application.builder().token(TOKEN).build()

    # Add handlers
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CallbackQueryHandler(check_membership_callback, pattern="check_membership"))
    bot_app.add_handler(CallbackQueryHandler(language_handler, pattern="lang_"))
    bot_app.add_handler(CallbackQueryHandler(category_handler, pattern="cat_"))
    bot_app.add_handler(CallbackQueryHandler(service_type_handler, pattern="design_"))
    bot_app.add_handler(CallbackQueryHandler(service_type_handler, pattern="service_"))
    bot_app.add_handler(CallbackQueryHandler(admin_action_handler, pattern="admin_"))
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description))
    bot_app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    print("🤖 Service Bot is running on Replit...")
    bot_app.run_polling()


if __name__ == "__main__":
    main()
