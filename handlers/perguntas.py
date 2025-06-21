# handlers/perguntas.py

import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction # IMPORTAR
from rag import responder
from handlers.callbacks import reset_timer

logger = logging.getLogger(__name__)

async def responder_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    await reset_timer(chat_id, context)

    curso = context.chat_data.get("curso")
    contexto_geral = context.chat_data.get("contexto")

    if not curso and not contexto_geral:
        await update.message.reply_text(
            "❗ Antes de fazer uma pergunta, por favor selecione um curso ou o contexto geral usando /start."
        )
        return

    prefixo = f"No contexto de {curso}" if curso else "No contexto geral da FGA UnB"
    pergunta_com_contexto = f"{prefixo}: {user_input}"

    # Informa ao usuário que o bot está "digitando..."
    # Isso dá um feedback imediato e visual.
    await update.message.reply_chat_action(action=ChatAction.TYPING)

    try:
        # Executa a função síncrona/bloqueante 'responder' em um thread separado
        # Isso libera o bot para continuar processando outras coisas.
        resposta = await asyncio.to_thread(responder, pergunta_com_contexto)
        await update.message.reply_text(f"💬 {resposta}", parse_mode="HTML")

    except Exception as e:
        logger.error(f"Erro ao processar pergunta do usuário '{user_input}': {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Desculpe, ocorreu um erro ao buscar sua resposta. Por favor, tente novamente mais tarde."
        )