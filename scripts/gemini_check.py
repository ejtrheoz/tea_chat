from google import genai
import os

client = genai.Client(api_key="AQ.Ab8RN6LUpRyRw67bK_it90ZJBAHgV0u42zFP8J8OdA7V6fgUcA")

text = "Hello world, this is a test"

response = client.models.embed_content(
    model="gemini-embedding-001",
    contents=text,
    config={
        "output_dimensionality": 1536
    }
)

embedding = response.embeddings[0].values

print(len(embedding))      # размер вектора
print(embedding[:5])       # первые значения