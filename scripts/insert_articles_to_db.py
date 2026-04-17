import os
import boto3
import psycopg2
import pandas as pd
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
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AQ.Ab8RN6LUpRyRw67bK_it90ZJBAHgV0u42zFP8J8OdA7V6fgUcA")
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
    print("Reading CSV file...")
    # Читаем CSV таблицу
    df = pd.read_csv("wikipedia_tea_articles.csv")

    # Получаем токен для подключения к БД
    print("Generating RDS auth token...")
    rds = boto3.client("rds", region_name=REGION)
    token = rds.generate_db_auth_token(
        DBHostname=HOST,
        Port=PORT,
        DBUsername=USER
    )

    # Подключаемся к базе данных
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
        
        # Создаем таблицу, если она не существует
        cur.execute("""
            CREATE TABLE IF NOT EXISTS tea_articles (
                id SERIAL PRIMARY KEY,
                url TEXT,
                content TEXT,
                embedding vector(1536)
            );
        """)
        conn.commit()
        print("Table 'tea_articles' ensures to exist.")

        # Проходим по строкам датафрейма
        for index, row in df.iterrows():
            url = row['url']
            title = str(row['title'])
            summary = str(row['summary'])
            
            # Объединяем title и summary в content (full_text игнорируется)
            content = f"{title}\n\n{summary}"
            
            print(f"[{index+1}/{len(df)}] Processing article: '{title}'...")
            
            try:
                # Генерируем эмбеддинг
                embedding = get_embedding(content)
                
                # Вставляем данные
                cur.execute(
                    "INSERT INTO tea_articles (url, content, embedding) VALUES (%s, %s, %s::vector);",
                    (url, content, embedding)
                )
                
                # Делаем коммит каждые 10 записей или в конце
                if (index + 1) % 10 == 0:
                    conn.commit()
                    
            except Exception as e:
                print(f"Error processing row {index+1} ({title}): {e}")
                conn.rollback() # Откатываем транзакцию в случае ошибки на текущей строке, но продолжаем итерацию

        # Финальный коммит для оставшихся записей
        conn.commit()
        print("Insertion finished successfully!")
        
    except Exception as e:
        print(f"A critical error occurred: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    main()
