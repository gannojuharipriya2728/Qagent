import os
from typing import List
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

def get_normalized_database_url(url: str) -> str:
    """
    Normalizes database connection strings for SQLAlchemy async engines.
    - sqlite:// -> sqlite+aiosqlite://
    - postgres:// or postgresql:// -> postgresql+asyncpg://
    - properly encodes password special characters (e.g. '@') if needed
    - cleans up incompatible query parameters for asyncpg (e.g. sslmode)
    """
    if not url:
        return url
    
    url = url.strip()
    
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("sqlite+aiosqlite://"):
        return url
    
    prefix = ""
    rest = ""
    if url.startswith("postgres://"):
        prefix = "postgresql+asyncpg://"
        rest = url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        prefix = "postgresql+asyncpg://"
        rest = url[len("postgresql://"):]
    elif url.startswith("postgresql+asyncpg://"):
        prefix = "postgresql+asyncpg://"
        rest = url[len("postgresql+asyncpg://"):]
    else:
        return url
    
    # Check for unencoded '@' in user:pass
    if "@" in rest:
        auth_part, sep, host_part = rest.rpartition("@")
        if ":" in auth_part:
            user, pwd = auth_part.split(":", 1)
            from urllib.parse import quote, unquote
            decoded_pwd = unquote(pwd)
            encoded_pwd = quote(decoded_pwd, safe="")
            rest = f"{user}:{encoded_pwd}@{host_part}"
    
    # Strip any sslmode query parameter because asyncpg handles SSL via connect_args
    if "?sslmode=" in rest:
        rest = rest.split("?sslmode=")[0]
    elif "&sslmode=" in rest:
        rest = rest.split("&sslmode=")[0]
        
    return prefix + rest

class Settings(BaseSettings):
    PROJECT_NAME: str = "QAgent — Agentic AI Question Generator"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    # Environment & Deployment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    SEED_DEMO_DATA: bool = os.getenv("SEED_DEMO_DATA", "false" if os.getenv("ENVIRONMENT") == "production" else "true").lower() in ["true", "1", "yes"]
    
    # Security
    SECRET_KEY: str = "agentic-ai-academic-rag-secret-key-2026-super-secure"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173", "*"]
    
    # LLM Settings (OpenRouter Primary Provider)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "openrouter")  # "openrouter", "ollama", "deterministic"
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173")
    OPENROUTER_APP_NAME: str = os.getenv("OPENROUTER_APP_NAME", "QAgent")
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    
    # Storage & Paths
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/academic_rag.db")
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # "local", "s3"
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./data/uploads")
    EXPORTS_DIR: str = os.getenv("EXPORTS_DIR", "./data/exports")
    VECTOR_STORAGE_DIR: str = os.getenv("VECTOR_STORAGE_DIR", "./data/vector_store")
    VECTOR_STORE_PROVIDER: str = os.getenv("VECTOR_STORE_PROVIDER", "local")  # "local", "pgvector"
    
    # S3 Object Storage Configuration (for STORAGE_PROVIDER="s3")
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")
    S3_ACCESS_KEY_ID: str = os.getenv("S3_ACCESS_KEY_ID", "")
    S3_SECRET_ACCESS_KEY: str = os.getenv("S3_SECRET_ACCESS_KEY", "")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "qagent-academic-storage")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    
    # Agent & RAG Parameters
    CHUNK_SIZE: int = 600
    CHUNK_OVERLAP: int = 100
    TOP_K_RETRIEVAL: int = 5
    SIMILARITY_DUPLICATE_THRESHOLD: float = 0.82
    MAX_REVISION_ATTEMPTS: int = 3

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return get_normalized_database_url(self.DATABASE_URL)

    @property
    def IS_POSTGRES(self) -> bool:
        return "postgres" in self.DATABASE_URL.lower()

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()
