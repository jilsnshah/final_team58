import os
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load environment variables
backend_env_path = Path(__file__).parent.parent.parent / '.env'
if backend_env_path.exists():
    load_dotenv(backend_env_path)
    print(f"✅ Loaded environment variables from {backend_env_path}\n")

# Configure API
api_key = os.getenv('GOOGLE_API_KEY')
if not api_key:
    print("❌ GOOGLE_API_KEY not found")
    exit(1)

genai.configure(api_key=api_key)

print("📋 Available Gemini models that support generateContent:\n")
print("-" * 80)

for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"✅ {model.name}")
        print(f"   Display Name: {model.display_name}")
        print(f"   Description: {model.description}")
        print(f"   Supported Methods: {', '.join(model.supported_generation_methods)}")
        print("-" * 80)
