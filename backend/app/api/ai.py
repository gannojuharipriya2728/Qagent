from fastapi import APIRouter
from backend.app.core.config import settings
from backend.app.services.llm.openrouter_provider import OpenRouterProvider

router = APIRouter(prefix="/ai", tags=["AI Health & Diagnostic"])

@router.get("/health")
async def get_ai_health():
    """
    Diagnostic health check for the AI LLM Gateway (OpenRouter / NVIDIA Nemotron).
    Returns provider info, model identifier, configuration status, and reachability.
    """
    provider_name = settings.LLM_PROVIDER
    model_name = settings.OPENROUTER_MODEL
    is_configured = bool(settings.OPENROUTER_API_KEY and settings.OPENROUTER_API_KEY.strip())
    
    reachable = False
    if is_configured:
        try:
            provider = OpenRouterProvider()
            reachable = await provider.check_health()
        except Exception:
            reachable = False

    return {
        "provider": provider_name,
        "model": model_name,
        "configured": is_configured,
        "reachable": reachable
    }
