from openai import AzureOpenAI
import os

endpoint = "https://autocase-ai-resource.cognitiveservices.azure.com/"
deployment = "gpt-5-chat-2"
subscription_key = os.getenv("AZURE_API_KEY")
api_version = "2024-12-01-preview"

client = AzureOpenAI(
    api_version=api_version,
    azure_endpoint=endpoint,
    api_key=subscription_key,
)

print("Testing Azure OpenAI connection...")
try:
    response = client.chat.completions.create(
        messages=[
            {"role": "user", "content": "Say hello"}
        ],
        max_tokens=50,
        model=deployment
    )
    print("SUCCESS!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"ERROR: {e}")
