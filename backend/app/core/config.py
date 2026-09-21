import os
import urllib.parse
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

def get_normalized_database_url(url: str) -> str:
    """
    Normalizes database connection strings for SQLAlchemy async engines.
    - sqlite:// -> sqlite+aiosqlite://
    - postgres:// or postgresql:// -> postgresql+asyncpg://
    - properly encodes password special characters (e.g. '@', '#', '!', '%')
    - cleans up incompatible query parameters for asyncpg (e.g. sslmode)
    """
    if not url:
        return url
    
    url = url.strip()
    
    # Handle SQLite schemes
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "sqlite+aiosqlite://", 1)
    if url.startswith("sqlite+aiosqlite://"):
        return url
    
    # Normalize PostgreSQL schemes to asyncpg
    prefix = "postgresql+asyncpg://"
    rest = ""
    if url.startswith("postgres://"):
        rest = url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        rest = url[len("postgresql://"):]
    elif url.startswith("postgresql+asyncpg://"):
        rest = url[len("postgresql+asyncpg://"):]
    elif url.startswith("postgresql+psycopg2://"):
        rest = url[len("postgresql+psycopg2://"):]
    else:
        return url
    
    # Separate query string if present
    query_str = ""
    if "?" in rest:
        rest_no_query, query_str = rest.split("?", 1)
    else:
        rest_no_query = rest
        
    # Clean query parameters incompatible with asyncpg
    clean_params = []
    if query_str:
        pairs = query_str.split("&")
        for pair in pairs:
            if not pair:
                continue
            k = pair.split("=")[0].lower().strip()
            # asyncpg handles SSL via connect_args; sslmode in URL causes TypeError
            if k in ["sslmode", "ssl_mode"]:
                continue
            clean_params.append(pair)
            
    clean_query = "&".join(clean_params)
    
    # Parse and encode credentials (handles '@' and other special characters in password)
    if "@" in rest_no_query:
        auth_part, sep, host_part = rest_no_query.rpartition("@")
        if ":" in auth_part:
            user, pwd = auth_part.split(":", 1)
            decoded_user = urllib.parse.unquote(user)
            encoded_user = urllib.parse.quote(decoded_user, safe="")
            decoded_pwd = urllib.parse.unquote(pwd)
            encoded_pwd = urllib.parse.quote(decoded_pwd, safe="")
            rest_no_query = f"{encoded_user}:{encoded_pwd}@{host_part}"
        else:
            decoded_user = urllib.parse.unquote(auth_part)
            encoded_user = urllib.parse.quote(decoded_user, safe="")
            rest_no_query = f"{encoded_user}@{host_part}"
            
    final_url = prefix + rest_no_query
    if clean_query:
        final_url += f"?{clean_query}"
        
    return final_url

def get_safe_db_info(url: str) -> Dict[str, Any]:
    """
    Extracts sanitized database connection metadata without exposing passwords or credentials.
    """
    if not url:
        return {"driver": "none", "hostname": "none", "database": "none", "port": None}
        
    norm_url = get_normalized_database_url(url)
    
    if "sqlite" in norm_url:
        return {
            "driver": "sqlite+aiosqlite",
            "hostname": "local",
            "database": norm_url.split("///")[-1] if "///" in norm_url else "memory",
            "port": None
        }
        
    try:
        clean_for_parse = norm_url.replace("postgresql+asyncpg://", "http://").replace("postgresql://", "http://")
        parsed = urllib.parse.urlparse(clean_for_parse)
        db_name = parsed.path.lstrip("/") if parsed.path else ""
        return {
            "driver": "postgresql+asyncpg",
            "hostname": parsed.hostname or "unknown",
            "port": parsed.port or 5432,
            "database": db_name or "unknown",
        }
    except Exception:
        return {
            "driver": "postgresql+asyncpg",
            "hostname": "redacted",
            "database": "redacted",
            "port": 5432
        }


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
    
    # CORS Origins Resolution
    @property
    def CORS_ORIGINS(self) -> List[str]:
        raw = os.getenv("CORS_ORIGINS", "")
        origins: List[str] = []
        if raw.strip():
            if raw.strip().startswith("["):
                try:
                    import json
                    parsed = json.loads(raw)
                    if isinstance(parsed, list):
                        origins = [str(o).strip() for o in parsed if str(o).strip()]
                except Exception:
                    origins = [o.strip() for o in raw.split(",") if o.strip()]
            else:
                origins = [o.strip() for o in raw.split(",") if o.strip()]
        
        default_prod_origins = [
            "https://qagent-frontend-iota.vercel.app",
            "https://qagent-production-1.onrender.com",
            "https://qagent-production.onrender.com"
        ]
        
        if not origins:
            if self.ENVIRONMENT.lower() == "production":
                origins = list(default_prod_origins)
            else:
                origins = list(default_prod_origins) + [
                    "http://localhost:5173",
                    "http://localhost:3000",
                    "http://127.0.0.1:5173",
                    "http://127.0.0.1:3000",
                ]
        else:
            for origin in default_prod_origins:
                if origin not in origins:
                    origins.append(origin)
        
        # Enforce no wildcard origin in production
        if self.ENVIRONMENT.lower() == "production":
            origins = [o for o in origins if o != "*"]

        return origins

    # LLM Settings (NVIDIA Primary Provider)
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "nvidia")  # "nvidia", "openrouter", "ollama", "deterministic"
    NVIDIA_API_KEY: str = os.getenv("NVIDIA_API_KEY", "")
    NVIDIA_MODEL: str = os.getenv("NVIDIA_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b")
    NVIDIA_BASE_URL: str = os.getenv("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1")
    
    # OpenRouter LLM Settings (Fallback/Alternative Provider)
    OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL: str = os.getenv("OPENROUTER_MODEL", "nvidia/nemotron-3.5-lightning:free")
    OPENROUTER_BASE_URL: str = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
    OPENROUTER_SITE_URL: str = os.getenv("OPENROUTER_SITE_URL", "http://localhost:5173")
    OPENROUTER_APP_NAME: str = os.getenv("OPENROUTER_APP_NAME", "QAgent")
    
    # Ollama Local Provider Settings (Optional)
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral")
    
    # Database & Storage Paths
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./data/academic_rag.db")
    DB_SSL_MODE: str = os.getenv("DB_SSL_MODE", "require")  # "require", "disable"
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "10"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "20"))
    
    STORAGE_PROVIDER: str = os.getenv("STORAGE_PROVIDER", "local")  # "local", "s3"
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "/tmp/qagent/uploads" if os.getenv("VERCEL") else "./data/uploads")
    EXPORTS_DIR: str = os.getenv("EXPORTS_DIR", "/tmp/qagent/exports" if os.getenv("VERCEL") else "./data/exports")
    VECTOR_STORAGE_DIR: str = os.getenv("VECTOR_STORAGE_DIR", "/tmp/qagent/vector_store" if os.getenv("VERCEL") else "./data/vector_store")
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
    def RESOLVED_DATABASE_URL(self) -> str:
        raw_url = (self.DATABASE_URL or "").strip()
        if self.ENVIRONMENT.lower() == "production":
            if not raw_url:
                raise ValueError(
                    "CRITICAL: DATABASE_URL environment variable is missing in production environment. "
                    "A valid PostgreSQL connection string is strictly required on Vercel/Production."
                )
            if "sqlite" in raw_url.lower():
                raise ValueError(
                    "CRITICAL: SQLite is not permitted in production mode. "
                    "Please configure a PostgreSQL connection string in DATABASE_URL."
                )
            return raw_url
        return raw_url if raw_url else "sqlite+aiosqlite:///./data/academic_rag.db"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return get_normalized_database_url(self.RESOLVED_DATABASE_URL)

    @property
    def IS_POSTGRES(self) -> bool:
        return "postgres" in self.ASYNC_DATABASE_URL.lower()

    @property
    def SAFE_DATABASE_INFO(self) -> Dict[str, Any]:
        return get_safe_db_info(self.RESOLVED_DATABASE_URL)

    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "allow"

settings = Settings()

