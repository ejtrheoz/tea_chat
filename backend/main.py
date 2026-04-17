import pandas as pd
from fastapi import FastAPI
from contextlib import asynccontextmanager
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from backend.routers import auth, rag
from backend.settings import BM25_TOP_K, CSV_PATH

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading BM25 Retriever into memory...")
    try:
        # Читаем данные для BM25
        df = pd.read_csv(CSV_PATH)
        
        # Создаем документы для Langchain
        documents = []
        for index, row in df.iterrows():
            title = str(row['title'])
            summary = str(row['summary'])
            url = str(row['url'])
            content = f"{title}\n\n{summary}"
            
            docs = Document(page_content=content, metadata={"url": url, "id": index})
            documents.append(docs)
            
        # Инициализация BM25Retriever
        bm25_retriever = BM25Retriever.from_documents(documents)
        bm25_retriever.k = BM25_TOP_K
        
        app.state.bm25_retriever = bm25_retriever
        print("BM25 Retriever loaded successfully!")
    except Exception as e:
        print(f"Error loading BM25 Retriever: {e}")
        app.state.bm25_retriever = None
        
    yield
    print("Shutting down, releasing resources...")

app = FastAPI(title="Tea Knowledge Base API", lifespan=lifespan)

# Подключаем модули с префиксами /auth и /rag
app.include_router(auth.router)
app.include_router(rag.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Modular Tea Knowledge Base API!"}
