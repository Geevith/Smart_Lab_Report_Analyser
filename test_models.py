import os
from dotenv import load_dotenv
load_dotenv('.env')

from google import genai

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

print("Available models:")
for model in client.models.list():
    if "flash" in model.name.lower():
        print(model.name)
