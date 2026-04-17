import os
from dotenv import load_dotenv

load_dotenv()

AWS_REGION = os.getenv("AWS_REGION", "eu-west-3")

DB_HOST = os.getenv("DB_HOST", "database-1-instance-1.ch0oww68op5p.eu-west-3.rds.amazonaws.com")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "iam_user")

CSV_PATH = os.getenv("CSV_PATH", "wikipedia_tea_articles.csv")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "gemini-embedding-001")
EMBEDDING_DIM = int(os.getenv("EMBEDDING_DIM", "1536"))

BEDROCK_LLM_MODEL_ID = os.getenv("BEDROCK_LLM_MODEL_ID", "global.amazon.nova-2-lite-v1:0")

VECTOR_TOP_K = int(os.getenv("VECTOR_TOP_K", "4"))
BM25_TOP_K = int(os.getenv("BM25_TOP_K", "4"))
