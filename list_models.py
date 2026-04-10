#!/usr/bin/env python3
"""List available Gemini models."""

import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

if not api_key:
    print("Error: No API key found")
    exit(1)

client = genai.Client(api_key=api_key)

print("Available Gemini models:")
print("=" * 60)

try:
    for model in client.models.list():
        print(f"- {model.name}")
        if hasattr(model, 'display_name'):
            print(f"  Display: {model.display_name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {model.supported_generation_methods}")
        print()
except Exception as e:
    print(f"Error listing models: {e}")
