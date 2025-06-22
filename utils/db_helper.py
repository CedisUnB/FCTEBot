# utils/db_helper.py
import os
import mysql.connector
from dotenv import load_dotenv
from utils.logger import setup_logging # Supondo que você quer logar aqui também
import logging

load_dotenv()
setup_logging() # Configura o logger se ainda não estiver
logger = logging.getLogger(__name__)

DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = 'fctebot'

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            return connection
    except mysql.connector.Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None

def save_feedback(chat_id: int, helped: bool, suggestion: str = None) -> bool: # Adicionado suggestion
    connection = get_db_connection()
    if not connection:
        return False

    cursor = connection.cursor()
    # Modificado para incluir a sugestão
    sql = "INSERT INTO feedbacks (chat_id, helped, suggestion) VALUES (%s, %s, %s)"
    values = (chat_id, helped, suggestion)

    try:
        cursor.execute(sql, values)
        connection.commit()
        logger.info(f"Feedback salvo para chat_id {chat_id}: helped={helped}, suggestion='{suggestion if suggestion else ''}'")
        return True
    except mysql.connector.Error as e:
        logger.error(f"Erro ao salvar feedback: {e}")
        connection.rollback()
        return False
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    # Teste rápido (opcional)
    if not DB_PASSWORD:
        print("Variável de ambiente DB_PASSWORD não definida. Não é possível testar.")
    else:
        print("Testando salvar feedback...")
        test_chat_id = 12345
        if save_feedback(test_chat_id, True):
            print(f"Feedback (Sim) salvo para chat_id {test_chat_id}")
        else:
            print(f"Falha ao salvar feedback (Sim) para chat_id {test_chat_id}")

        if save_feedback(test_chat_id, False, "O bot não entendeu minha pergunta sobre prazos."):
            print(f"Feedback (Não com sugestão) salvo para chat_id {test_chat_id}")
        else:
            print(f"Falha ao salvar feedback (Não com sugestão) para chat_id {test_chat_id}")

        if save_feedback(test_chat_id, False):
            print(f"Feedback (Não sem sugestão) salvo para chat_id {test_chat_id}")
        else:
            print(f"Falha ao salvar feedback (Não sem sugestão) para chat_id {test_chat_id}")