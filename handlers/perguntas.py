# handlers/perguntas.py

from telegram import Update
from telegram.ext import ContextTypes
from rag import responder
from handlers.callbacks import reset_timer # IMPORTAR
from handlers.menus import create_menu  # Importa os botões

async def responder_pergunta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_input = update.message.text.strip()

    # Resetar o timer de inatividade a cada mensagem do usuário
    await reset_timer(chat_id, context) # ADICIONADO AQUI

    curso = context.chat_data.get("curso")
    contexto_geral = context.chat_data.get("contexto") # Renomeado para evitar conflito com 'context' do telegram.ext

    if not curso and not contexto_geral: # Verificação atualizada
        await update.message.reply_text(
            "❗ Antes de fazer uma pergunta, por favor selecione um curso ou o contexto de engenharias:", # adicionar as opções de curso ou contexto geral 
            reply_markup=create_menu()
        )
        return

    prefixo = f"No contexto de {curso}" if curso else "No contexto geral da FGA UnB"
    pergunta_com_contexto = f"{prefixo}: {user_input}"

    await update.message.reply_text("🔎 Buscando a resposta para sua pergunta, só um instante...")

    resposta = responder(pergunta_com_contexto) # Função síncrona, pode bloquear se demorar

    await update.message.reply_text(f"💬 {resposta}", parse_mode="HTML")