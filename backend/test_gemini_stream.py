import httpx
import json
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import SessionLocal
from models.provider import Provider
from utils.security import decrypt_api_key
from providers import ProviderRegistry

async def test_stream():
    db = SessionLocal()
    try:
        provider = db.query(Provider).filter(Provider.id == 5).first()
        api_key = decrypt_api_key(provider.api_key) if provider.api_key else None
        
        provider_class = ProviderRegistry.get(provider.type)
        provider_instance = provider_class(api_key=api_key)
        
        # Use the provider's message format
        messages = [{"role": "user", "content": "Hi"}]
        
        print("Starting stream test...")
        chunk_count = 0
        full_text = ""
        
        async for chunk in provider_instance.stream(messages=messages, model="gemini-2.5-flash"):
            chunk_count += 1
            full_text += chunk
            print(f"Chunk {chunk_count}: {repr(chunk[:100])}")
            if chunk_count >= 10:
                break
        
        print(f"\nTotal chunks: {chunk_count}")
        print(f"Full text: {repr(full_text[:500])}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_stream())
