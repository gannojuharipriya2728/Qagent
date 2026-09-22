import logging
from app.core.config import settings
from app.services.llm.base import BaseLLMProvider
from app.services.llm.nvidia_provider import NvidiaProvider
from app.services.llm.openrouter_provider import OpenRouterProvider
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.deterministic_provider import DeterministicAcademicProvider

logger = logging.getLogger("qagent.llm.factory")

def get_llm_provider(override_provider: str = None) -> BaseLLMProvider:
    provider_type = (override_provider or settings.LLM_PROVIDER).lower().strip()
    
    if provider_type == "openrouter":
        logger.info(
            "LLM_PROVIDER_SELECTED",
            extra={
                "provider": "openrouter",
                "model": settings.OPENROUTER_MODEL,
                "base_url": settings.OPENROUTER_BASE_URL,
            },
        )
        return OpenRouterProvider()
    elif provider_type == "nvidia":
        logger.info(
            "LLM_PROVIDER_SELECTED",
            extra={
                "provider": "nvidia",
                "model": settings.NVIDIA_MODEL,
                "base_url": settings.NVIDIA_BASE_URL,
            },
        )
        return NvidiaProvider()
    elif provider_type == "ollama":
        logger.info(
            "LLM_PROVIDER_SELECTED",
            extra={
                "provider": "ollama",
                "model": settings.OLLAMA_MODEL,
                "base_url": settings.OLLAMA_BASE_URL,
            },
        )
        return OllamaProvider()
    elif provider_type == "deterministic":
        logger.info(
            "LLM_PROVIDER_SELECTED",
            extra={
                "provider": "deterministic",
                "model": "deterministic-rules",
                "base_url": "local",
            },
        )
        return DeterministicAcademicProvider()
    else:
        logger.info(
            "LLM_PROVIDER_SELECTED",
            extra={
                "provider": "openrouter",
                "model": settings.OPENROUTER_MODEL,
                "base_url": settings.OPENROUTER_BASE_URL,
            },
        )
        return OpenRouterProvider()
