import json
import re
import asyncio
import logging
from typing import Dict, Any, Optional, List
import httpx
from app.core.config import settings
from app.services.llm.base import BaseLLMProvider

logger = logging.getLogger("qagent.nvidia_provider")

class NvidiaProvider(BaseLLMProvider):
    """
    NVIDIA NIM API Provider.
    Directly interfaces with NVIDIA's API endpoint (https://integrate.api.nvidia.com/v1/chat/completions)
    for high-speed, grounded question generation using models such as
    nvidia/nemotron-3.5-lightning-30b-a3b.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        resolved_api_key = (
            api_key
            if api_key is not None
            else settings.NVIDIA_API_KEY
        )
        self.provider_name = "nvidia"
        self.api_key = resolved_api_key.strip() if resolved_api_key else ""
        self.model = model or settings.NVIDIA_MODEL
        self.base_url = (base_url or settings.NVIDIA_BASE_URL).rstrip("/")
        self.endpoint = f"{self.base_url}/chat/completions"

    def _validate_configuration(self):
        if not self.api_key or not self.api_key.strip():
            raise ValueError(
                "NVIDIA_API_KEY is required for NvidiaProvider. Please set NVIDIA_API_KEY in the environment."
            )

    def _get_headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        top_p: float = 0.9,
        max_tokens: int = 4096,
        max_retries: int = 3,
        response_format: Optional[Dict[str, str]] = None
    ) -> str:
        self._validate_configuration()

        messages: List[Dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
            "max_tokens": max_tokens
        }
        if response_format:
            payload["response_format"] = response_format

        headers = self._get_headers()
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=httpx.Timeout(90.0, connect=15.0)) as client:
                    response = await asyncio.wait_for(
                        client.post(
                            self.endpoint,
                            headers=headers,
                            json=payload
                        ),
                        timeout=90.0
                    )

                    if response.status_code == 200:
                        data = response.json()
                        choices = data.get("choices", [])
                        if not choices:
                            raise ValueError("NVIDIA NIM API returned an empty choices array.")

                        msg = choices[0].get("message") or {}
                        content = msg.get("content")
                        if content is None:
                            content = msg.get("reasoning") or choices[0].get("text") or ""
                        elif isinstance(content, list):
                            content = "".join(
                                part.get("text", "") if isinstance(part, dict) else str(part)
                                for part in content
                            )

                        content_str = str(content or "").strip()
                        if not content_str:
                            raise ValueError("NVIDIA NIM API returned empty response content.")
                        return content_str

                    error_text = response.text[:300]
                    if response.status_code in [429, 500, 502, 503, 504]:
                        wait_time = 2 ** attempt
                        logger.warning(
                            f"NVIDIA NIM API status {response.status_code}. Retrying attempt {attempt}/{max_retries} in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        last_error = ValueError(f"NVIDIA NIM API Error ({response.status_code}): {error_text}")
                        continue

                    raise ValueError(f"NVIDIA NIM API Error ({response.status_code}): {error_text}")

            except (httpx.TimeoutException, asyncio.TimeoutError) as e:
                logger.warning(f"NVIDIA NIM API request timed out (attempt {attempt}/{max_retries}).")
                last_error = TimeoutError(f"NVIDIA NIM API timed out: {e}")
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)
            except Exception as e:
                if "NVIDIA NIM API Error" in str(e):
                    raise
                logger.warning(f"NVIDIA NIM API connection error (attempt {attempt}/{max_retries}): {e}")
                last_error = e
                if attempt < max_retries:
                    await asyncio.sleep(2 ** attempt)

        raise last_error or RuntimeError("NVIDIA NIM API failed after multiple retries.")

    async def generate_json(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        json_system_prompt = (
            (system_prompt or "You are an expert academic assessment AI.")
            + "\nCRITICAL REQUIREMENT: Output MUST be a strictly valid JSON object. Do not include markdown preamble, commentary, or text outside the JSON structure."
        )

        raw_text = await self.generate_text(
            prompt=prompt,
            system_prompt=json_system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
        return self._extract_json_from_text(raw_text)

    def _try_parse_or_repair(self, s: str) -> Optional[Any]:
        if not s:
            return None
        s_clean = s.strip()
        try:
            return json.loads(s_clean)
        except Exception:
            pass

        cleaned = re.sub(r',\s*([\}\]])', r'\1', s_clean)
        try:
            return json.loads(cleaned)
        except Exception:
            pass

        stack = []
        in_quote = False
        escape = False
        for char in cleaned:
            if escape:
                escape = False
                continue
            if char == '\\':
                escape = True
                continue
            if char == '"':
                in_quote = not in_quote
                continue
            if not in_quote:
                if char in '{[':
                    stack.append('}' if char == '{' else ']')
                elif char in '}]':
                    if stack and stack[-1] == char:
                        stack.pop()

        repaired = cleaned
        if in_quote:
            repaired += '"'
        repaired = re.sub(r',\s*$', '', repaired)
        while stack:
            repaired += stack.pop()

        repaired = re.sub(r',\s*([\}\]])', r'\1', repaired)
        try:
            return json.loads(repaired)
        except Exception:
            return None

    def _extract_json_from_text(self, text: Optional[str]) -> Dict[str, Any]:
        if not text:
            raise ValueError("Empty or null response received from NVIDIA NIM LLM.")
        raw_str = str(text).strip()

        direct = self._try_parse_or_repair(raw_str)
        if isinstance(direct, (dict, list)):
            return direct

        fence_matches = re.findall(r'```(?:json)?\s*([\s\S]*?)(?:```|$)', raw_str)
        for block in reversed(fence_matches):
            parsed = self._try_parse_or_repair(block)
            if isinstance(parsed, (dict, list)):
                return parsed

        dict_candidates: List[str] = []
        list_candidates: List[str] = []

        for start_char, end_char, target_list in [('{', '}', dict_candidates), ('[', ']', list_candidates)]:
            pos = 0
            while True:
                start_idx = raw_str.find(start_char, pos)
                if start_idx == -1:
                    break

                depth = 0
                in_string = False
                escape = False
                candidate_found = False
                for i in range(start_idx, len(raw_str)):
                    c = raw_str[i]
                    if escape:
                        escape = False
                        continue
                    if c == '\\':
                        escape = True
                        continue
                    if c == '"':
                        in_string = not in_string
                        continue
                    if not in_string:
                        if c == start_char:
                            depth += 1
                        elif c == end_char:
                            depth -= 1
                            if depth == 0:
                                candidate = raw_str[start_idx:i+1]
                                target_list.append(candidate)
                                candidate_found = True
                                break

                if not candidate_found and depth > 0:
                    remainder = raw_str[start_idx:]
                    target_list.append(remainder)

                pos = start_idx + 1

        valid_dicts = []
        for cand in dict_candidates:
            parsed = self._try_parse_or_repair(cand)
            if isinstance(parsed, dict) and len(parsed) > 0:
                score = len(cand)
                for template_marker in ["string or null", '"title": "string"', '"description": "string"', "Unit Title", "CO Description", "detailed paragraph", "Remember|Understand"]:
                    if template_marker in cand:
                        score -= 2000
                valid_dicts.append((score, parsed))

        if valid_dicts:
            valid_dicts.sort(key=lambda x: x[0], reverse=True)
            return valid_dicts[0][1]

        for cand in reversed(list_candidates):
            parsed = self._try_parse_or_repair(cand)
            if isinstance(parsed, list):
                return parsed

        raise ValueError(f"Failed to parse JSON from NVIDIA response. Raw: {raw_str[:300]}")

    async def check_health(self) -> bool:
        """
        Safe health check to verify configuration and reachability.
        Does not consume generation credits unnecessarily.
        """
        if not self.api_key:
            return False
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                res = await client.get(
                    f"{self.base_url}/models",
                    headers=self._get_headers()
                )
                return res.status_code == 200
        except Exception as e:
            logger.warning(f"NVIDIA health check failed: {e}")
            return False
