from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menus import create_menu, create_cursos_menu

# Cria o menu com perguntas de exemplo
def create_perguntas_exemplo(context=None):
    curso = 'Engenharias'
    if context and 'curso' in context.chat_data:
        curso = context.chat_data['curso']

    keyboard = [
        [InlineKeyboardButton(f"📌 Qual o fluxograma do curso de {curso}?", callback_data='exemplo_fluxograma')],
        [InlineKeyboardButton("🗓️ Como faço a matrícula?", callback_data='exemplo_matricula')],
        [InlineKeyboardButton("📧 Como entrar em contato com professores?", callback_data='exemplo_contato')],
        [InlineKeyboardButton("🔙 Voltar", callback_data='menu')]
    ]
    return InlineKeyboardMarkup(keyboard)

# Função para finalizar a conversa por inatividade
async def end_conversation(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(
        chat_id=job.chat_id,
        text="⏱️ A conversa foi encerrada por inatividade. Envie /start para começar novamente."
    )

    # Limpa os dados do chat e do usuário (opcional)
    context.chat_data.clear()
    context.user_data.clear()

# Reinicia o temporizador sempre que o usuário interage
async def reset_timer(chat_id, context: ContextTypes.DEFAULT_TYPE):
    old_job = context.chat_data.get("end_conversation_job")

    if old_job:
        try:
            old_job.schedule_removal()
        except Exception as e:
            # Log opcional: print(f"Erro ao remover job antigo: {e}")
            pass

    new_job = context.job_queue.run_once(end_conversation, 30, chat_id=chat_id)
    context.chat_data["end_conversation_job"] = new_job

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())
    await reset_timer(update.effective_chat.id, context)

# Handler dos botões
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    await reset_timer(update.effective_chat.id, context)

    if query.data == 'contexto':
        context.chat_data['curso'] = 'Engenharias'
        context.chat_data['contexto'] = True  # ADICIONADO
        await query.edit_message_text(
            "👋 Olá! Seja bem-vindo(a) ao assistente virtual da UnB – FGA!\n\n"
            "Estou aqui para te ajudar com dúvidas administrativas sobre o campus, como informações sobre matrícula, calendário acadêmico, fluxogramas, estágios, entre outros temas do dia a dia universitário.\n"
            "Você pode digitar sua dúvida normalmente ou escolher uma das perguntas de exemplo que aparecem abaixo.\n\n"
            "📌 *Exemplo:*\n"
            "Você pode perguntar algo como: *\"Qual o fluxograma do curso de Engenharias?\"*\n"
            "Nesse caso, eu te respondo com o link ou imagem do fluxograma mais atualizado disponível!\n\n"
            "💬 Agora é só escolher uma das perguntas sugeridas ou digitar a sua dúvida. Estou pronto para te ajudar!",
            parse_mode="Markdown",
            reply_markup=create_perguntas_exemplo(context)
        )

    elif query.data == 'cursos':
        await query.edit_message_text("📊 Escolha um Curso:", reply_markup=create_cursos_menu())

    elif query.data in ['curso_es', 'curso_eelet', 'curso_eaut', 'curso_eaero', 'curso_een']:
        cursos_dict = {
            'curso_es': 'Engenharia de Software',
            'curso_eelet': 'Engenharia Eletrônica',
            'curso_eaut': 'Engenharia Automotiva',
            'curso_eaero': 'Engenharia Aeroespacial',
            'curso_een': 'Engenharia de Energia'
        }
        curso_nome = cursos_dict.get(query.data, 'Engenharias')
        context.chat_data['curso'] = curso_nome

        await query.edit_message_text(
            f"👋 Você selecionou *{curso_nome}*!\n\n"
            "Estou aqui para te ajudar com dúvidas administrativas sobre o campus, como informações sobre matrícula, calendário acadêmico, fluxogramas, estágios, entre outros temas do dia a dia universitário.\n"
            "Você pode digitar sua dúvida normalmente ou escolher uma das perguntas de exemplo que aparecem abaixo.\n\n"
            "📌 *Exemplo:*\n"
            f"Você pode perguntar algo como: *\"Qual o fluxograma do curso de {curso_nome}?\"*\n"
            "Nesse caso, eu te respondo com o link ou imagem do fluxograma mais atualizado disponível!\n\n"
            "💬 Agora é só escolher uma das perguntas sugeridas ou digitar a sua dúvida. Estou pronto para te ajudar!",
            parse_mode="Markdown",
            reply_markup=create_perguntas_exemplo(context)
        )

    elif query.data == 'exemplo_fluxograma':
        curso = context.chat_data.get('curso', 'Engenharias')
        await query.edit_message_text(
            f"🔍 Você perguntou: *Qual o fluxograma do curso de {curso}?*\n\n"
            "Aguarde um instante enquanto eu busco essa informação pra você... 🧭",
            parse_mode="Markdown"
        )

        # Dicionário com os caminhos dos fluxogramas por curso
        fluxogramas = {
            'Engenharia de Software': {
                '2024': 'imgs/fluxo_software_2024.png',
                '2017': 'pdfs/Fluxo_Software_2017.pdf'
            },
            'Engenharia Aeroespacial': {
                # '2024': 'pdfs/Fluxo_Aeroespacial_2024.pdf',
                '2017': 'pdfs/Fluxo_Aeroespacial_2017.pdf'
            },
            'Engenharia Automotiva': {
                # '2024': 'pdfs/Fluxo_Aeroespacial_2024.pdf',
                # '2017': 'pdfs/Fluxo_Automotiva_2017.pdf'
            },
            'Engenharia de Energia': {
                # '2024': 'pdfs/Fluxo_Aeroespacial_2024.pdf',
                '2017': 'pdfs/Fluxo_Energia_2017.pdf'
            }
        }
        # Busca os arquivos correspondentes
        arquivos = fluxogramas.get(curso)
        if arquivos:
            # Envia o fluxograma mais recente (2024)
            with open(arquivos['2024'], 'rb') as fluxo_2024:
                await context.bot.send_photo(
                    chat_id=query.message.chat.id,
                    photo=fluxo_2024,
                    caption=f"📎 Aqui está o fluxograma mais recente (2024) do curso de {curso}.",
                    parse_mode="Markdown"
                )

            # Envia o fluxograma mais antigo (2017)
            with open(arquivos['2017'], 'rb') as fluxo_2017:
                await context.bot.send_document(
                    chat_id=query.message.chat.id,
                    document=fluxo_2017,
                    caption=f"📁 Aqui está o fluxograma mais antigo (2017) do curso de {curso}.",
                    parse_mode="Markdown"
                )
        else:
            # Curso não tem fluxograma disponível
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=f"❌ Desculpe, não encontrei fluxogramas cadastrados para o curso de {curso}.",
                parse_mode="Markdown"
            )

    elif query.data == 'exemplo_matricula':
        await query.edit_message_text(
            "📚 Você perguntou: *Como faço a matrícula?*\n\n"
            "A matrícula é feita pelo SIGAA, dentro do prazo definido no calendário acadêmico. Se precisar de ajuda, posso te mostrar o passo a passo!",
            parse_mode="Markdown"
        )

    elif query.data == 'exemplo_contato':
        await query.edit_message_text(
            "📧 Você perguntou: *Como entrar em contato com os professores?*\n\n"
            "Você pode encontrar os e-mails dos professores no site da FGA ou no SIGAA, na seção da disciplina em que ele leciona.",
            parse_mode="Markdown"
        )

    elif query.data == 'menu':
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())