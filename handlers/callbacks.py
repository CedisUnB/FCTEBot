from telegram import Update
from telegram.ext import ContextTypes
from handlers.menus import (
    create_menu, create_matricula_menu, create_estagio_menu,
    create_fluxos_menu, create_duvida_curso_menu
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = "Olá! Escolha uma das opções abaixo:"
    await update.message.reply_text(welcome_message, reply_markup=create_menu())

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.data == 'matricula':
        await query.edit_message_text("📄 Escolha uma opção de Matrícula:", reply_markup=create_matricula_menu())
    elif query.data == 'estagio':
        await query.edit_message_text("💼 Escolha uma opção de Estágio:", reply_markup=create_estagio_menu())
    elif query.data == 'fluxos':
        await query.edit_message_text("📊 Escolha um Fluxo de Curso:", reply_markup=create_fluxos_menu())
    elif query.data == 'duvida':
        await query.edit_message_text(
            "👀 Para melhor te ajudar, escolha seu curso abaixo:",
            reply_markup=create_duvida_curso_menu()
        )

    # Submenus - Matrícula
    elif query.data == 'matricula_geral':
        await query.edit_message_text("ℹ️ Informações sobre Matrícula Geral...")
    elif query.data == 'rematricula':
        await query.edit_message_text("ℹ️ Informações sobre Rematrícula...")
    elif query.data == 'extraordinaria':
        await query.edit_message_text("ℹ️ Informações sobre Matrícula Extraordinária...")

    # Submenus - Estágio
    elif query.data == 'estagio_obrigatorio':
        await query.edit_message_text("ℹ️ Informações sobre Estágio Obrigatório...")
    elif query.data == 'estagio_nao_obrigatorio':
        await query.edit_message_text("ℹ️ Informações sobre Estágio Não Obrigatório...")

    # Submenus - Fluxos
    elif query.data == 'fluxo_es':
        await query.edit_message_text("ℹ️ Fluxo: Engenharia de Software (ES).")
    elif query.data == 'fluxo_eelet':
        await query.edit_message_text("ℹ️ Fluxo: Engenharia Elétrica (EElet).")
    elif query.data == 'fluxo_eaut':
        await query.edit_message_text("ℹ️ Fluxo: Engenharia Automotiva (EAut).")
    elif query.data == 'fluxo_eaero':
        await query.edit_message_text("ℹ️ Fluxo: Engenharia Aeroespacial (EAero).")
    elif query.data == 'fluxo_een':
        await query.edit_message_text("ℹ️ Fluxo: Engenharia de Energia (EEn).")

    # Dúvida - após selecionar o curso
    elif query.data.startswith('duvida_'):
        curso = query.data.split('_')[1].capitalize()
        await query.edit_message_text(
            f"💬 Você selecionou o curso: {curso}. Agora, por favor, digite sua dúvida abaixo e responderemos o quanto antes!"
        )

    elif query.data == 'menu':
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())
