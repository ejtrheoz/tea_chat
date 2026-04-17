import boto3
import psycopg2
from backend.settings import AWS_REGION, DB_HOST, DB_NAME, DB_PORT, DB_USER

def get_db_connection():
    # Fetch AWS RDS token
    rds = boto3.client("rds", region_name=AWS_REGION)
    token = rds.generate_db_auth_token(
        DBHostname=DB_HOST,
        Port=DB_PORT,
        DBUsername=DB_USER
    )
    # Connect to PostgreSQL
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=token,
        sslmode="require"
    )
