import boto3
import psycopg2
from google import genai
from dotenv import load_dotenv

load_dotenv()

# --- Настройки БД ---
HOST = "database-1-instance-1.ch0oww68op5p.eu-west-3.rds.amazonaws.com"
PORT = 5432
DBNAME = "postgres"
USER = "iam_user"
REGION = "eu-west-3"

# --- Настройки Gemini ---
# Желательно вынести API ключ в .env
GEMINI_API_KEY = "AQ.Ab8RN6LUpRyRw67bK_it90ZJBAHgV0u42zFP8J8OdA7V6fgUcA"
client = genai.Client(api_key=GEMINI_API_KEY)

def get_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text,
        config={
            "output_dimensionality": 1536
        }
    )
    return response.embeddings[0].values

def main():
    # 1. Генерируем эмбеддинг для тестовой строки
    text_to_insert = "Hello world, this is a test embedding insertion"
    print(f"Generating embedding for: '{text_to_insert}'...")
    embedding = get_embedding(text_to_insert)
    print(f"Generated embedding of length {len(embedding)}")

    # 2. Получаем токен для подключения к БД
    rds = boto3.client("rds", region_name=REGION)
    token = rds.generate_db_auth_token(
        DBHostname=HOST,
        Port=PORT,
        DBUsername=USER
    )

    # 3. Подключаемся к базе данных
    print("Connecting to the database...")
    conn = psycopg2.connect(
        host=HOST,
        port=PORT,
        database=DBNAME,
        user=USER,
        password=token,
        sslmode="require"
    )
    
    cur = conn.cursor()

    try:
        # Убедимся, что расширение pgvector установлено
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        
        # Создаем тестовую таблицу, если она не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tea_articles (
                id SERIAL PRIMARY KEY,
                url TEXT,
                content TEXT,
                embedding vector(1536)
            );
        """)
        
        # Вставляем данные (используем приведение типа ::vector)
        print("Inserting data into test_embeddings table...")
        cur.execute(
            "INSERT INTO test_embeddings (content, embedding) VALUES (%s, %s::vector) RETURNING id;",
            (text_to_insert, embedding)
        )
        
        inserted_id = cur.fetchone()[0]
        conn.commit()
        print(f"Successfully inserted row with ID: {inserted_id}")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
