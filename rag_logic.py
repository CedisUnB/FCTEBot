import os
import logging
import asyncio
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from google import genai
import google.api_core.exceptions
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

logger = logging.getLogger(__name__)

# --- Configurações Globais Seguras ---
load_dotenv()
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

try:
    # Pinecone
    pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    spec = ServerlessSpec(cloud="aws", region="us-east-1")
    index_name = "infosadmunbbot"
    myindex = pc.Index(index_name)

    # Google GenAI Embeddings e LangChain VectorStore
    os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
    embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vectorstore = PineconeVectorStore(index=myindex, embedding=embed_model, text_key="texto")

    genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
    logger.info("Serviços de Pinecone e Google GenAI inicializados com sucesso.")
except Exception as e:
    logger.critical(f"Falha na inicialização dos serviços. Erro: {e}", exc_info=True)
    raise

system_message = (
    "Você é um(a) secretário(a) prestativo(a) e respeitoso(a) da universidade. "
    "Responda às perguntas com clareza e educação, sempre utilizando uma linguagem informal e acolhedora. "
    "Se não souber a resposta, encaminhe o número da secretaria (61) 3107-8901, e o horário de funcionamento de segunda a sexta-feira das 07h às 19h. "
    "Inclua no final da resposta a fonte da informação e a data de atualização conforme disponível no contexto."
)

def make_prompt(query: str, context: str) -> str:
  return (
        f"{system_message}\n\n"
        "IMPORTANTE: Use a tag HTML <b> para negrito ao invés de *texto*, use <a> para links e as listas faça com '-', evite markdown na resposta.\n\n"
        f"Com base nas informações abaixo, responda à pergunta de forma precisa e clara. "
        f"Sempre que possível, cite a fonte e a data de atualização da informação ao final da resposta e caso a fonte já tenha sido mencionada, não repetir:\n\n"
        f"{context}\n\n"
        f"Pergunta: {query}\n\n"
    )

def _get_relevant_chunks_sync(query: str) -> str:
    logger.info(f"Buscando chunks para a query: '{query[:30]}...'")
      # Usamos o método síncrono aqui, pois a função toda já é síncrona
    results = vectorstore.similarity_search(query, k=30)
    if not results:
        return "Nenhum resultado relevante encontrado."
    
    # Processamento dos resultados (sem alterações)
    partes = []
    fontes_vistas = set()
    for doc in results:
        meta = doc.metadata
        fonte = meta.get('fonte', 'Fonte não informada')
        data = meta.get('data_atualizacao', 'Data não disponível')
        texto = doc.page_content
        if fonte not in fontes_vistas:
            partes.append(f"{texto}\n(Fonte: {fonte} | Atualizado em: {data})")
            fontes_vistas.add(fonte)
        else:
            partes.append(texto)
    contexto = "\n\n---\n\n".join(partes)
    return contexto

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted),
    before_sleep=lambda s: logger.warning(f"Rate limit atingido. Tentando novamente... (Tentativa {s.attempt_number})")
)

def _generate_content_sync(prompt: str) -> str:
    """Função SÍNCRONA para gerar conteúdo com o Gemini."""
    logger.info("Gerando resposta com a API do Gemini...")
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    logger.info("Resposta gerada com sucesso.")
    return response.text.strip()

async def get_contexto_rag(query: str) -> str:
    return await asyncio.to_thread(_get_relevant_chunks_sync, query)

async def gerar_resposta_rag(query: str, contexto: str) -> str:
    prompt_final = make_prompt(query, contexto)
    return await asyncio.to_thread(_generate_content_sync, prompt_final)