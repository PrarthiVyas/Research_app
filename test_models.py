from dotenv import load_dotenv
import os
from google import genai

load_dotenv()

api_key = os.getenv('GOOGLE_API_KEY')
print(f"API Key loaded: {api_key[:10]}...")

client = genai.Client(api_key=api_key)

print("\nAvailable models:")
for model in client.models.list():
    print(f"  {model.name}")
