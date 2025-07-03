# utils/db_helper.py
import os
import mysql.connector
from dotenv import load_dotenv
from utils.logger import setup_logging
import logging

load_dotenv()
setup_logging()
logger = logging.getLogger(__name__)

DB_HOST = os.getenv('DB_HOST')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
DB_PORT = int(os.getenv('DB_PORT', 4000))

def get_db_connection():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            port=DB_PORT,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        if connection.is_connected():
            # --- ADICIONA ESTE BLOCO PARA DEFINIR O FUSO HORÁRIO DA SESSÃO ---
            try:
                cursor = connection.cursor()
                cursor.execute("SET time_zone = 'America/Sao_Paulo'")
                # Não precisa de connection.commit() aqui, pois SET time_zone é um comando de configuração
                cursor.close()
                logger.info("Fuso horário da sessão do banco de dados definido para 'America/Sao_Paulo'.")
            except mysql.connector.Error as e:
                logger.error(f"Erro ao definir o fuso horário da sessão: {e}")
                connection.close() # Fechar a conexão se não conseguir definir o fuso horário
                return None
            # --- FIM DO BLOCO DE FUSO HORÁRIO ---

            return connection
    except mysql.connector.Error as e:
        logger.error(f"Erro ao conectar ao MySQL: {e}")
        return None

def save_feedback(chat_id: int, helped: bool, suggestion: str = None) -> bool:
    connection = get_db_connection()
    if not connection:
        return False

    cursor = connection.cursor()
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