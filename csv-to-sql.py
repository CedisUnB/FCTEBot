import os
import pandas as pd
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

csv_file = 'infosadmunb.csv'
data = pd.read_csv(csv_file)

db_connection = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME'),
    port=os.getenv('DB_PORT')
)

cursor = db_connection.cursor()

cursor.execute("DELETE FROM infosadmunb")

for index, row in data.iterrows():
    sql = """
    INSERT INTO infosadmunb (id, nome, texto, fonte, data_atualizacao)
    VALUES (%s, %s, %s, %s, %s)
    """
    values = (
        int(row['id']),
        str(row['nome']),
        str(row['texto']),
        str(row['fonte']),
        str(row['data_atualizacao']) if not pd.isna(row['data_atualizacao']) else None
    )
    cursor.execute(sql, values)

db_connection.commit()
print(f"✅ {cursor.rowcount} registros inseridos com sucesso no MySQL.")

cursor.close()
db_connection.close()