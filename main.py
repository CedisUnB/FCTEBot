# main.py (Versão Corrigida para integração asyncio)
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Importações do Bot
from telegram.ext import Application
from handlers.callbacks import start, button, handle_feedback_button
from handlers.perguntas import responder_pergunta
from telegram.ext import CommandHandler, CallbackQueryHandler, MessageHandler, filters

# Importações da API RAG
from rag_logic import get_contexto_rag, gerar_resposta_rag

# --- Configuração Inicial ---
load_dotenv()
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("Variável de ambiente TELEGRAM_BOT_TOKEN não encontrada!")

# --- Variável global para manter a instância do bot ---
# Isso permite que a função de shutdown acesse a mesma instância criada no startup.
telegram_app: Application | None = None

# --- Lógica do Bot Telegram ---
def setup_telegram_bot() -> Application:
    """Configura e retorna a aplicação do bot do Telegram."""
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Adiciona os handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_feedback_button, pattern='^feedback_(yes|no)$'))
    application.add_handler(CallbackQueryHandler(button)) 
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, responder_pergunta))

    return application

# --- Lógica da API FastAPI ---
class QueryRequest(BaseModel):
    query: str
class QueryResponse(BaseModel):
    answer: str

# --- Combinação dos Serviços com Lifespan do FastAPI (O jeito correto) ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que executa ANTES do servidor iniciar (startup)
    global telegram_app
    logger.info("Configurando e inicializando o bot do Telegram...")
    telegram_app = setup_telegram_bot()
    
    # Inicializa a aplicação do bot (mas não bloqueia)
    await telegram_app.initialize()
    # Inicia o polling em uma tarefa de fundo
    await telegram_app.start()
    # Inicia o updater para começar a receber atualizações
    await telegram_app.updater.start_polling()
    
    logger.info("Bot do Telegram iniciado e rodando em segundo plano.")
    
    yield # Este é o ponto onde a API FastAPI fica rodando

    # Código que executa DEPOIS que o servidor é encerrado (shutdown)
    logger.info("Encerrando o bot do Telegram...")
    if telegram_app:
        # Para o updater de forma graciosa
        await telegram_app.updater.stop()
        # Para a aplicação
        await telegram_app.stop()
        # Limpa os recursos
        await telegram_app.shutdown()
    logger.info("Bot do Telegram encerrado.")

# Cria a aplicação FastAPI e associa o ciclo de vida (lifespan)
app = FastAPI(lifespan=lifespan)

# Define o endpoint da API
@app.post("/responder", response_model=QueryResponse)
async def responder_endpoint(request: QueryRequest):
    # ... (esta parte não muda)
    query = request.query
    if not query or not query.strip():
        raise HTTPException(status_code=400, detail="A query não pode ser vazia.")
    try:
        contexto = await get_contexto_rag(query)
        resposta = await gerar_resposta_rag(query, contexto)
        return QueryResponse(answer=resposta)
    except Exception as e:
        logger.error(f"Erro no endpoint /responder: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Erro interno ao processar a pergunta.")

# Adiciona um endpoint raiz para o Health Check do Render
@app.get("/")
def health_check():
    # ... (esta parte não muda)
    is_running = telegram_app.updater.running if telegram_app and telegram_app.updater else False
    return {"status": "ok", "bot_status": "running" if is_running else "stopped"}