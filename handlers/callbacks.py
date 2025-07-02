import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menus import create_menu, create_cursos_menu
from utils.db_helper import save_feedback
from utils.api_helper import call_rag_api  # <-- NOVO
import logging
from telegram.constants import ChatAction


logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT_ASK_FEEDBACK = 120
INACTIVITY_TIMEOUT_AWAIT_SUGGESTION = 180
INACTIVITY_TIMEOUT_END_CONVERSATION_AFTER_FEEDBACK_PROMPT = 180

async def _handle_pending_suggestion_timeout(context: ContextTypes.DEFAULT_TYPE):

    job = context.job
    chat_id = job.chat_id

    if context.chat_data.get('awaiting_suggestion_after_feedback'):
        logger.info(f"Usuário {chat_id} não enviou sugestão a tempo. Salvando feedback 'Não' sem sugestão.")
        save_feedback(chat_id, False, None)
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)
        context.chat_data.pop('await_suggestion_job', None)

        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text="📝 Sua sugestão não foi recebida a tempo. A conversa foi encerrada.\n"
                     "Se precisar de mais alguma coisa, digite /start para começar novamente."
            )
        except Exception as e:
            logger.error(f"Erro ao enviar mensagem de timeout de sugestão para {chat_id}: {e}")
        finally:
            context.chat_data.clear()
            context.user_data.clear()
    else:
        logger.debug(f"Timeout de sugestão para {chat_id}, mas não estava aguardando sugestão. Nenhuma ação.")

def create_perguntas_exemplo(context=None):
    curso = 'Engenharias'
    if context and 'curso' in context.chat_data:
        curso = context.chat_data['curso']
    keyboard = []
    if curso != 'Engenharias':
        keyboard.append(
            [InlineKeyboardButton(f"📌 Qual o fluxograma do curso de {curso}?", callback_data='exemplo_fluxograma')]
        )
    keyboard.append([InlineKeyboardButton("🗓️ Como faço a matrícula?", callback_data='exemplo_matricula')])
    if curso == 'Engenharias':
        keyboard.append([InlineKeyboardButton("📧 Qual o email dos professores do ciclo básico?", callback_data='exemplo_contato')])
    else:
        keyboard.append([InlineKeyboardButton("📧 Qual o email dos professores?", callback_data='exemplo_contato')])
    keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data='menu')])
    return InlineKeyboardMarkup(keyboard)

def create_feedback_buttons():
    keyboard = [
        [
            InlineKeyboardButton("👍 Sim", callback_data='feedback_yes'),
            InlineKeyboardButton("👎 Não", callback_data='feedback_no')
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

async def ask_for_feedback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id

    if context.chat_data.get('awaiting_suggestion_after_feedback'):
        logger.warning(f"ask_for_feedback chamado para {chat_id} enquanto aguardava sugestão. Isso não deveria acontecer.")
        await _handle_pending_suggestion_timeout(context)
        return

    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Parece que você está inativo(a). Consegui te ajudar com sua dúvida?",
            reply_markup=create_feedback_buttons()
        )

        new_job_end = context.job_queue.run_once(
            end_conversation_after_feedback_prompt, 
            INACTIVITY_TIMEOUT_END_CONVERSATION_AFTER_FEEDBACK_PROMPT,
            chat_id=chat_id,
            name=f"end_after_feedback_prompt_job_{chat_id}"
        )
        context.chat_data["end_conversation_job"] = new_job_end
        logger.info(f"Pedido de feedback enviado para {chat_id}. Job de encerramento (end_after_feedback_prompt_job) agendado.")
    except Exception as e:
        logger.error(f"Erro ao enviar pedido de feedback para {chat_id}: {e}")

async def end_conversation_after_feedback_prompt(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    try:
        if "end_conversation_job" not in context.chat_data :
            logger.info(f"Job end_conversation_after_feedback_prompt para {chat_id} já tratado ou cancelado.")
            return
        if context.chat_data.get('awaiting_suggestion_after_feedback'):
            logger.info(f"Job end_conversation_after_feedback_prompt para {chat_id} cancelado, pois está aguardando sugestão.")
            return

        await context.bot.send_message(
            chat_id=chat_id,
            text="⏱️ A conversa foi encerrada por inatividade após o pedido de feedback. Envie /start para começar novamente."
        )
        logger.info(f"Conversa com {chat_id} encerrada por inatividade (não respondeu ao Sim/Não).")
    except Exception as e:
        logger.error(f"Erro ao encerrar conversa após pedido de feedback com {chat_id}: {e}")
    finally:
        context.chat_data.clear()
        context.user_data.clear()

async def reset_timer(chat_id, context: ContextTypes.DEFAULT_TYPE):
    if context.chat_data.get('awaiting_suggestion_after_feedback'):
        logger.debug(f"Timer de inatividade geral não resetado para {chat_id} pois está aguardando sugestão.")
        return
    current_ask_feedback_job = context.chat_data.pop("ask_feedback_job", None)
    if current_ask_feedback_job:
        try:
            current_ask_feedback_job.schedule_removal()
            logger.debug(f"Job 'ask_feedback_job' para {chat_id} removido.")
        except Exception as e:
            logger.warning(f"Erro ao remover job 'ask_feedback_job' antigo para {chat_id}: {e}")

    current_end_conversation_job = context.chat_data.pop("end_conversation_job", None)
    if current_end_conversation_job:
        try:
            current_end_conversation_job.schedule_removal()
            logger.debug(f"Job 'end_conversation_job' para {chat_id} removido.")
        except Exception as e:
            logger.warning(f"Erro ao remover job 'end_conversation_job' antigo para {chat_id}: {e}")

    new_ask_feedback_job = context.job_queue.run_once(
        ask_for_feedback,
        INACTIVITY_TIMEOUT_ASK_FEEDBACK,
        chat_id=chat_id,
        name=f"ask_feedback_job_{chat_id}"
    )
    context.chat_data["ask_feedback_job"] = new_ask_feedback_job
    logger.info(f"Timer de inatividade geral resetado para {chat_id}. Job de pedir feedback agendado.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id

    awaiting_suggestion_job = context.chat_data.pop("await_suggestion_job", None)
    if awaiting_suggestion_job:
        awaiting_suggestion_job.schedule_removal()
        logger.info(f"Usuário {chat_id} digitou /start enquanto aguardava sugestão. Salvando feedback 'Não' e cancelando job.")
        save_feedback(chat_id, False, None)
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)

    welcome_message = (
        "👋 Olá! Seja bem-vindo(a) ao assistente virtual da UnB – FCTE!\n\n"
        "Estou aqui para te ajudar com dúvidas administrativas sobre o campus, como informações sobre matrícula, fluxogramas, estágios, entre outros temas gerais do dia a dia universitário.\n\n"
        "Para iniciar, selecione *Engenharias* ou o seu curso abaixo. Você também pode digitar sua dúvida se preferir.\n\n"
        "👇 Escolha uma das opções:"
    )
    context.chat_data.clear() 
    context.user_data.clear()

    await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=create_menu())
    await reset_timer(chat_id, context)

async def handle_feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    end_conversation_job = context.chat_data.pop("end_conversation_job", None)
    if end_conversation_job:
        end_conversation_job.schedule_removal()
        logger.info(f"Job 'end_conversation_job' para {chat_id} cancelado devido à resposta de feedback.")

    awaiting_suggestion_job = context.chat_data.pop("await_suggestion_job", None)
    if awaiting_suggestion_job:
        awaiting_suggestion_job.schedule_removal()
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)


    if query.data == 'feedback_yes':
        save_feedback(chat_id, True)
        await query.edit_message_text("Obrigado pelo seu feedback! 😊 Fico feliz em ajudar. Para iniciar uma nova conversa digite /start")
        logger.info(f"Feedback POSITIVO recebido de {chat_id}. Encerrando sessão de interação ativa.")
        context.chat_data.clear()
        context.user_data.clear()
        ask_feedback_job = context.chat_data.pop("ask_feedback_job", None)
        if ask_feedback_job: ask_feedback_job.schedule_removal()


    elif query.data == 'feedback_no':
        context.chat_data['awaiting_suggestion_after_feedback'] = True
        await query.edit_message_text(
            "Lamento não ter ajudado como esperado. 😕\n"
            "Para que eu possa melhorar, por favor, envie sua sugestão ou observação como uma mensagem de texto.\n\n"
            "Sua opinião é muito importante! Se não enviar uma sugestão em alguns minutos, a conversa será encerrada."
        )
        new_suggestion_timeout_job = context.job_queue.run_once(
            _handle_pending_suggestion_timeout,
            INACTIVITY_TIMEOUT_AWAIT_SUGGESTION,
            chat_id=chat_id,
            name=f"await_suggestion_job_{chat_id}"
        )
        context.chat_data["await_suggestion_job"] = new_suggestion_timeout_job
        logger.info(f"Feedback NEGATIVO preliminar de {chat_id}. Aguardando sugestão. Job de timeout de sugestão agendado.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    awaiting_suggestion_job = context.chat_data.pop("await_suggestion_job", None)
    if awaiting_suggestion_job:
        awaiting_suggestion_job.schedule_removal()
        logger.info(f"Usuário {chat_id} clicou em botão enquanto aguardava sugestão. Salvando feedback 'Não' e cancelando job.")
        save_feedback(chat_id, False, None) 
        context.chat_data.pop('awaiting_suggestion_after_feedback', None)

    await reset_timer(chat_id, context)

    if query.data == 'contexto':
        context.chat_data['curso'] = 'Engenharias'
        context.chat_data['contexto'] = True
        await query.edit_message_text(
            "👋 Você selecionou o contexto geral das *Engenharias*.\n\n"
            "✅ *Aqui está tudo o que você pode me perguntar:*\n\n"
            "🎓 *Vida Acadêmica:*\n"
            "• Manual do Estudante\n"
            "• Matrícula (calouro, veterano, transferido)\n"
            "• Estágio, Monitoria e TCC\n"
            "• Dupla Graduação, Confirmação de Matrícula e Mudança de Curso\n"
            "• Fluxogramas, Cadeias de Seletividade, Carga Horária, Matérias Optativas\n"
            "• Aproveitamento de horas e Equivalência de disciplinas\n"
            "• Calendário Acadêmico\n"
            "• IRA, Menção, Revisão de Menção, Trancamentos e Critérios de Jubilamento (desligamento)\n"
            "• Diploma, Colação de Grau, Status de Formando, Checklist do Calouro\n"
            "• Principais Formulários Acadêmicos\n"
            "• Turmas disponíveis no semestre\n"
            "• Língua Estrangeira, Aluno Especial, Habilidades Específicas e Transferências\n\n"
            "🏢 *Informações do Campus Gama:*\n"
            "• Informações gerais da unidade Gama e de cada curso de Engenharia\n"
            "• Corpo Docente (professores)\n"
            "• Serviços disponíveis no campus: Secretaria, Auxílios e Assistência Estudantil, Psicóloga, Acessibilidade\n"
            "• Extensão, Iniciação Científica, Laboratórios do campus\n\n"
            "📌 *Exemplo de pergunta:*\n"
            "Você pode perguntar algo como: *\"Como faço a matrícula?\"*\n"
            "Nesse caso, eu te respondo com as principais informações sobre como fazer a matrícula sendo calouro, transferido ou veterano!\n\n"
            "⚠️ *IMPORTANTE:*\n"
            "Lembre-se que não sou capaz de trazer informações *pessoais* sobre você e nem consigo acompanhar um diálogo com várias mensagens.\n"
            "Então, envie suas perguntas de forma *clara e completa*, com o *contexto necessário*, para que eu possa ajudar da melhor forma!\n\n"
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
        context.chat_data['contexto'] = False

        await query.edit_message_text(
            f"👋 Você selecionou *{curso_nome}*!\n\n"
            "✅ *Aqui está tudo o que você pode me perguntar:*\n\n"
            "🎓 *Vida Acadêmica:*\n"
            "• Manual do Estudante\n"
            "• Matrícula (calouro, veterano, transferido)\n"
            "• Estágio, Monitoria e TCC\n"
            "• Dupla Graduação, Confirmação de Matrícula e Mudança de Curso\n"
            "• Fluxogramas, Cadeias de Seletividade, Carga Horária, Matérias Optativas\n"
            "• Aproveitamento de horas e Equivalência de disciplinas\n"
            "• Calendário Acadêmico\n"
            "• IRA, Menção, Revisão de Menção, Trancamentos e Critérios de Jubilamento (desligamento)\n"
            "• Diploma, Colação de Grau, Status de Formando, Checklist do Calouro\n"
            "• Principais Formulários Acadêmicos\n"
            "• Turmas disponíveis no semestre\n"
            "• Língua Estrangeira, Aluno Especial, Habilidades Específicas e Transferências\n\n"
            "🏢 *Informações do Campus Gama:*\n"
            "• Informações gerais da unidade Gama e de cada curso de Engenharia\n"
            "• Corpo Docente (professores)\n"
            "• Serviços disponíveis no campus: Secretaria, Auxílios e Assistência Estudantil, Psicóloga, Acessibilidade\n"
            "• Extensão, Iniciação Científica, Laboratórios do campus\n\n"
            "📌 *Exemplo de pergunta:*\n"
            f"Você pode perguntar algo como: *\"Qual o fluxograma do curso de {curso_nome}?\"*\n"
            "Nesse caso, eu te respondo com o link ou imagem do fluxograma mais atualizado disponível!\n\n"
            "⚠️ *IMPORTANTE:*\n"
            "Lembre-se que não sou capaz de trazer informações *pessoais* sobre você e nem consigo acompanhar um diálogo com várias mensagens.\n"
            "Então, envie suas perguntas de forma *clara e completa*, com o *contexto necessário*, para que eu possa ajudar da melhor forma!\n\n"
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
        fluxogramas = {
            'Engenharia de Software': {'2024': 'imgs/2024/Fluxo_Software_2024.png', '2017': 'imgs/2017/Fluxo_Software_2017.jpeg'},
            'Engenharia Aeroespacial': {'2024': 'imgs/2024/Fluxo_Aeroespacial_2024.png', '2017': 'imgs/2017/Fluxo_Aeroespacial_2017.jpeg'},
            'Engenharia Automotiva': {'2024': 'imgs/2024/Fluxo_Automotiva_2024.png', '2017': 'imgs/2017/Fluxo_Automotiva_2017.jpeg'},
            'Engenharia de Energia': {'2024': 'imgs/2024/Fluxo_Energia_2024.png', '2017': 'imgs/2017/Fluxo_Energia_2017.jpeg'},
            'Engenharia Eletrônica': {'2024': 'imgs/2024/Fluxo_Eletronica_2024.jpg', '2017': 'imgs/2017/Fluxo_Eletronica_2017.png'}
        }
        fontes = {
            'Engenharia de Software': 'https://software.unb.br/ensino/estrutura-curricular',
            'Engenharia Aeroespacial': 'https://fcte.unb.br/engenharia-aeroespacial/',
            'Engenharia Automotiva': 'https://fcte.unb.br/engenharia-automotiva/',
            'Engenharia de Energia': 'https://fcte.unb.br/engenharia-de-energia/',
            'Engenharia Eletrônica': 'https://eletronica.unb.br/matriz-curricular/'
        }
        arquivos = fluxogramas.get(curso)
        fonte = fontes.get(curso, 'Coordenação do curso')
        if arquivos:
            if '2024' in arquivos:
                try:
                    with open(arquivos['2024'], 'rb') as fluxo_2024:
                        await context.bot.send_photo(chat_id=query.message.chat.id, photo=fluxo_2024, caption=f"📎 Aqui está o fluxograma mais recente (2024) do curso de {curso}.\n\n📚 *Fonte:* {fonte}", parse_mode="Markdown")
                except FileNotFoundError:
                    logger.error(f"Arquivo não encontrado: {arquivos['2024']}")
                    await context.bot.send_message(chat_id=query.message.chat.id, text=f"Desculpe, o arquivo do fluxograma de 2024 para {curso} não foi encontrado.")
            if '2017' in arquivos:
                try:
                    with open(arquivos['2017'], 'rb') as fluxo_2017:
                        await context.bot.send_photo(chat_id=query.message.chat.id, photo=fluxo_2017, caption=f"📁 Aqui está o fluxograma mais antigo (2017) do curso de {curso}.\n\n📚 *Fonte:* {fonte}", parse_mode="Markdown")
                except FileNotFoundError:
                    logger.error(f"Arquivo não encontrado: {arquivos['2017']}")
                    await context.bot.send_message(chat_id=query.message.chat.id, text=f"Desculpe, o arquivo do fluxograma de 2017 para {curso} não foi encontrado.")
            if not ('2024' in arquivos or '2017' in arquivos):
                 await context.bot.send_message(chat_id=query.message.chat.id, text=f"❌ Desculpe, não encontrei arquivos de fluxogramas cadastrados para o curso de {curso}.", parse_mode="Markdown")
        else:
            await context.bot.send_message(chat_id=query.message.chat.id, text=f"❌ Desculpe, não encontrei fluxogramas cadastrados para o curso de {curso}.", parse_mode="Markdown")
        await context.bot.send_message(chat_id=query.message.chat.id, text="ℹ️ Se quiser, posso te ajudar com outras informações também!", reply_markup=create_perguntas_exemplo(context))

    elif query.data in ['exemplo_matricula', 'exemplo_contato']:
        user_question_text = ""
        curso_para_contexto_rag = context.chat_data.get('curso', 'Engenharias')
        if query.data == 'exemplo_matricula':
            user_question_text = "Como faço a matrícula?"
        elif query.data == 'exemplo_contato':
            if curso_para_contexto_rag == 'Engenharias':
                user_question_text = "Qual o email dos professores do ciclo básico?"
            else:
                user_question_text = "Qual o email dos professores?"
        
        pergunta_para_rag = f"No contexto de {curso_para_contexto_rag}: {user_question_text}"
        await query.edit_message_text(f"🔍 Você selecionou o exemplo: {user_question_text}\n\nAguarde um instante... 🧭", parse_mode="Markdown")
        await context.bot.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.TYPING)
        
        # --- CHAMADA ASSÍNCRONA PARA A API ---
        resposta_rag = await call_rag_api(pergunta_para_rag)
        # --- FIM DA CHAMADA ---
        
        await query.edit_message_text(text=f"💬 {resposta_rag}", parse_mode="HTML", reply_markup=create_perguntas_exemplo(context))

    elif query.data == 'menu':
        context.chat_data.pop('curso', None)
        context.chat_data.pop('contexto', None)
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())