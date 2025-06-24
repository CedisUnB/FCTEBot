# handlers/perguntas.py

import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from rag import responder
from handlers.callbacks import reset_timer
from utils.db_helper import save_feedback
from handlers.menus import create_menu 

logger = logging.getLogger(__name__)

async def responder_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    if context.chat_data.get('awaiting_suggestion_after_feedback'):
        logger.info(f"Recebida sugestão de {chat_id}: {user_input}")

        awaiting_suggestion_job = context.chat_data.pop("await_suggestion_job", None)
        if awaiting_suggestion_job:
            awaiting_suggestion_job.schedule_removal()
            logger.debug(f"Job de timeout de sugestão para {chat_id} cancelado.")

        save_feedback(chat_id, False, user_input) # Salva "Não Ajudou" com a sugestão
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)
        
        await update.message.reply_text(
            "Obrigado pela sua sugestão! 👍 Ela foi registrada e é muito importante para mim.\n"
            "Para iniciar uma nova conversa, digite /start"
        )

        context.chat_data.clear()
        context.user_data.clear()

        ask_feedback_job = context.chat_data.pop("ask_feedback_job", None)
        if ask_feedback_job: ask_feedback_job.schedule_removal()
        end_conversation_job = context.chat_data.pop("end_conversation_job", None)
        if end_conversation_job: end_conversation_job.schedule_removal()
        return

    await reset_timer(chat_id, context)

    curso = context.chat_data.get("curso")
    contexto_geral = context.chat_data.get("contexto")

    if not curso and not contexto_geral:
        await update.message.reply_text(
            "❗ Antes de fazer uma pergunta, por favor selecione um curso ou o contexto de engenharias:", # adicionar as opções de curso ou contexto geral Add commentMore actions
            reply_markup=create_menu()
        )
        return

    prefixo = f"No contexto de {curso}" if curso else "No contexto geral da FGA UnB"
    pergunta_com_contexto = f"{prefixo}: {user_input}"
    await update.message.reply_text("🔎 Buscando a resposta para sua pergunta, só um instante...")
    await update.message.reply_chat_action(action=ChatAction.TYPING)
    resposta = responder(pergunta_com_contexto)

    try:
        resposta = await asyncio.to_thread(responder, pergunta_com_contexto)
        await update.message.reply_text(f"💬 {resposta}", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Erro ao processar pergunta do usuário '{user_input}': {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Desculpe, ocorreu um erro ao buscar sua resposta. Por favor, tente novamente mais tarde."
        )