import json
import boto3
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from google import genai

from backend.database import get_db_connection
from backend.settings import (
    AWS_REGION,
    BEDROCK_LLM_MODEL_ID,
    BM25_TOP_K,
    EMBEDDING_DIM,
    GEMINI_API_KEY,
    GEMINI_EMBED_MODEL,
    VECTOR_TOP_K,
)

router = APIRouter(prefix="/rag", tags=["RAG"])

bedrock_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

class QueryRequest(BaseModel):
    query: str


def _invoke_nova(prompt: str, max_tokens: int = 350, temperature: float = 0.2) -> str:
    response = bedrock_client.converse(
        modelId=BEDROCK_LLM_MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}],
            }
        ],
        inferenceConfig={
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    )
    return response["output"]["message"]["content"][0]["text"].strip()


def rewrite_query(original_query: str) -> str:
    prompt = (
        "You are rewriting a user query for retrieval over Wikipedia tea articles. "
        "Keep it concise and retrieval-friendly for BM25 and semantic search. "
        "Return only the rewritten query.\n\n"
        f"User query: {original_query}"
    )
    try:
        return _invoke_nova(prompt, max_tokens=90, temperature=0.0)
    except Exception as e:
        print(f"Error rewriting query with Bedrock Nova: {e}. Falling back to original query.")
        return original_query


def get_embedding(text: str) -> list[float]:
    if not GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY is empty. Set it in your .env file.")

    response = gemini_client.models.embed_content(
        model=GEMINI_EMBED_MODEL,
        contents=text,
        config={"output_dimensionality": EMBEDDING_DIM},
    )
    return response.embeddings[0].values


def generate_final_answer(user_query: str, rewritten_query: str, context_blocks: list[str]) -> str:
    context_text = "\n\n".join(context_blocks)
    prompt = (
        "You are a helpful assistant answering questions using only the provided context from Wikipedia tea articles. "
        "If the context is insufficient, clearly say that the answer is not found in the retrieved context.\n\n"
        f"Original user query:\n{user_query}\n\n"
        f"Rewritten retrieval query:\n{rewritten_query}\n\n"
        f"Retrieved context:\n{context_text}\n\n"
        "Give a concise factual answer."
    )
    return _invoke_nova(prompt, max_tokens=420, temperature=0.2)


@router.post("/search")
def hybrid_search(req: QueryRequest, request: Request):
    conn = None
    cur = None
    try:
        rewritten_query = rewrite_query(req.query)
        query_embedding = get_embedding(rewritten_query)
        embedding_str = json.dumps(query_embedding)

        conn = get_db_connection()
        cur = conn.cursor()
        sql_query = """
            SELECT id, url, content, embedding <=> %s::vector AS vector_dist
            FROM tea_articles
            ORDER BY vector_dist ASC
            LIMIT %s;
        """

        cur.execute(sql_query, (embedding_str, VECTOR_TOP_K))
        vector_results = cur.fetchall()

        context_blocks = []
        for row in vector_results:
            context_blocks.append(
                f"[PGVECTOR] URL: {row[1]}\nContent: {row[2]}"
            )

        bm25_retriever = request.app.state.bm25_retriever
        if bm25_retriever is not None:
            bm25_retriever.k = BM25_TOP_K
            langchain_docs = bm25_retriever.invoke(rewritten_query)
            for doc in langchain_docs:
                context_blocks.append(
                    f"[BM25] URL: {doc.metadata.get('url')}\nContent: {doc.page_content}"
                )

        answer = generate_final_answer(req.query, rewritten_query, context_blocks)
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()
