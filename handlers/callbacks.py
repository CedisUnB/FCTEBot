from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menus import create_menu, create_cursos_menu

# Função para finalizar a conversa
async def end_conversation(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text="⏱️ A conversa foi encerrada por inatividade. Envie /start para começar novamente."
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())
    await reset_timer(update.effective_chat.id, context)

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    await reset_timer(update.effective_chat.id, context)

    if query.data == 'contexto':
        await query.edit_message_text("👋 Bem-vindo ao FCTE Bot!")
    elif query.data == 'cursos':
        await query.edit_message_text("📊 Escolha um Curso:", reply_markup=create_cursos_menu())
    elif query.data in ['curso_es', 'curso_eelet', 'curso_eaut', 'curso_eaero', 'curso_een']:
        await query.edit_message_text("👋 Bem-vindo ao FCTE Bot!")
    elif query.data == 'menu':
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())

# Reinicia o temporizador sempre que o usuário interage
async def reset_timer(chat_id, context):
    old_job = context.chat_data.get("end_conversation_job")
    if old_job:
        old_job.schedule_removal()

    new_job = context.job_queue.run_once(end_conversation, 30, chat_id=chat_id)
    context.chat_data["end_conversation_job"] = new_job
