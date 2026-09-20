import json
import re
from typing import Dict, Any, Optional
import httpx
from backend.app.core.config import settings
from backend.app.services.llm.base import BaseLLMProvider

class OllamaProvider(BaseLLMProvider):
    def __init__(self, base_url: Optional[str] = None, model: Optional[str] = None):
        self.base_url = (base_url or settings.OLLAMA_BASE_URL).rstrip("/")
        self.model = model or settings.OLLAMA_MODEL

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None, temperature: float = 0.4) -> str:
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }
        if system_prompt:
            payload["system"] = system_prompt

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                res = await client.post(f"{self.base_url}/api/generate", json=payload)
                if res.status_code != 200:
                    raise ValueError(f"Ollama error ({res.status_code}): {res.text}")
                data = res.json()
                return data.get("response", "")
        except Exception as e:
            raise ValueError(f"Ollama connection failed ({self.base_url}): {str(e)}")

    async def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Dict[str, Any]:
        text = await self.generate_text(
            prompt=prompt + "\n\nCRITICAL: Respond ONLY with a valid JSON object.",
            system_prompt=system_prompt,
            temperature=0.2
        )
        cleaned = text.strip()
        if cleaned.startswith("```json"):
            cleaned = cleaned[7:]
        if cleaned.startswith("```"):
            cleaned = cleaned[3:]
        if cleaned.endswith("```"):
            cleaned = cleaned[:-3]

        try:
            return json.loads(cleaned.strip())
        except Exception:
            match = re.search(r'\{.*\}', cleaned, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            raise ValueError(f"Failed to parse JSON from Ollama response: {text}")
