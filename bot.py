import os
import logging
import sys
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)
from google_drive import GoogleDriveManager
from doc_generator import generate_doc

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ── Conversation states ──────────────────────────────────────────────────────
(
    CLIENT_NAME, CLIENT_PHONE, CLIENT_CITY,
    HOW_MANY_CHILDREN,
    CHILD_NAME, CHILD_AGE, CHILD_GENDER,
    CHILD_CHARACTER, CHILD_PROBLEM, CHILD_HERO,
    CHILD_PHOTOS, CHILD_MORE_PHOTOS,
    PARTICIPANT_PHOTOS, PARTICIPANT_MORE_PHOTOS,
    EXTRA_NOTES,
    CONFIRM
) = range(16)

# ── Keyboards ────────────────────────────────────────────────────────────────
def kb_col(*rows):
    """Vertical keyboard — each item on its own row."""
    return ReplyKeyboardMarkup([[r] for r in rows], resize_keyboard=True, one_time_keyboard=True)

def kb_row(*items):
    """Horizontal keyboard — all items on one row."""
    return ReplyKeyboardMarkup([list(items)], resize_keyboard=True, one_time_keyboard=True)

CHARACTER_KB = ReplyKeyboardMarkup([
    ["😟 Uyatchan", "😨 Qo'rqoq"],
    ["😤 Tez jahli chiqadi", "🤥 Yolg'onchi"],
    ["😴 Dangasa", "😤 O'jar"],
    ["🙋 Boshqa (yozaman)"]
], resize_keyboard=True, one_time_keyboard=True)

HERO_KB = ReplyKeyboardMarkup([
    ["🐾 Hayvon qahramoni", "👦 Bola qahramoni"],
    ["🧚 Ertak qahramoni", "🦸 Superqahramon"],
    ["✍️ Boshqa (yozaman)"]
], resize_keyboard=True, one_time_keyboard=True)

GENDER_KB  = kb_row("👦 O'g'il", "👧 Qiz")
YES_NO_KB  = kb_row("✅ Ha", "❌ Yo'q")


# ── Helpers ──────────────────────────────────────────────────────────────────
def safe_text(update: Update) -> str:
    """Return message text safely (empty string if no text)."""
    return update.message.text.strip() if update.message.text else ""


def gender_icon(gender_str: str) -> str:
    return "👦" if "O'g'il" in gender_str else "👧"


# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data['children'] = []
    await update.message.reply_text(
        "✨ *NASIHA — Mehr va Tarbiya Olami*\n\n"
        "Assalomu alaykum! 👋\n\n"
        "Bu yerda farzandingiz uchun *shaxsiy hikoya kitob* buyurtma bera olasiz.\n\n"
        "Forma to'ldirish taxminan *5–7 daqiqa* oladi.\n"
        "Istalgan vaqtda /bekor yozib to'xtatishingiz mumkin.\n\n"
        "Boshlaylik! 🚀\n\n"
        "━━━━━━━━━━━━━━━\n"
        "👤 *1-QADAM: SIZNING MA'LUMOTLARINGIZ*\n\n"
        "Ism va familiyangizni yozing:\n"
        "_(Masalan: Nilufar Raximova)_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return CLIENT_NAME


# ── Client info ──────────────────────────────────────────────────────────────
async def client_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['client_name'] = safe_text(update)
    await update.message.reply_text(
        "📱 Telefon raqamingizni yozing:\n"
        "_(Masalan: +998 90 123 45 67)_",
        parse_mode='Markdown'
    )
    return CLIENT_PHONE


async def client_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['client_phone'] = safe_text(update)
    await update.message.reply_text(
        "🏙 Shahringiz yoki manzilingizni yozing:\n"
        "_(Masalan: Toshkent, Chilonzor tumani)_",
        parse_mode='Markdown'
    )
    return CLIENT_CITY


async def client_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['client_city'] = safe_text(update)
    await update.message.reply_text(
        "━━━━━━━━━━━━━━━\n"
        "👨‍👩‍👧‍👦 *Nechta bola uchun kitob buyurtma berasiz?*\n\n"
        "Raqam yozing: _(1, 2, 3...)_",
        parse_mode='Markdown'
    )
    return HOW_MANY_CHILDREN


async def how_many_children(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = safe_text(update)
    if not text.isdigit() or not (1 <= int(text) <= 10):
        await update.message.reply_text("⚠️ Iltimos, 1 dan 10 gacha raqam yozing.")
        return HOW_MANY_CHILDREN
    ctx.user_data['total_children'] = int(text)
    ctx.user_data['current_child'] = 1
    return await ask_child_name(update, ctx)


# ── Per-child questions ──────────────────────────────────────────────────────
async def ask_child_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n     = ctx.user_data['current_child']
    total = ctx.user_data['total_children']
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━\n"
        f"👶 *{n}-BOLA MA'LUMOTLARI* ({n}/{total})\n\n"
        f"Bolaning ismini yozing:\n"
        f"_(Masalan: Amir)_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_NAME


async def child_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data'] = {
        'name': safe_text(update),
        'photos': [],
        'participant_photos': []
    }
    await update.message.reply_text(
        "🎂 Yoshini yozing:\n_(Masalan: 7)_",
        parse_mode='Markdown'
    )
    return CHILD_AGE


async def child_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data']['age'] = safe_text(update)
    await update.message.reply_text(
        "👦👧 Jinsi?",
        reply_markup=GENDER_KB
    )
    return CHILD_GENDER


async def child_gender(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data']['gender'] = safe_text(update)
    name = ctx.user_data['current_child_data']['name']
    await update.message.reply_text(
        f"🧠 *{name}ning asosiy xususiyati qaysi?*\n\n"
        f"Eng ko'p sezadigan muammo yoki xarakter belgisini tanlang:",
        parse_mode='Markdown',
        reply_markup=CHARACTER_KB
    )
    return CHILD_CHARACTER


async def child_character(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data']['character'] = safe_text(update)
    name = ctx.user_data['current_child_data']['name']
    await update.message.reply_text(
        f"💬 *{name} haqida ko'proq gapirib bering:*\n\n"
        f"Bu xususiyat qanday namoyon bo'ladi? Qachon ko'proq sezasiz?\n\n"
        f"_(Masalan: Mehmonlar kelganda yashirinib oladi, yangi bolalar bilan gaplasha olmaydi)_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_PROBLEM


async def child_problem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data']['problem'] = safe_text(update)
    name = ctx.user_data['current_child_data']['name']
    await update.message.reply_text(
        f"🦸 *Hikoya qahramoni kim bo'lsin?*\n\n"
        f"_{name} qanday qahramonlarni yaxshi ko'radi?_",
        parse_mode='Markdown',
        reply_markup=HERO_KB
    )
    return CHILD_HERO


async def child_hero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['current_child_data']['hero'] = safe_text(update)
    name = ctx.user_data['current_child_data']['name']
    await update.message.reply_text(
        f"━━━━━━━━━━━━━━━\n"
        f"📸 *{name}ning rasmlarini yuboring*\n\n"
        f"Iltimos, imkon qadar:\n\n"
        f"• 👕 Turli kiyimdagi\n"
        f"• 🏃 Turli holatdagi\n"
        f"• 📷 Sifatli\n"
        f"• 😊 Yuzlari aniq ko'rinadigan\n\n"
        f"rasmlarni yuboring ✨\n\n"
        f"Har bir bola uchun kamida *3–4 ta rasm* yuborilishi tavsiya etiladi.\n\n"
        f"Bu hikoya qahramonlarini yanada o'xshash va chiroyli yaratishga yordam beradi 💛\n\n"
        f"_(Bir vaqtda bir nechta rasm yuborishingiz mumkin)_",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_PHOTOS


# ── Photo handlers ───────────────────────────────────────────────────────────
def _extract_file(update: Update) -> dict | None:
    """Extract file_id and type from a message. Returns None if not an image."""
    if update.message.photo:
        return {'type': 'photo', 'file_id': update.message.photo[-1].file_id}
    if (update.message.document
            and update.message.document.mime_type
            and update.message.document.mime_type.startswith('image/')):
        return {'type': 'document', 'file_id': update.message.document.file_id}
    return None


async def child_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    file_info = _extract_file(update)
    if not file_info:
        await update.message.reply_text("⚠️ Iltimos, rasm yuboring (JPG, PNG, HEIC).")
        return CHILD_PHOTOS

    photos = ctx.user_data['current_child_data']['photos']
    photos.append(file_info)
    count = len(photos)

    if count < 3:
        await update.message.reply_text(
            f"✅ *{count} ta rasm qabul qilindi.*\n\n"
            f"Yana kamida *{3 - count} ta* rasm yuboring 📸",
            parse_mode='Markdown'
        )
        return CHILD_PHOTOS
    else:
        await update.message.reply_text(
            f"✅ *{count} ta rasm qabul qilindi!*\n\n"
            f"Yana rasm qo'shmoqchimisiz?",
            parse_mode='Markdown',
            reply_markup=YES_NO_KB
        )
        return CHILD_MORE_PHOTOS


async def child_more_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = safe_text(update)
    if "Ha" in text:
        await update.message.reply_text(
            "📸 Davom eting, rasmlarni yuboring:",
            reply_markup=ReplyKeyboardRemove()
        )
        return CHILD_PHOTOS

    count = len(ctx.user_data['current_child_data']['photos'])
    await update.message.reply_text(
        f"👍 Jami *{count} ta rasm* saqlandi!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"👨‍👩‍👧 *Hikoyada boshqa ishtirokchilar bormi?*\n\n"
        f"_(Ota, ona, buvi, do'st va boshqalar)_\n\n"
        f"Ularning rasmlarini ham yuborishingiz mumkin ✨",
        parse_mode='Markdown',
        reply_markup=YES_NO_KB
    )
    return PARTICIPANT_PHOTOS


async def participant_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = safe_text(update)

    # User said NO — skip participant photos
    if "Yo'q" in text:
        return await next_child_or_continue(update, ctx)

    file_info = _extract_file(update)
    if not file_info:
        # Could be "Ha" reply or unknown message — ask them to send photo
        await update.message.reply_text(
            "📸 Ishtirokchilar rasmlarini yuboring yoki '❌ Yo'q' tugmasini bosing:",
            reply_markup=YES_NO_KB
        )
        return PARTICIPANT_PHOTOS

    p_photos = ctx.user_data['current_child_data']['participant_photos']
    p_photos.append(file_info)
    count = len(p_photos)
    await update.message.reply_text(
        f"✅ *{count} ta ishtirokchi rasmi qabul qilindi.*\n\nYana qo'shmoqchimisiz?",
        parse_mode='Markdown',
        reply_markup=YES_NO_KB
    )
    return PARTICIPANT_MORE_PHOTOS


async def participant_more_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    # Could be a photo sent directly
    file_info = _extract_file(update)
    if file_info:
        p_photos = ctx.user_data['current_child_data']['participant_photos']
        p_photos.append(file_info)
        count = len(p_photos)
        await update.message.reply_text(
            f"✅ *{count} ta ishtirokchi rasmi qabul qilindi.*\n\nYana qo'shmoqchimisiz?",
            parse_mode='Markdown',
            reply_markup=YES_NO_KB
        )
        return PARTICIPANT_MORE_PHOTOS

    text = safe_text(update)
    if "Ha" in text:
        await update.message.reply_text("📸 Davom eting:", reply_markup=ReplyKeyboardRemove())
        return PARTICIPANT_PHOTOS

    return await next_child_or_continue(update, ctx)


# ── Child loop ───────────────────────────────────────────────────────────────
async def next_child_or_continue(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    child_data = ctx.user_data.pop('current_child_data')
    ctx.user_data['children'].append(child_data)

    current = ctx.user_data['current_child']
    total   = ctx.user_data['total_children']

    if current < total:
        ctx.user_data['current_child'] += 1
        await update.message.reply_text(
            f"✅ *{child_data['name']} uchun ma'lumotlar saqlandi!*\n\n"
            f"Keyingi bolaga o'tamiz... 👶",
            parse_mode='Markdown',
            reply_markup=ReplyKeyboardRemove()
        )
        return await ask_child_name(update, ctx)

    await update.message.reply_text(
        "━━━━━━━━━━━━━━━\n"
        "📝 *QO'SHIMCHA IZOH*\n\n"
        "Bizga bildirishni xohlagan biror maxsus xohish yoki e'tibor qaratish kerak bo'lgan narsa bormi?\n\n"
        "_(Masalan: Bolam qo'g'irchoqlarni yaxshi ko'radi, yashil rangni yaxshi ko'radi, "
        "tug'ilgan kuni 15-iyun...)_\n\n"
        "Yo'q bo'lsa — *Yo'q* yozing.",
        parse_mode='Markdown',
        reply_markup=ReplyKeyboardRemove()
    )
    return EXTRA_NOTES


# ── Extra notes & confirm ────────────────────────────────────────────────────
async def extra_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data['extra_notes'] = safe_text(update)
    data = ctx.user_data

    lines = [
        "📋 *BUYURTMA XULOSASI*\n",
        f"👤 Mijoz: *{data['client_name']}*",
        f"📱 Tel: {data['client_phone']}",
        f"🏙 Manzil: {data['client_city']}\n",
    ]

    for i, child in enumerate(data['children'], 1):
        icon = gender_icon(child.get('gender', ''))
        lines.append(f"👶 *{i}-bola: {child['name']}*")
        lines.append(f"   🎂 Yoshi: {child['age']}")
        lines.append(f"   {icon} Jinsi: {child['gender']}")
        lines.append(f"   🧠 Xarakteri: {child['character']}")
        lines.append(f"   📸 Rasmlar: {len(child['photos'])} ta\n")

    if data['extra_notes'].lower() not in ("yo'q", "yoq", ""):
        lines.append(f"📝 Izoh: {data['extra_notes']}\n")

    lines.append("━━━━━━━━━━━━━━━")
    lines.append("✅ Ma'lumotlar to'g'rimi? Tasdiqlaysizmi?")

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode='Markdown',
        reply_markup=YES_NO_KB
    )
    return CONFIRM


async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = safe_text(update)

    if "Yo'q" in text:
        await update.message.reply_text(
            "🔄 Qaytadan boshlash uchun /start bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "⏳ Ma'lumotlar saqlanmoqda... Biroz kuting.",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        drive   = GoogleDriveManager()
        data    = ctx.user_data
        bot     = ctx.application.bot

        date_str    = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"{data['client_name']} — {data['client_city']} — {date_str}"
        main_folder_id = drive.create_folder(folder_name)

        # Generate and upload Word doc
        doc_path = generate_doc(data)
        drive.upload_file(doc_path, f"Buyurtma_{data['client_name']}.docx", main_folder_id)

        # Upload child photos
        photos_folder_id = drive.create_folder("Rasmlar", main_folder_id)
        for i, child in enumerate(data['children'], 1):
            child_folder_id = drive.create_folder(
                f"{i}-BOLA_{child['name']}", photos_folder_id
            )

            for j, p in enumerate(child['photos'], 1):
                tg_file  = await bot.get_file(p['file_id'])
                ext      = 'jpg' if p['type'] == 'photo' else tg_file.file_path.split('.')[-1]
                tmp_path = f"/tmp/{child['name']}_{j}.{ext}"
                await tg_file.download_to_drive(tmp_path)
                drive.upload_file(tmp_path, f"rasm_{j}.{ext}", child_folder_id)
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

            if child['participant_photos']:
                part_folder_id = drive.create_folder("Ishtirokchilar", child_folder_id)
                for j, p in enumerate(child['participant_photos'], 1):
                    tg_file  = await bot.get_file(p['file_id'])
                    ext      = 'jpg' if p['type'] == 'photo' else tg_file.file_path.split('.')[-1]
                    tmp_path = f"/tmp/participant_{child['name']}_{j}.{ext}"
                    await tg_file.download_to_drive(tmp_path)
                    drive.upload_file(tmp_path, f"ishtirokchi_{j}.{ext}", part_folder_id)
                    try:
                        os.remove(tmp_path)
                    except OSError:
                        pass

        folder_link = drive.get_shareable_link(main_folder_id)
        await update.message.reply_text(
            "🎉 *Buyurtmangiz qabul qilindi!*\n\n"
            "✅ Barcha ma'lumotlar saqlandi\n"
            "✅ Rasmlar yuklandi\n"
            "✅ Hujjat tayyorlandi\n\n"
            f"📁 Papka: `{folder_name}`\n"
            f"🔗 [Drive papkasini ko'rish]({folder_link})\n\n"
            "Tez orada siz bilan bog'lanamiz! 💛\n\n"
            "_Nasiha — Mehr va Tarbiya Olami_",
            parse_mode='Markdown'
        )

    except Exception as e:
        logger.error(f"Error saving order: {e}", exc_info=True)
        await update.message.reply_text(
            "⚠️ Texnik xato yuz berdi. Iltimos, @nasiha_support ga yozing."
        )

    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❌ Forma bekor qilindi.\n\nQayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN environment variable is not set! Exiting.")
        sys.exit(1)   # <-- exit gracefully, no crash loop

    app = Application.builder().token(token).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CLIENT_NAME:             [MessageHandler(filters.TEXT & ~filters.COMMAND, client_name)],
            CLIENT_PHONE:            [MessageHandler(filters.TEXT & ~filters.COMMAND, client_phone)],
            CLIENT_CITY:             [MessageHandler(filters.TEXT & ~filters.COMMAND, client_city)],
            HOW_MANY_CHILDREN:       [MessageHandler(filters.TEXT & ~filters.COMMAND, how_many_children)],
            CHILD_NAME:              [MessageHandler(filters.TEXT & ~filters.COMMAND, child_name)],
            CHILD_AGE:               [MessageHandler(filters.TEXT & ~filters.COMMAND, child_age)],
            CHILD_GENDER:            [MessageHandler(filters.TEXT & ~filters.COMMAND, child_gender)],
            CHILD_CHARACTER:         [MessageHandler(filters.TEXT & ~filters.COMMAND, child_character)],
            CHILD_PROBLEM:           [MessageHandler(filters.TEXT & ~filters.COMMAND, child_problem)],
            CHILD_HERO:              [MessageHandler(filters.TEXT & ~filters.COMMAND, child_hero)],
            CHILD_PHOTOS:            [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, child_photos),
            ],
            CHILD_MORE_PHOTOS:       [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, child_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_more_photos),
            ],
            PARTICIPANT_PHOTOS:      [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, participant_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, participant_photos),
            ],
            PARTICIPANT_MORE_PHOTOS: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, participant_more_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, participant_more_photos),
            ],
            EXTRA_NOTES:             [MessageHandler(filters.TEXT & ~filters.COMMAND, extra_notes)],
            CONFIRM:                 [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm)],
        },
        fallbacks=[
            CommandHandler("bekor", cancel),
            CommandHandler("cancel", cancel),
        ],
        allow_reentry=True,
        conversation_timeout=3600,   # 1 soat faoliyatsizlikda avtomatik yopiladi
    )

    app.add_handler(conv_handler)
    logger.info("✅ Nasiha bot started successfully.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
