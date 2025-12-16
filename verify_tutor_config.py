import sys
import os
from app.services.tutor.ai_tutor import AITutor

print("--- DIAGNOSTIC START ---")
tutor = AITutor()

if not tutor.llm_client:
    print("FAIL: LLM Client is None.")
    sys.exit(1)

print("Attempting to list available models...")
try:
    response = tutor.llm_client.models.list()
    print("SUCCESS: Retrieved specific model list.")
    ids = [m.id for m in response.data]
    print(f"Available models: {ids[:10]}... (Total {len(ids)})")
    
    # Check for common chat models
    chat_models = [m for m in ids if "gpt" in m]
    print(f"Chat models found: {chat_models}")
    
except Exception as e:
    print(f"FAIL: List models call failed with error: {e}")
    sys.exit(1)
