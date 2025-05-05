import os
from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.callbacks import start, button
from utils.logger import setup_logging

# Carrega variáveis do arquivo .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN não encontrado no .env")

    setup_logging()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
