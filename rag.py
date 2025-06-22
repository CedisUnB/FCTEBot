# rag.py
import os
import time
import logging
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from google import genai
import google.api_core.exceptions
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

load_dotenv()
logger = logging.getLogger(__name__)

# Inicializar Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
spec = ServerlessSpec(cloud="aws", region="us-east-1")
index_name = "infosadmunbbot"
myindex = pc.Index(index_name)
time.sleep(1)

# Inicializar modelo de embeddings (Google GenAI)
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Vector Store com campo texto
vectorstore = PineconeVectorStore(
    index=myindex,
    embedding=embed_model,
    text_key="texto"
)

# Inicializar cliente Gemini para geração de resposta
genai_client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))

system_message = (
    "Você é um(a) secretário(a) prestativo(a) e respeitoso(a) da universidade. "
    "Responda às perguntas com clareza e educação, sempre utilizando uma linguagem informal e acolhedora. "
    "Se não souber a resposta, encaminhe o número da secretaria (61) 3107-8901, e o horário de funcionamento de segunda a sexta-feira das 07h às 19h. "
    "Inclua no final da resposta a fonte da informação e a data de atualização conforme disponível no contexto."
)

def get_relevant_chunk(query, vectorstore):
    results = vectorstore.similarity_search(query, k=20)
    if results:
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
    return "Nenhum resultado relevante encontrado."


def make_prompt(query, context):
    return (
        f"{system_message}\n\n"
        f"IMPORTANTE: Use a tag HTML <b> para negrito ao invés de *texto*, use <a> para links e as listas faça com '-', evite markdown na resposta.\n\n"
        f"Com base nas informações abaixo, responda à pergunta de forma precisa e clara. "
        f"Sempre que possível, cite a fonte e a data de atualização da informação ao final da resposta e caso a fonte já tenha sido mencionada, não repetir:\n\n"
        f"{context}\n\n"
        f"Pergunta: {query}\n\n"
    )

def log_before_retry(retry_state):
    logger.warning(
        f"Rate limit atingido ou erro na API. Tentando novamente em "
        f"{retry_state.next_action.sleep:.2f} segundos... "
        f"(Tentativa {retry_state.attempt_number})"
    )

@retry(
    wait=wait_exponential(multiplier=1, min=2, max=60), 
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(google.api_core.exceptions.ResourceExhausted), 
    before_sleep=log_before_retry, 
    reraise=True 
)
def gen_answer(prompt):
    logger.info("Gerando resposta com a API do Gemini...")
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash-lite",
        contents=prompt
    )
    logger.info("Resposta gerada com sucesso.")
    return response.text.strip()


def responder(query):
    try:
        context = get_relevant_chunk(query, vectorstore)
        prompt = make_prompt(query, context)
        resposta = gen_answer(prompt)
        return resposta
    except google.api_core.exceptions.ResourceExhausted:
        logger.error(f"Falha ao gerar resposta para '{query}' após todas as tentativas devido a rate limit.")
        return "🤖 Desculpe, estou com muitas solicitações no momento. Por favor, tente novamente em alguns instantes."
    except Exception as e:
        logger.error(f"Um erro inesperado ocorreu na função responder para a query '{query}': {e}", exc_info=True)
        return "❌ Ocorreu um erro inesperado ao processar sua pergunta. Por favor, tente novamente."

if __name__ == "__main__":
    pergunta = input("Digite sua pergunta: ").strip()
    resposta = responder(pergunta)
    print("\nResposta da IA Gemini:\n")
    print(resposta)
