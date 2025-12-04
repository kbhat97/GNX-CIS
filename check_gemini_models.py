"""
Check available Gemini models
"""
import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure with API key
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

print("🔍 Available Gemini Models:\n")
print("=" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"\n📦 Model: {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")

print("\n" + "=" * 80)
