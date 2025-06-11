import datetime
import os
import time
import mysql.connector
import pandas as pd
from dotenv import load_dotenv
from tqdm.auto import tqdm
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pinecone import Pinecone, ServerlessSpec

# Carrega variáveis do .env
load_dotenv()

# Configurações do Pinecone
api_key = os.getenv("PINECONE_API_KEY")
pc = Pinecone(api_key=api_key)
spec = ServerlessSpec(cloud="aws", region="us-east-1")

index_name = "infosadmunbbot"
existing_indexes = [index["name"] for index in pc.list_indexes()]

# Cria índice caso ainda não exista
if index_name not in existing_indexes:
    pc.create_index(
        name=index_name,
        dimension=768,
        metric='dotproduct',
        spec=spec
    )
    while not pc.describe_index(index_name).status['ready']:
        time.sleep(1)

index = pc.Index(index_name)
time.sleep(1)

# Conecta ao banco de dados MySQL
db_connection = mysql.connector.connect(
    host='localhost',
    user='root',
    password=os.getenv('DB_PASSWORD'),
    database='fctebot'
)
cursor = db_connection.cursor()

# Inicializa modelo de embeddings
os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")
embed_model = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

# Consulta os dados da tabela
def fetch_data():
    query = "SELECT id, nome, texto, fonte, data_atualizacao FROM infosadmunb"
    cursor.execute(query)
    columns = [desc[0] for desc in cursor.description]
    data = pd.DataFrame(cursor.fetchall(), columns=columns)
    return data

# Sincroniza com Pinecone
def sync_with_pinecone(data):
    batch_size = 100
    total_batches = (len(data) + batch_size - 1) // batch_size

    for i in tqdm(range(0, len(data), batch_size), desc="Processando Lotes", unit='lote', total=total_batches):
        i_end = min(len(data), i + batch_size)
        batch = data.iloc[i:i_end]

        ids = [str(row['id']) for _, row in batch.iterrows()]
        texts = [row['texto'] for _, row in batch.iterrows()]
        embeds = embed_model.embed_documents(texts)

        metadata = [
            {
                'nome': row['nome'],
                'fonte': row['fonte'],
                'data_atualizacao': row['data_atualizacao'].strftime('%Y-%m-%d') if isinstance(row['data_atualizacao'], (pd.Timestamp, datetime.date)) else str(row['data_atualizacao']),
                'texto': row['texto'],
            }
            for _, row in batch.iterrows()
        ]

        with tqdm(total=len(ids), desc="Enviando vetores", unit='vetor') as upsert_bar:
            index.upsert(vectors=zip(ids, embeds, metadata))
            upsert_bar.update(len(ids))

# Executa tudo
def main():
    data = fetch_data()
    sync_with_pinecone(data)

if __name__ == "__main__":
    main()

# Finaliza conexões
cursor.close()
db_connection.close()
