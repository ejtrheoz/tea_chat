from dotenv import load_dotenv

load_dotenv()

import boto3

client = boto3.client("bedrock-runtime", region_name="eu-west-3")

model_id = "global.amazon.nova-2-lite-v1:0"

response = client.converse(
    modelId=model_id,
    messages=[
        {
            "role": "user",
            "content": [
                {"text": "Объясни что такое LLM простыми словами"}
            ]
        }
    ],
    inferenceConfig={
        "maxTokens": 300,
        "temperature": 0.7
    }
)

print(response["output"]["message"]["content"][0]["text"])