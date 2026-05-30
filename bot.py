import os
import logging
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ConversationHandler, ContextTypes, filters
)

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── States ───────────────────────────────────────────────────────────────────
(
    CLIENT_NAME, CLIENT_PHONE, CLIENT_CITY,
    HOW_MANY_CHILDREN,
    CHILD_NAME, CHILD_AGE, CHILD_GENDER,
    CHILD_CHARACTER, CHILD_PROBLEM, CHILD_HERO,
    CHILD_PHOTOS, CHILD_MORE_PHOTOS,
    PARTICIPANT_ASK, PARTICIPANT_PHOTOS, PARTICIPANT_MORE_PHOTOS,
    EXTRA_NOTES, CONFIRM
) = range(17)

# ── Keyboards ────────────────────────────────────────────────────────────────
def kb_row(*items):
    return ReplyKeyboardMarkup([list(items)], resize_keyboard=True, one_time_keyboard=True)

CHARACTER_KB = ReplyKeyboardMarkup([
    ["Uyatchan", "Qo'rqoq"],
    ["Tez jahli chiqadi", "Yolg'onchi"],
    ["Dangasa", "O'jar"],
    ["Boshqa (o'zim yozaman)"]
], resize_keyboard=True, one_time_keyboard=True)

HERO_KB = ReplyKeyboardMarkup([
    ["Hayvon qahramoni", "Bola qahramoni"],
    ["Ertak qahramoni", "Superqahramon"],
    ["Boshqa (o'zim yozaman)"]
], resize_keyboard=True, one_time_keyboard=True)

GENDER_KB = kb_row("O'g'il", "Qiz")
YES_NO_KB  = kb_row("Ha", "Yo'q")

# ── /start ───────────────────────────────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data.clear()
    ctx.user_data["children"] = []
    await update.message.reply_text(
        "NASIHA — Mehr va Tarbiya Olami\n\n"
        "Assalomu alaykum!\n\n"
        "Bu yerda farzandingiz uchun shaxsiy hikoya kitob buyurtma bera olasiz.\n\n"
        "Forma to'ldirish taxminan 5-7 daqiqa oladi.\n"
        "To'xtatish uchun /bekor yozing.\n\n"
        "Boshlaylik!\n\n"
        "1-QADAM: SIZNING MA'LUMOTLARINGIZ\n\n"
        "Ism va familiyangizni yozing:\n"
        "Masalan: Nilufar Raximova",
        reply_markup=ReplyKeyboardRemove()
    )
    return CLIENT_NAME

# ── Client info ───────────────────────────────────────────────────────────────
async def client_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["client_name"] = update.message.text.strip()
    await update.message.reply_text(
        "Telefon raqamingizni yozing:\n"
        "Masalan: +998 90 123 45 67"
    )
    return CLIENT_PHONE

async def client_phone(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["client_phone"] = update.message.text.strip()
    await update.message.reply_text(
        "Shahringiz yoki manzilingizni yozing:\n"
        "Masalan: Toshkent, Chilonzor tumani"
    )
    return CLIENT_CITY

async def client_city(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["client_city"] = update.message.text.strip()
    await update.message.reply_text(
        "Nechta bola uchun kitob buyurtma berasiz?\n\n"
        "Raqam yozing: 1, 2, 3..."
    )
    return HOW_MANY_CHILDREN

async def how_many_children(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    if not text.isdigit() or not (1 <= int(text) <= 10):
        await update.message.reply_text("Iltimos, 1 dan 10 gacha raqam yozing.")
        return HOW_MANY_CHILDREN
    ctx.user_data["total_children"] = int(text)
    ctx.user_data["current_child"] = 1
    return await ask_child_name(update, ctx)

# ── Per-child ─────────────────────────────────────────────────────────────────
async def ask_child_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    n     = ctx.user_data["current_child"]
    total = ctx.user_data["total_children"]
    await update.message.reply_text(
        f"{n}-BOLA MA'LUMOTLARI ({n}/{total})\n\n"
        "Bolaning ismini yozing:\n"
        "Masalan: Amir",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_NAME

async def child_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"] = {
        "name": update.message.text.strip(),
        "photos": [],
        "participant_photos": []
    }
    await update.message.reply_text(
        "Yoshini yozing:\nMasalan: 7"
    )
    return CHILD_AGE

async def child_age(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"]["age"] = update.message.text.strip()
    await update.message.reply_text("Jinsi?", reply_markup=GENDER_KB)
    return CHILD_GENDER

async def child_gender(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"]["gender"] = update.message.text.strip()
    name = ctx.user_data["current_child_data"]["name"]
    await update.message.reply_text(
        f"{name}ning asosiy xususiyati qaysi?\n\n"
        "Eng ko'p sezadigan muammo yoki xarakter belgisini tanlang:",
        reply_markup=CHARACTER_KB
    )
    return CHILD_CHARACTER

async def child_character(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"]["character"] = update.message.text.strip()
    name = ctx.user_data["current_child_data"]["name"]
    await update.message.reply_text(
        f"{name} haqida ko'proq gapirib bering:\n\n"
        "Bu xususiyat qanday namoyon bo'ladi? Qachon ko'proq sezasiz?\n\n"
        "Masalan: Mehmonlar kelganda yashirinib oladi, yangi bolalar bilan gaplasha olmaydi",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_PROBLEM

async def child_problem(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"]["problem"] = update.message.text.strip()
    name = ctx.user_data["current_child_data"]["name"]
    await update.message.reply_text(
        f"Hikoya qahramoni kim bo'lsin?\n\n"
        f"{name} qanday qahramonlarni yaxshi ko'radi?",
        reply_markup=HERO_KB
    )
    return CHILD_HERO

async def child_hero(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["current_child_data"]["hero"] = update.message.text.strip()
    name = ctx.user_data["current_child_data"]["name"]
    await update.message.reply_text(
        f"RASMLAR — {name}\n\n"
        "Iltimos, imkon qadar:\n\n"
        "- Turli kiyimdagi\n"
        "- Turli holatdagi\n"
        "- Sifatli\n"
        "- Yuzlari aniq ko'rinadigan\n\n"
        "rasmlarni yuboring.\n\n"
        "Kamida 3-4 ta rasm tavsiya etiladi.\n"
        "Bu hikoya qahramonini yanada o'xshash yaratishga yordam beradi.\n\n"
        "Rasmlarni yuboring:",
        reply_markup=ReplyKeyboardRemove()
    )
    return CHILD_PHOTOS

async def child_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    photos = ctx.user_data["current_child_data"]["photos"]

    if update.message.photo:
        photos.append({"type": "photo", "file_id": update.message.photo[-1].file_id})
    elif update.message.document and update.message.document.mime_type and \
         update.message.document.mime_type.startswith("image/"):
        photos.append({"type": "document", "file_id": update.message.document.file_id})
    else:
        await update.message.reply_text("Iltimos, rasm yuboring (JPG yoki PNG).")
        return CHILD_PHOTOS

    count = len(photos)
    if count < 3:
        await update.message.reply_text(
            f"{count} ta rasm qabul qilindi.\n\n"
            f"Yana kamida {3 - count} ta rasm yuboring."
        )
        return CHILD_PHOTOS
    else:
        await update.message.reply_text(
            f"{count} ta rasm qabul qilindi!\n\nYana rasm qo'shmoqchimisiz?",
            reply_markup=YES_NO_KB
        )
        return CHILD_MORE_PHOTOS

async def child_more_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "Ha" in update.message.text:
        await update.message.reply_text("Rasmlarni yuboring:", reply_markup=ReplyKeyboardRemove())
        return CHILD_PHOTOS
    count = len(ctx.user_data["current_child_data"]["photos"])
    await update.message.reply_text(
        f"Jami {count} ta rasm saqlandi!\n\n"
        "Hikoyada boshqa ishtirokchilar bormi?\n"
        "(Ota, ona, buvi, do'st va boshqalar)\n\n"
        "Ularning rasmlarini ham yuborishingiz mumkin.",
        reply_markup=YES_NO_KB
    )
    return PARTICIPANT_ASK

async def participant_ask(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "Ha" in update.message.text:
        await update.message.reply_text(
            "Ishtirokchilar rasmlarini yuboring:",
            reply_markup=ReplyKeyboardRemove()
        )
        return PARTICIPANT_PHOTOS
    return await finish_child(update, ctx)

async def participant_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    p_photos = ctx.user_data["current_child_data"]["participant_photos"]

    if update.message.photo:
        p_photos.append({"type": "photo", "file_id": update.message.photo[-1].file_id})
    elif update.message.document and update.message.document.mime_type and \
         update.message.document.mime_type.startswith("image/"):
        p_photos.append({"type": "document", "file_id": update.message.document.file_id})
    else:
        await update.message.reply_text("Iltimos, rasm yuboring.")
        return PARTICIPANT_PHOTOS

    count = len(p_photos)
    await update.message.reply_text(
        f"{count} ta ishtirokchi rasmi qabul qilindi.\nYana qo'shmoqchimisiz?",
        reply_markup=YES_NO_KB
    )
    return PARTICIPANT_MORE_PHOTOS

async def participant_more_photos(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "Ha" in update.message.text:
        await update.message.reply_text("Rasmlarni yuboring:", reply_markup=ReplyKeyboardRemove())
        return PARTICIPANT_PHOTOS
    return await finish_child(update, ctx)

async def finish_child(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    child_data = ctx.user_data.pop("current_child_data")
    ctx.user_data["children"].append(child_data)

    current = ctx.user_data["current_child"]
    total   = ctx.user_data["total_children"]

    if current < total:
        ctx.user_data["current_child"] += 1
        await update.message.reply_text(
            f"{child_data['name']} uchun ma'lumotlar saqlandi!\n\nKeyingi bolaga o'tamiz...",
            reply_markup=ReplyKeyboardRemove()
        )
        return await ask_child_name(update, ctx)
    else:
        await update.message.reply_text(
            "QO'SHIMCHA IZOH\n\n"
            "Maxsus xohish yoki e'tibor qaratish kerak bo'lgan narsa bormi?\n\n"
            "Masalan: Bolam yashil rangni yaxshi ko'radi, tug'ilgan kuni 15-iyun...\n\n"
            "Yo'q bo'lsa — Yo'q deb yozing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return EXTRA_NOTES

# ── Summary & confirm ─────────────────────────────────────────────────────────
async def extra_notes(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["extra_notes"] = update.message.text.strip()
    data = ctx.user_data

    lines = ["BUYURTMA XULOSASI\n"]
    lines.append(f"Mijoz: {data['client_name']}")
    lines.append(f"Tel: {data['client_phone']}")
    lines.append(f"Manzil: {data['client_city']}\n")

    for i, child in enumerate(data["children"], 1):
        gender_icon = "O'g'il" if "g'il" in child["gender"] else "Qiz"
        lines.append(f"{i}-bola: {child['name']}")
        lines.append(f"  Yoshi: {child['age']}")
        lines.append(f"  Jinsi: {gender_icon}")
        lines.append(f"  Xarakteri: {child['character']}")
        lines.append(f"  Rasmlar: {len(child['photos'])} ta\n")

    if data["extra_notes"].lower() not in ("yo'q", "yoq", "no", "-"):
        lines.append(f"Izoh: {data['extra_notes']}\n")

    lines.append("Ma'lumotlar to'g'rimi? Tasdiqlaysizmi?")

    await update.message.reply_text("\n".join(lines), reply_markup=YES_NO_KB)
    return CONFIRM

async def confirm(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if "Yo'q" in update.message.text or "Yoq" in update.message.text:
        await update.message.reply_text(
            "Qaytadan boshlash uchun /start bosing.",
            reply_markup=ReplyKeyboardRemove()
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "Ma'lumotlar saqlanmoqda... Biroz kuting.",
        reply_markup=ReplyKeyboardRemove()
    )

    try:
        from google_drive import GoogleDriveManager
        from doc_generator import generate_doc

        drive = GoogleDriveManager()
        data  = ctx.user_data
        bot   = ctx.application.bot

        date_str    = datetime.now().strftime("%Y-%m-%d")
        folder_name = f"{data['client_name']} - {data['client_city']} - {date_str}"
        main_folder_id = drive.create_folder(folder_name)

        doc_path = generate_doc(data)
        drive.upload_file(doc_path, f"Buyurtma_{data['client_name']}.docx", main_folder_id)

        photos_folder_id = drive.create_folder("Child_Photos", main_folder_id)
        for i, child in enumerate(data["children"], 1):
            child_folder_id = drive.create_folder(f"{i}-BOLA-{child['name']}", photos_folder_id)
            for j, p in enumerate(child["photos"], 1):
                tg_file  = await bot.get_file(p["file_id"])
                ext      = "jpg" if p["type"] == "photo" else tg_file.file_path.split(".")[-1]
                tmp_path = f"/tmp/{child['name']}_{j}.{ext}"
                await tg_file.download_to_drive(tmp_path)
                drive.upload_file(tmp_path, f"rasm_{j}.{ext}", child_folder_id)

            if child["participant_photos"]:
                part_id = drive.create_folder("Ishtirokchilar", child_folder_id)
                for j, p in enumerate(child["participant_photos"], 1):
                    tg_file  = await bot.get_file(p["file_id"])
                    ext      = "jpg" if p["type"] == "photo" else tg_file.file_path.split(".")[-1]
                    tmp_path = f"/tmp/participant_{j}.{ext}"
                    await tg_file.download_to_drive(tmp_path)
                    drive.upload_file(tmp_path, f"ishtirokchi_{j}.{ext}", part_id)

        await update.message.reply_text(
            "Buyurtmangiz qabul qilindi!\n\n"
            "Barcha ma'lumotlar saqlandi\n"
            "Rasmlar yuklandi\n"
            "Hujjat tayyorlandi\n\n"
            f"Papka nomi: {folder_name}\n\n"
            "Tez orada siz bilan bog'lanamiz!\n\n"
            "Nasiha - Mehr va Tarbiya Olami"
        )
    except Exception as e:
        logger.error(f"Buyurtmani saqlashda xato: {e}", exc_info=True)
        await update.message.reply_text(
            "Texnik xato yuz berdi. Iltimos, @nasiha_support ga yozing."
        )

    return ConversationHandler.END

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Forma bekor qilindi.\nQayta boshlash uchun /start bosing.",
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    token = os.environ.get("BOT_TOKEN")
    if not token:
        raise ValueError("BOT_TOKEN muhit o'zgaruvchisi yo'q!")

    app = Application.builder().token(token).build()

    conv = ConversationHandler(
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
            CHILD_PHOTOS:            [MessageHandler(filters.PHOTO | filters.Document.IMAGE, child_photos)],
            CHILD_MORE_PHOTOS:       [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, child_photos),
                MessageHandler(filters.TEXT & ~filters.COMMAND, child_more_photos),
            ],
            PARTICIPANT_ASK:         [MessageHandler(filters.TEXT & ~filters.COMMAND, participant_ask)],
            PARTICIPANT_PHOTOS:      [MessageHandler(filters.PHOTO | filters.Document.IMAGE, participant_photos)],
            PARTICIPANT_MORE_PHOTOS: [
                MessageHandler(filters.PHOTO | filters.Document.IMAGE, participant_photos),
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
    )

    app.add_handler(conv)
    logger.info("Nasiha bot ishga tushdi...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
