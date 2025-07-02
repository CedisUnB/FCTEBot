# utils/api_helper.py
import httpx
import logging

logger = logging.getLogger(__name__)
RAG_API_URL = "http://127.0.0.1:8000/responder"

async def call_rag_api(query: str) -> str:
    """
    Faz uma chamada assíncrona para o serviço RAG FastAPI.
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                RAG_API_URL,
                json={"query": query},
                timeout=120.0  # Timeout generoso para a API do GenAI
            )
            response.raise_for_status()  # Lança exceção para erros HTTP (4xx, 5xx)
            data = response.json()
            return data.get("answer", "Não foi possível obter uma resposta.")

    except httpx.HTTPStatusError as e:
        logger.error(f"Erro de status da API RAG: {e.response.status_code} - {e.response.text}")
        if e.response.status_code == 503:
            return "🤖 Desculpe, estou com muitas solicitações no momento. Por favor, tente novamente em alguns instantes."
        return "❌ Ocorreu um erro ao me comunicar com o serviço de inteligência. Por favor, avise o administrador."
    except httpx.RequestError as e:
        logger.error(f"Erro de conexão com a API RAG: {e}")
        return "❌ Não consegui me conectar ao serviço de inteligência. Por favor, verifique se ele está no ar e tente novamente."
    except Exception as e:
        logger.error(f"Erro inesperado ao chamar a API RAG: {e}", exc_info=True)
        return "❌ Ocorreu um erro inesperado ao processar sua pergunta."