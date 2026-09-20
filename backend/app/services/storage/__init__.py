from app.core.config import settings
from app.services.storage.base import BaseStorageService
from app.services.storage.local import LocalStorageService
from app.services.storage.s3 import S3StorageService

_storage_instance = None

def get_storage_service() -> BaseStorageService:
    """
    Factory that returns the configured StorageService instance (Local or S3).
    """
    global _storage_instance
    if _storage_instance is None:
        provider = settings.STORAGE_PROVIDER.lower()
        if provider == "s3":
            _storage_instance = S3StorageService()
        else:
            _storage_instance = LocalStorageService()
    return _storage_instance

__all__ = [
    "BaseStorageService",
    "LocalStorageService",
    "S3StorageService",
    "get_storage_service",
]
