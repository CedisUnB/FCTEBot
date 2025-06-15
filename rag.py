import os
import time
from dotenv import load_dotenv
from pinecone import Pinecone, ServerlessSpec
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from google import genai

load_dotenv()

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

chat_history = []

def get_relevant_chunk(query, vectorstore):
    results = vectorstore.similarity_search(query, k=10)  # Pode ajustar k se quiser
    if results:
        partes = []
        fontes_vistas = set()
        for doc in results:
            meta = doc.metadata
            fonte = meta.get('fonte', 'Fonte não informada')
            data = meta.get('data_atualizacao', 'Data não disponível')
            texto = doc.page_content
            
            # Evitar repetir fonte na montagem do contexto
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
        f"IMPORTANTE: Use a tag HTML <b> para negrito ao invés de **texto**, use <a> para links e as listas faça com '-', evite markdown na resposta.\n\n"
        f"Com base nas informações abaixo, responda à pergunta de forma precisa e clara. "
        f"Sempre que possível, cite a fonte e a data de atualização da informação ao final da resposta e caso a fonte já tenha sido mencionada, não repetir:\n\n"
        f"{context}\n\n"
        f"Pergunta: {query}\n\n"
    )

def gen_answer(prompt):
    response = genai_client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )
    return response.text.strip()

def responder(query):
    context = get_relevant_chunk(query, vectorstore)
    prompt = make_prompt(query, context)
    resposta = gen_answer(prompt)
    return resposta

if __name__ == "__main__":
    pergunta = input("Digite sua pergunta: ").strip()
    resposta = responder(pergunta)
    print("\nResposta da IA Gemini:\n")
    print(resposta)
