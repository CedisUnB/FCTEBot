# handlers/perguntas.py
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from handlers.callbacks import reset_timer
from utils.db_helper import save_feedback
from handlers.menus import create_menu
from utils.api_helper import call_rag_api # <-- NOVO

logger = logging.getLogger(__name__)

async def responder_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    # Lógica de feedback (sem alterações)
    if context.chat_data.get('awaiting_suggestion_after_feedback'):
        logger.info(f"Recebida sugestão de {chat_id}: {user_input}")
        awaiting_suggestion_job = context.chat_data.pop("await_suggestion_job", None)
        if awaiting_suggestion_job:
            awaiting_suggestion_job.schedule_removal()
        save_feedback(chat_id, False, user_input)
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)
        await update.message.reply_text(
            "Obrigado pela sua sugestão! 👍 Ela foi registrada e é muito importante para mim.\n"
            "Para iniciar uma nova conversa, digite /start"
        )
        context.chat_data.clear()
        context.user_data.clear()
        return

    await reset_timer(chat_id, context)

    curso = context.chat_data.get("curso")
    contexto_geral = context.chat_data.get("contexto")

    if not curso and not contexto_geral:
        await update.message.reply_text(
            "❗ Antes de fazer uma pergunta, por favor selecione um curso ou o contexto de engenharias:",
            reply_markup=create_menu()
        )
        return

    prefixo = f"No contexto de {curso}" if curso else "No contexto geral da FGA UnB"
    pergunta_com_contexto = f"{prefixo}: {user_input}"
    
    await update.message.reply_text("🔎 Buscando a resposta para sua pergunta, só um instante...")
    await update.message.reply_chat_action(action=ChatAction.TYPING)

    # --- CHAMADA ASSÍNCRONA PARA A API ---
    resposta = await call_rag_api(pergunta_com_contexto)
    # --- FIM DA CHAMADA ---

    await update.message.reply_text(f"💬 {resposta}", parse_mode="HTML")