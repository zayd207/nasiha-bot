# ── Main ─────────────────────────────────────────────────────────────────────
async def main():
    token = os.environ.get("BOT_TOKEN") or os.environ.get("TOKEN")
    if not token:
        logger.critical("BOT_TOKEN environment variable is not set! Exiting.")
        sys.exit(1)

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
            CHILD_PHOTOS:            [MessageHandler(filters.PHOTO | filters.Document.IMAGE, child_photos)],
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
        conversation_timeout=3600,
    )

    app.add_handler(conv_handler)
    logger.info("✅ Nasiha bot started successfully.")

    await app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
