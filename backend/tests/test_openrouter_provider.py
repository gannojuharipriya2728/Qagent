import pytest
import os
import json
from unittest.mock import AsyncMock, patch, MagicMock
from dotenv import load_dotenv
import httpx

load_dotenv()

from backend.app.services.llm.openrouter_provider import OpenRouterProvider
from backend.app.services.llm.factory import get_llm_provider
from backend.app.services.llm.syllabus_analyzer import SyllabusAnalyzer
from backend.app.core.config import settings

def test_openrouter_provider_initialization():
    provider = OpenRouterProvider(
        api_key="test-openrouter-key",
        model="nvidia/nemotron-3.5-lightning:free",
        base_url="https://openrouter.ai/api/v1",
        site_url="http://localhost:5173",
        app_name="QAgent"
    )
    assert provider.api_key == "test-openrouter-key"
    assert provider.model == "nvidia/nemotron-3.5-lightning:free"
    assert provider.base_url == "https://openrouter.ai/api/v1"
    assert provider.site_url == "http://localhost:5173"
    assert provider.app_name == "QAgent"
    assert provider.endpoint == "https://openrouter.ai/api/v1/chat/completions"

@pytest.mark.asyncio
async def test_openrouter_provider_missing_key_error():
    with pytest.raises(ValueError) as exc:
        OpenRouterProvider(api_key="")
    assert "OPENROUTER_API_KEY is required" in str(exc.value) or "OpenRouter" in str(exc.value)

@pytest.mark.asyncio
async def test_openrouter_provider_generate_text_mock():
    provider = OpenRouterProvider(
        api_key="mock-openrouter-key",
        model="nvidia/nemotron-3.5-lightning:free",
        site_url="http://localhost:5173",
        app_name="QAgent"
    )
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Explain the principle of public key cryptography and RSA encryption."
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        text = await provider.generate_text("Prompt test", "System prompt test")
        assert text == "Explain the principle of public key cryptography and RSA encryption."
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert kwargs["headers"]["Authorization"] == "Bearer mock-openrouter-key"
        assert kwargs["headers"]["HTTP-Referer"] == "http://localhost:5173"
        assert kwargs["headers"]["X-Title"] == "QAgent"
        assert kwargs["json"]["model"] == "nvidia/nemotron-3.5-lightning:free"

@pytest.mark.asyncio
async def test_openrouter_provider_generate_json_repair_mock():
    provider = OpenRouterProvider(api_key="mock-openrouter-key")
    
    # Mocking response wrapped in markdown code fence
    mock_json_content = """```json
    {
        "course": {
            "code": "IT701PC",
            "title": "Information Security"
        },
        "units": [
            {"unit_number": 1, "title": "Security Attacks", "topics": "Classical ciphers and models"}
        ],
        "course_outcomes": [
            {"code": "CO1", "description": "Understand cryptography basics", "bloom_level": "Understand", "bloom_source": "explicit"}
        ]
    }
    ```"""
    
    mock_response_data = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": mock_json_content
                }
            }
        ]
    }
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_response_data

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp
        res = await provider.generate_json("Prompt test")
        assert res["course"]["code"] == "IT701PC"
        assert len(res["units"]) == 1
        assert res["course_outcomes"][0]["code"] == "CO1"

@pytest.mark.asyncio
async def test_openrouter_provider_429_retry_handling():
    provider = OpenRouterProvider(api_key="mock-openrouter-key")
    
    # First response 429 rate-limited, second response 200 OK
    mock_resp_429 = MagicMock()
    mock_resp_429.status_code = 429
    mock_resp_429.text = "Rate limit exceeded"

    mock_resp_200 = MagicMock()
    mock_resp_200.status_code = 200
    mock_resp_200.json.return_value = {
        "choices": [{"message": {"role": "assistant", "content": "Success after retry"}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [mock_resp_429, mock_resp_200]
        with patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            text = await provider.generate_text("Test prompt")
            assert text == "Success after retry"
            assert mock_post.call_count == 2
            mock_sleep.assert_called_once()

def test_llm_factory_openrouter_provider_selection():
    with patch.object(settings, "OPENROUTER_API_KEY", "test-or-key"):
        provider = get_llm_provider("openrouter")
        assert isinstance(provider, OpenRouterProvider)
        assert provider.api_key == "test-or-key"
        assert provider.model == settings.OPENROUTER_MODEL

@pytest.mark.asyncio
async def test_syllabus_analyzer_structured_flow():
    mock_syllabus = """
    Department of Information Technology
    Course Code: IT701PC
    Course Title: Information Security
    Semester: IV Year I Semester
    
    UNIT I: Security Attacks, Services & Classical Encryption
    Symmetric Cipher Model, Substitution techniques, Transposition techniques.
    
    UNIT II: Public Key Cryptography & Hash Functions
    Principles of Public-Key Cryptosystems, RSA algorithm, Diffie-Hellman Key Exchange, SHA-512.
    
    Course Outcomes:
    CO1: Demonstrate the knowledge of cryptography, network security concepts.
    CO2: Ability to apply security principles in system design.
    CO3: Ability to identify and investigate vulnerabilities and security threats.
    """

    res = await SyllabusAnalyzer.analyze_syllabus_text(mock_syllabus, override_provider="deterministic")
    assert "course" in res
    assert res["course"]["code"] in ["IT701PC", "COURSE101"]
    assert len(res["units"]) >= 2
    assert len(res["course_outcomes"]) >= 3
    # Check no fabricated COs
    co_codes = [c["code"] for c in res["course_outcomes"]]
    assert "CO4" not in co_codes
    assert "CO5" not in co_codes

@pytest.mark.asyncio
async def test_syllabus_analyzer_with_openrouter_mock():
    mock_syllabus = "Course Code: CS501\nCourse Title: Operating Systems\nUNIT I: Processes\nCO1: Understand processes."
    mock_response = {
        "course": {"code": "CS501", "title": "Operating Systems", "department": "CSE", "semester": "V"},
        "units": [{"unit_number": 1, "title": "Processes", "topics": "Process management"}],
        "course_outcomes": [{"code": "CO1", "description": "Understand processes", "bloom_level": "Understand", "bloom_source": "explicit"}]
    }
    with patch("backend.app.services.llm.openrouter_provider.OpenRouterProvider.generate_json", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_response
        with patch.object(settings, "OPENROUTER_API_KEY", "mock-key"):
            res = await SyllabusAnalyzer.analyze_syllabus_text(mock_syllabus, override_provider="openrouter")
            assert res["course"]["code"] == "CS501"
            assert len(res["units"]) == 1
            assert res["course_outcomes"][0]["code"] == "CO1"

@pytest.mark.asyncio
async def test_production_never_falls_back_to_deterministic():
    """
    Verify that in production (LLM_PROVIDER=openrouter), when OpenRouter API fails
    (due to missing key, invalid key, or network error), the system raises a clear
    RuntimeError instead of silently generating fake deterministic questions.
    """
    from backend.app.services.agents.generation_agent import QuestionGenerationAgent
    from backend.app.services.agents.requirement_agent import PlannedQuestionSlot
    from backend.app.services.agents.retrieval_agent import RetrievalResult

    slot = PlannedQuestionSlot(
        slot_index=0,
        section_name="Section A",
        question_number=1,
        marks=2,
        unit_number=1,
        bloom_level="Remember",
        course_outcome="CO1",
        difficulty="Easy",
        question_type="Short"
    )
    retrieval = RetrievalResult(
        assembled_context="Symmetric Cipher Model and Classical Encryption.",
        source_documents=[],
        source_topics=["Classical Encryption"]
    )

    with patch.object(settings, "LLM_PROVIDER", "openrouter"):
        with patch.object(settings, "OPENROUTER_API_KEY", ""):
            with pytest.raises(RuntimeError) as exc_info:
                await QuestionGenerationAgent.generate_question(
                    slot=slot,
                    retrieval=retrieval,
                    course_name="Information Security",
                    override_provider=None
                )
            assert "OpenRouter AI generation failed" in str(exc_info.value)

@pytest.mark.asyncio
async def test_ai_health_endpoint():
    from backend.app.api.ai import get_ai_health
    with patch.object(settings, "OPENROUTER_API_KEY", ""):
        health = await get_ai_health()
        assert health["provider"] == settings.LLM_PROVIDER
        assert health["model"] == settings.OPENROUTER_MODEL
        assert health["configured"] is False
        assert health["reachable"] is False

@pytest.mark.asyncio
@pytest.mark.skipif(
    not settings.OPENROUTER_API_KEY and not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set"
)
async def test_openrouter_provider_live_api_text():
    """
    Live API text generation test with NVIDIA Nemotron 3.5 Lightning via OpenRouter.
    """
    provider = OpenRouterProvider()
    res = await provider.generate_text("State the definition of cryptography in one concise sentence.")
    assert res and len(res.strip()) > 5

@pytest.mark.asyncio
@pytest.mark.skipif(
    not settings.OPENROUTER_API_KEY and not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY environment variable not set"
)
async def test_openrouter_provider_live_api_json():
    """
    Live API structured JSON generation test with NVIDIA Nemotron 3.5 Lightning via OpenRouter.
    """
    provider = OpenRouterProvider()
    prompt = "Return a JSON object with 'topic': 'Information Security', 'concepts': ['Confidentiality', 'Integrity', 'Availability'], 'status': 'active'."
    res = await provider.generate_json(prompt)
    assert isinstance(res, dict)
    assert "topic" in res or "concepts" in res
