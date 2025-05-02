import logging
import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Carrega variáveis do arquivo .env
load_dotenv()
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

def create_menu():
    keyboard = [
        [
            InlineKeyboardButton("📰 Novidades", callback_data='opcao1'),
            InlineKeyboardButton("🆘 Ajuda", callback_data='opcao2')
        ],
        [
            InlineKeyboardButton("⚙️ Configurações", callback_data='opcao3'),
            InlineKeyboardButton("🔄 Mostrar Menu", callback_data='menu')
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = "Olá! Escolha uma das opções abaixo:"
    context.job_queue.run_once(timeout_reached, 30, data=update)
    await update.message.reply_text(welcome_message, reply_markup=create_menu())

async def timeout_reached(context: ContextTypes.DEFAULT_TYPE) -> None:
    update = context.job.data
    await update.message.reply_text("⏳ O tempo expirou! Digite /start para reiniciar o menu.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if 'timer' in context.user_data:
        context.user_data['timer'].cancel()
        del context.user_data['timer']

    if query.data == 'opcao1':
        await query.edit_message_text("📰 Aqui estão as últimas novidades!")
    elif query.data == 'opcao2':
        await query.edit_message_text("🆘 Como posso te ajudar? Envie uma dúvida!")
    elif query.data == 'opcao3':
        await query.edit_message_text("⚙️ Aqui você poderá configurar suas preferências futuramente.")
    elif query.data == 'menu':
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())

def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN não encontrado no .env")
    
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.run_polling()

if __name__ == "__main__":
    main()
