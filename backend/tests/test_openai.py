import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv(".env")

api_key = os.getenv("OPENAI_API_KEY")
print(f"API Key present: {bool(api_key)}")
if api_key:
    print(f"API Key start: {api_key[:10]}...")

try:
    from openai import OpenAI
    print("OpenAI module imported successfully")
except ImportError:
    print("Error: openai module not found. Run 'pip install openai'")
    sys.exit(1)

client = OpenAI(api_key=api_key)

try:
    print("Attempting to call OpenAI API...")
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": "Hello, are you working?"}
        ],
        max_tokens=10
    )
    print("Response received:")
    print(response.choices[0].message.content)
    print("✅ OpenAI connection successful!")
except Exception as e:
    print(f"❌ OpenAI call failed: {e}")
