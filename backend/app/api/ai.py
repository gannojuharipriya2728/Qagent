from fastapi import APIRouter
from app.core.config import settings
from app.services.llm.factory import get_llm_provider

router = APIRouter(prefix="/ai", tags=["AI Health & Diagnostic"])

@router.get("/health")
async def get_ai_health():
    """
    Diagnostic health check for the AI LLM Gateway (NVIDIA NIM / OpenRouter).
    Returns provider info, model identifier, configuration status, and reachability.
    Never returns secrets, authorization headers, or API keys.
    """
    provider_name = settings.LLM_PROVIDER.lower().strip()
    if provider_name == "nvidia":
        model_name = settings.NVIDIA_MODEL
        is_configured = bool(settings.NVIDIA_API_KEY and settings.NVIDIA_API_KEY.strip())
    elif provider_name == "openrouter":
        model_name = settings.OPENROUTER_MODEL
        is_configured = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())
    elif provider_name == "ollama":
        model_name = settings.OLLAMA_MODEL
        is_configured = bool(settings.OLLAMA_BASE_URL and settings.OLLAMA_BASE_URL.strip())
    else:
        model_name = "deterministic-rule-engine"
        is_configured = True
    
    reachable = False
    if is_configured:
        try:
            provider = get_llm_provider()
            if hasattr(provider, "check_health"):
                reachable = await provider.check_health()
            else:
                reachable = True
        except Exception:
            reachable = False

    return {
        "provider": provider_name,
        "model": model_name,
        "configured": is_configured,
        "reachable": reachable
    }

