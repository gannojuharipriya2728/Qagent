import asyncio
import os
import sys
import time
import httpx
from pathlib import Path
from dotenv import load_dotenv

root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))
load_dotenv(dotenv_path=root_dir / ".env")

from backend.app.core.config import settings

async def main():
    print(f"Testing OpenRouter API key: {settings.OPENROUTER_API_KEY[:10]}...")
    print(f"Model: {settings.OPENROUTER_MODEL}")
    
    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY.strip()}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5173",
        "X-Title": "QAgent"
    }

    # 1. Quick test
    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": "You are a JSON assistant. Output strictly valid JSON."},
            {"role": "user", "content": 'Extract {"code": "IT701PC", "title": "Information Security"} from this text: Course IT701PC Information Security'}
        ],
        "temperature": 0.1,
        "max_tokens": 512
    }

    t0 = time.time()
    print(f"Sending quick request at {time.strftime('%X')}...")
    async with httpx.AsyncClient(timeout=45.0) as client:
        try:
            resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            dt = time.time() - t0
            print(f"Status Code: {resp.status_code} in {dt:.2f}s")
            print("Response:")
            print(resp.text[:600])
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
