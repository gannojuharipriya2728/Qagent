from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.deterministic_provider import DeterministicAcademicProvider

def get_llm_provider(override_provider: str = None) -> BaseLLMProvider:
    provider_type = (override_provider or settings.LLM_PROVIDER).lower().strip()
    
    if provider_type == "openrouter":
        return OpenRouterProvider()
    elif provider_type == "ollama":
        return OllamaProvider()
    elif provider_type == "deterministic":
        return DeterministicAcademicProvider()
    else:
        return OpenRouterProvider()

