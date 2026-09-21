import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.services.llm.nvidia_provider import NvidiaProvider
from app.services.llm.factory import get_llm_provider
from app.core.config import settings
from app.main import app

def test_nvidia_provider_initialization():
    provider = NvidiaProvider(
        api_key="test-key-12345",
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        base_url="https://integrate.api.nvidia.com/v1"
    )
    assert provider.api_key == "test-key-12345"
    assert provider.model == "nvidia/nemotron-3.5-lightning-30b-a3b"
    assert provider.base_url == "https://integrate.api.nvidia.com/v1"
    assert provider.endpoint == "https://integrate.api.nvidia.com/v1/chat/completions"

def test_nvidia_provider_missing_key():
    provider = NvidiaProvider(api_key="")
    with pytest.raises(ValueError, match="NVIDIA_API_KEY is required"):
        provider._validate_configuration()

def test_nvidia_provider_headers():
    provider = NvidiaProvider(api_key="test-key-secret")
    headers = provider._get_headers()
    assert headers["Authorization"] == "Bearer test-key-secret"
    assert headers["Content-Type"] == "application/json"
    assert headers["Accept"] == "application/json"

@pytest.mark.asyncio
async def test_nvidia_provider_generate_text_mock():
    provider = NvidiaProvider(
        api_key="test-key",
        model="nvidia/nemotron-3.5-lightning-30b-a3b",
        base_url="https://integrate.api.nvidia.com/v1"
    )

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Explain the concept of Public Key Infrastructure (PKI) and asymmetric cryptography."
                }
            }
        ]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response) as mock_post:
        result = await provider.generate_text("Generate a question on PKI")
        assert "Public Key Infrastructure" in result
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["model"] == "nvidia/nemotron-3.5-lightning-30b-a3b"

@pytest.mark.asyncio
async def test_nvidia_provider_generate_json_mock():
    provider = NvidiaProvider(api_key="test-key")

    mock_json_content = """```json
    {
        "unit_number": 1,
        "title": "Introduction to Information Security",
        "topics": ["CIA Triad", "Threat Modeling", "Symmetric Ciphers"]
    }
    ```"""

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "choices": [{"message": {"content": mock_json_content}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock, return_value=mock_response):
        parsed = await provider.generate_json("Analyze Unit 1")
        assert isinstance(parsed, dict)
        assert parsed["unit_number"] == 1
        assert "CIA Triad" in parsed["topics"]

def test_nvidia_json_repair_logic():
    provider = NvidiaProvider(api_key="dummy")

    # 1. Unclosed JSON object with trailing comma
    broken_1 = '{"course_code": "IT701PC", "name": "Information Security",'
    repaired_1 = provider._try_parse_or_repair(broken_1)
    assert repaired_1 is not None
    assert repaired_1["course_code"] == "IT701PC"

    # 2. Markdown fence with extra text
    text_with_fences = """Here is the analyzed output:
    ```json
    {"status": "success", "confidence": 0.95}
    ```
    Please review the results."""
    extracted = provider._extract_json_from_text(text_with_fences)
    assert extracted["status"] == "success"
    assert extracted["confidence"] == 0.95

def test_llm_factory_nvidia():
    with patch.object(settings, "LLM_PROVIDER", "nvidia"):
        provider = get_llm_provider()
        assert isinstance(provider, NvidiaProvider)

def test_health_llm_endpoint():
    client = TestClient(app)
    response = client.get("/health/llm")
    assert response.status_code == 200
    data = response.json()
    assert "provider" in data
    assert "model" in data
    assert "configured" in data
    # Verify no secrets or credentials leaked
    assert "api_key" not in data
    assert "NVIDIA_API_KEY" not in data
    assert "Authorization" not in data
    assert "Bearer" not in str(data)

def test_health_main_endpoint():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "llm_provider" in data
    assert "llm_model" in data
