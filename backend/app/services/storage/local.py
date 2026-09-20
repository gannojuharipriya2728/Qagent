import os
import shutil
from typing import Optional, BinaryIO
from app.core.config import settings
from app.services.storage.base import BaseStorageService

class LocalStorageService(BaseStorageService):
    """
    Local filesystem storage provider for development, testing, and single-instance deployments.
    """
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = os.path.abspath(base_dir or settings.STORAGE_DIR)
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_full_path(self, storage_key: str) -> str:
        # Strip leading slashes to prevent root escapes
        clean_key = storage_key.lstrip("/\\")
        full_path = os.path.abspath(os.path.join(self.base_dir, clean_key))
        # Ensure path stays within base_dir (directory traversal protection)
        if not full_path.startswith(self.base_dir):
            raise ValueError(f"Invalid storage path traversal attempt: {storage_key}")
        return full_path

    async def upload_file(
        self,
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        dest_path = self._get_full_path(storage_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Reset file pointer if seekable
        if hasattr(file_obj, "seek"):
            try:
                file_obj.seek(0)
            except Exception:
                pass

        with open(dest_path, "wb") as f_out:
            shutil.copyfileobj(file_obj, f_out)
        
        return storage_key

    async def upload_bytes(
        self,
        data: bytes,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        dest_path = self._get_full_path(storage_key)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f_out:
            f_out.write(data)
        return storage_key

    async def download_bytes(self, storage_key: str) -> bytes:
        dest_path = self._get_full_path(storage_key)
        if not os.path.exists(dest_path):
            raise FileNotFoundError(f"Storage key '{storage_key}' not found at '{dest_path}'")
        with open(dest_path, "rb") as f_in:
            return f_in.read()

    async def delete_file(self, storage_key: str) -> bool:
        dest_path = self._get_full_path(storage_key)
        if os.path.exists(dest_path):
            try:
                os.remove(dest_path)
                return True
            except OSError:
                return False
        return False

    async def file_exists(self, storage_key: str) -> bool:
        dest_path = self._get_full_path(storage_key)
        return os.path.exists(dest_path)

    async def get_local_path(self, storage_key: str) -> str:
        dest_path = self._get_full_path(storage_key)
        return dest_path

    async def get_file_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        # Return local relative API path
        return f"/api/resources/files/{storage_key}"
