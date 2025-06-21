import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.menus import create_menu, create_cursos_menu
from utils.db_helper import save_feedback
from rag import responder
import logging
import asyncio
from telegram.constants import ChatAction   

logger = logging.getLogger(__name__)

INACTIVITY_TIMEOUT_ASK_FEEDBACK = 120
INACTIVITY_TIMEOUT_END_CONVERSATION = 180

# Cria o menu com perguntas de exemplo
def create_perguntas_exemplo(context=None):
    curso = 'Engenharias'
    if context and 'curso' in context.chat_data:
        curso = context.chat_data['curso']

    keyboard = []

    # Só adiciona a pergunta do fluxograma se o curso for específico (≠ 'Engenharias')
    if curso != 'Engenharias':
        keyboard.append(
            [InlineKeyboardButton(f"📌 Qual o fluxograma do curso de {curso}?", callback_data='exemplo_fluxograma')]
        )

    keyboard.append([InlineKeyboardButton("🗓️ Como faço a matrícula?", callback_data='exemplo_matricula')])

    # Adiciona botão específico dependendo do curso
    if curso == 'Engenharias':
        keyboard.append([InlineKeyboardButton("📧 Qual o e-mail dos professores do ciclo básico?", callback_data='exemplo_contato')])
    else:
        keyboard.append([InlineKeyboardButton("📧 Qual o e-mail dos professores?", callback_data='exemplo_contato')])

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

# Função para pedir feedback após inatividade
async def ask_for_feedback(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏳ Parece que você está inativo(a). Consegui te ajudar com sua dúvida?",
            reply_markup=create_feedback_buttons()
        )
        # Agenda o encerramento final da conversa se não houver resposta ao feedback
        new_job_end = context.job_queue.run_once(
            end_conversation_final,
            INACTIVITY_TIMEOUT_END_CONVERSATION,
            chat_id=chat_id,
            name=f"final_end_job_{chat_id}"
        )
        context.chat_data["final_end_conversation_job"] = new_job_end
        logger.info(f"Pedido de feedback enviado para {chat_id}. Job de encerramento final agendado.")
    except Exception as e:
        logger.error(f"Erro ao enviar pedido de feedback para {chat_id}: {e}")


# Função para finalizar a conversa por inatividade (após o pedido de feedback não respondido)
async def end_conversation_final(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    chat_id = job.chat_id
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⏱️ A conversa foi encerrada por inatividade. Envie /start para começar novamente."
        )
        logger.info(f"Conversa com {chat_id} encerrada por inatividade final.")
    except Exception as e:
        logger.error(f"Erro ao encerrar conversa final com {chat_id}: {e}")
    finally:
        # Limpa os dados do chat e do usuário
        context.chat_data.clear()
        context.user_data.clear()

# Reinicia o(s) temporizador(es) sempre que o usuário interage
async def reset_timer(chat_id, context: ContextTypes.DEFAULT_TYPE):
    current_ask_feedback_job = context.chat_data.get("ask_feedback_job")
    if current_ask_feedback_job:
        try:
            current_ask_feedback_job.schedule_removal()
            logger.debug(f"Job 'ask_feedback_job' para {chat_id} removido.")
        except Exception as e:
            logger.warning(f"Erro ao remover job 'ask_feedback_job' antigo para {chat_id}: {e}")

    current_final_end_job = context.chat_data.get("final_end_conversation_job")
    if current_final_end_job:
        try:
            current_final_end_job.schedule_removal()
            logger.debug(f"Job 'final_end_conversation_job' para {chat_id} removido.")
        except Exception as e:
            logger.warning(f"Erro ao remover job 'final_end_conversation_job' antigo para {chat_id}: {e}")

    new_ask_feedback_job = context.job_queue.run_once(
        ask_for_feedback,
        INACTIVITY_TIMEOUT_ASK_FEEDBACK,
        chat_id=chat_id,
        name=f"ask_feedback_job_{chat_id}"
    )
    context.chat_data["ask_feedback_job"] = new_ask_feedback_job
    logger.info(f"Timer resetado para {chat_id}. Job de pedir feedback agendado.")


# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    welcome_message = (
        "👋 Olá! Seja bem-vindo(a) ao assistente virtual da UnB – FGA!\n\n"
        "Estou aqui para te ajudar com dúvidas administrativas sobre o campus, como informações sobre matrícula, fluxogramas, estágios, entre outros temas gerais do dia a dia universitário.\n\n"
        "Para iniciar, selecione *Engenharias* ou o seu curso abaixo. Você também pode digitar sua dúvida se preferir.\n\n"
        "👇 Escolha uma das opções:"
    )
    await update.message.reply_text(welcome_message, parse_mode="Markdown", reply_markup=create_menu())
    await reset_timer(update.effective_chat.id, context)


# Handler dos botões de feedback
async def handle_feedback_button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id

    # Remove o job de encerramento final, pois o usuário respondeu ao feedback
    final_end_job = context.chat_data.get("final_end_conversation_job")
    if final_end_job:
        try:
            final_end_job.schedule_removal()
            logger.info(f"Job de encerramento final para {chat_id} cancelado devido à resposta de feedback.")
        except Exception as e:
            logger.warning(f"Erro ao remover job de encerramento final para {chat_id}: {e}")
        context.chat_data.pop("final_end_conversation_job", None)

    feedback_given = None
    if query.data == 'feedback_yes':
        feedback_given = True
        await query.edit_message_text("Obrigado pelo seu feedback! 😊 Fico feliz em ajudar. Para iniciar uma nova conversa digite /start")
    elif query.data == 'feedback_no':
        feedback_given = False
        await query.edit_message_text("Obrigado pelo seu feedback! 👍 Vou continuar aprendendo para te ajudar melhor da próxima vez. \n Enquanto isso, entre em contato com a secretaria do campus para obter a resposta que deseja: (61) 3107-8901.\n Para iniciar uma nova conversa digite /start")

    if feedback_given is not None:
        save_feedback(chat_id, feedback_given)

    logger.info(f"Feedback recebido de {chat_id}. Encerrando sessão de interação ativa.")
    context.chat_data.clear()
    context.user_data.clear()

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    await reset_timer(update.effective_chat.id, context) # Reset timer em qualquer interação de botão

    if query.data == 'contexto':
        context.chat_data['curso'] = 'Engenharias'  # Default se contexto geral
        context.chat_data['contexto'] = True
        await query.edit_message_text(
            "👋 Você selecionou o contexto geral das *Engenharias*.\n\n"
            "Você pode digitar sua dúvida normalmente ou escolher uma das perguntas de exemplo que aparecem abaixo.\n\n"
            "📌 *Exemplo:*\n"
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
        context.chat_data['contexto'] = False # Define contexto como falso se um curso é escolhido

        await query.edit_message_text(
            f"👋 Você selecionou *{curso_nome}*!\n\n"
            "Você pode digitar sua dúvida normalmente ou escolher uma das perguntas de exemplo que aparecem abaixo.\n\n"
            "📌 *Exemplo:*\n"
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
        # Dicionário com os caminhos dos fluxogramas por curso
        fluxogramas = {
            'Engenharia de Software': {
                '2024': 'imgs/2024/Fluxo_Software_2024.png',
                '2017': 'imgs/2017/Fluxo_Software_2017.jpeg'
            },
            'Engenharia Aeroespacial': {
                '2024': 'imgs/2024/Fluxo_Aeroespacial_2024.png',
                '2017': 'imgs/2017/Fluxo_Aeroespacial_2017.jpeg'
            },
            'Engenharia Automotiva': {
                '2024': 'imgs/2024/Fluxo_Automotiva_2024.png',
                '2017': 'imgs/2017/Fluxo_Automotiva_2017.jpeg'
            },
            'Engenharia de Energia': {
                '2024': 'imgs/2024/Fluxo_Energia_2024.png',
                '2017': 'imgs/2017/Fluxo_Energia_2017.jpeg'
            },
            'Engenharia Eletrônica': {
                '2024': 'imgs/2024/Fluxo_Eletronica_2024.jpg',
                '2017': 'imgs/2017/Fluxo_Eletronica_2017.png'
            }
        }

        # Dicionário com a fonte por curso
        fontes = {
            'Engenharia de Software': 'https://software.unb.br/ensino/estrutura-curricular',
            'Engenharia Aeroespacial': 'https://fcte.unb.br/engenharia-aeroespacial/',
            'Engenharia Automotiva': 'https://fcte.unb.br/engenharia-automotiva/',
            'Engenharia de Energia': 'https://fcte.unb.br/engenharia-de-energia/',
            'Engenharia Eletrônica': 'https://eletronica.unb.br/matriz-curricular/'
        }
        # Busca os arquivos correspondentes
        arquivos = fluxogramas.get(curso)
        fonte = fontes.get(curso, 'Coordenação do curso')
        if arquivos:
            # Envia o fluxograma mais recente (2024)
            if '2024' in arquivos: # Verifica se a chave existe
                try:
                    with open(arquivos['2024'], 'rb') as fluxo_2024:
                        await context.bot.send_photo(
                            chat_id=query.message.chat.id,
                            photo=fluxo_2024,
                            caption=(
                                f"📎 Aqui está o fluxograma mais recente (2024) do curso de {curso}.\n\n"
                                f"📚 *Fonte:* {fonte}"
                            ),
                            parse_mode="Markdown"
                        )
                except FileNotFoundError:
                    logger.error(f"Arquivo não encontrado: {arquivos['2024']}")
                    await context.bot.send_message(chat_id=query.message.chat.id, text=f"Desculpe, o arquivo do fluxograma de 2024 para {curso} não foi encontrado.")

            # Envia o fluxograma mais antigo (2017)
            if '2017' in arquivos: # Verifica se a chave existe
                try:
                    with open(arquivos['2017'], 'rb') as fluxo_2017:
                        await context.bot.send_photo(
                            chat_id=query.message.chat.id,
                            photo=fluxo_2017,
                            caption=(
                                f"📁 Aqui está o fluxograma mais antigo (2017) do curso de {curso}.\n\n"
                                f"📚 *Fonte:* {fonte}"
                            ),
                            parse_mode="Markdown"
                        )
                except FileNotFoundError:
                    logger.error(f"Arquivo não encontrado: {arquivos['2017']}")
                    await context.bot.send_message(chat_id=query.message.chat.id, text=f"Desculpe, o arquivo do fluxograma de 2017 para {curso} não foi encontrado.")
            if not ('2024' in arquivos or '2017' in arquivos): # Se nenhuma chave foi encontrada
                 await context.bot.send_message(
                    chat_id=query.message.chat.id,
                    text=f"❌ Desculpe, não encontrei arquivos de fluxogramas cadastrados para o curso de {curso}.",
                    parse_mode="Markdown"
                )
        else:
            # Curso não tem fluxograma disponível
            await context.bot.send_message(
                chat_id=query.message.chat.id,
                text=f"❌ Desculpe, não encontrei fluxogramas cadastrados para o curso de {curso}.",
                parse_mode="Markdown"
            )
        await context.bot.send_message(
            chat_id=query.message.chat.id,
            text="ℹ️ Se quiser, posso te ajudar com outras informações também!",
            reply_markup=create_perguntas_exemplo(context)
        )

    elif query.data in ['exemplo_matricula', 'exemplo_contato']:
        user_question_text = ""
        curso_para_contexto_rag = context.chat_data.get('curso', 'Engenharias')

        if query.data == 'exemplo_matricula':
            user_question_text = "Como faço a matrícula?"
        elif query.data == 'exemplo_contato':
            if curso_para_contexto_rag == 'Engenharias':
                user_question_text = "Qual o e-mail dos professores do ciclo básico?"
            else:
                user_question_text = "Como entrar em contato com os professores?"

        pergunta_para_rag = f"No contexto de {curso_para_contexto_rag}: {user_question_text}"

        await query.edit_message_text(
            f"🔍 Você selecionou o exemplo: {user_question_text}\n\n"
            "Aguarde um instante enquanto eu busco essa informação pra você... 🧭",
            parse_mode="Markdown"
        )
        
        # Feedback visual para o usuário
        await context.bot.send_chat_action(chat_id=query.message.chat.id, action=ChatAction.TYPING)

        try:
            # A chamada já era assíncrona, o que é bom.
            resposta_rag = await asyncio.to_thread(responder, pergunta_para_rag)

            await query.edit_message_text(
                text=f"💬 {resposta_rag}",
                parse_mode="HTML",
                reply_markup=create_perguntas_exemplo(context)
            )
        except Exception as e:
            logger.error(f"Erro ao obter resposta do RAG para pergunta de exemplo '{query.data}': {e}", exc_info=True)
            await query.edit_message_text(
                text="❌ Desculpe, ocorreu um erro ao processar sua pergunta de exemplo. Por favor, tente digitar sua dúvida ou volte ao menu.",
                reply_markup=create_perguntas_exemplo(context)
            )
    elif query.data == 'menu':
        # Ao voltar para o menu principal, limpamos o curso e contexto para forçar nova seleção.
        context.chat_data.pop('curso', None)
        context.chat_data.pop('contexto', None)
        await query.edit_message_text("Olá! Escolha uma das opções abaixo:", reply_markup=create_menu())