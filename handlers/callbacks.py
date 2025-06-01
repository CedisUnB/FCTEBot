from telegram import Update
from telegram.ext import ContextTypes
from handlers.menus import create_menu, create_cursos_menu

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = "Olá! Escolha uma das opções abaixo:"
    await update.message.reply_text(welcome_message, reply_markup=create_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'contexto':
        await query.edit_message_text("👋 Bem-vindo ao FCTE Bot!")
    elif query.data == 'cursos':
        await query.edit_message_text("📊 Escolha um Curso:", reply_markup=create_cursos_menu())
    elif query.data in ['curso_es', 'curso_eelet', 'curso_eaut', 'curso_eaero', 'curso_een']:
        await query.edit_message_text("👋 Bem-vindo ao FCTE Bot!")
    elif query.data == 'menu':
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())
