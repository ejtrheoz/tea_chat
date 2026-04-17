import time
import boto3
import psycopg2
from dotenv import load_dotenv

load_dotenv()

HOST = "database-1-instance-1.ch0oww68op5p.eu-west-3.rds.amazonaws.com"
PORT = 5432
DBNAME = "postgres"
USER = "iam_user"   # НЕ postgres
REGION = "eu-west-3"

# создаём IAM токен (аналог aws rds generate-db-auth-token)
rds = boto3.client("rds", region_name=REGION)

token = rds.generate_db_auth_token(
    DBHostname=HOST,
    Port=PORT,
    DBUsername=USER
)

# подключение
start_time = time.time()
conn = psycopg2.connect(
    host=HOST,
    port=PORT,
    database=DBNAME,
    user=USER,
    password=token,
    sslmode="require"
)
end_time = time.time()

print(f"Connected! (took {end_time - start_time:.4f} seconds)")

cur = conn.cursor()
cur.execute("SELECT version();")
print(cur.fetchone())

cur.close()
conn.close()