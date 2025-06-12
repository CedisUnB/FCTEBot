from telegram import Update
from telegram.ext import ContextTypes
from rag import responder  # Certifique-se de que o arquivo RAG está como `rag.py` no mesmo diretório ou no PYTHONPATH

async def responder_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    curso = context.chat_data.get("curso")
    contexto = context.chat_data.get("contexto")

    if not curso and not contexto:
        await update.message.reply_text(
            "❗ Antes de fazer uma pergunta, por favor selecione um curso ou o contexto geral usando /start."
        )
        return

    prefixo = f"No contexto de {curso}" if curso else "No contexto geral"
    pergunta_com_contexto = f"{prefixo}: {user_input}"

    await update.message.reply_text("🔎 Buscando a resposta para sua pergunta, só um instante...")

    resposta = responder(pergunta_com_contexto)

    await update.message.reply_text(f"💬 {resposta}", parse_mode="HTML")
