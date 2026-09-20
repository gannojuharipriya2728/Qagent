import abc
from typing import Optional, BinaryIO

class BaseStorageService(abc.ABC):
    """
    Abstract interface for object and file storage.
    Enables pluggable backend drivers (Local filesystem, S3 / MinIO / Cloud Object Store).
    """

    @abc.abstractmethod
    async def upload_file(
        self,
        file_obj: BinaryIO,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Uploads a binary file stream and returns the normalized storage_key.
        """
        pass

    @abc.abstractmethod
    async def upload_bytes(
        self,
        data: bytes,
        storage_key: str,
        content_type: str = "application/octet-stream"
    ) -> str:
        """
        Uploads raw bytes to storage and returns the normalized storage_key.
        """
        pass

    @abc.abstractmethod
    async def download_bytes(self, storage_key: str) -> bytes:
        """
        Downloads the complete file as bytes.
        """
        pass

    @abc.abstractmethod
    async def delete_file(self, storage_key: str) -> bool:
        """
        Deletes a file by its storage key.
        """
        pass

    @abc.abstractmethod
    async def file_exists(self, storage_key: str) -> bool:
        """
        Checks whether a file exists in the storage bucket / directory.
        """
        pass

    @abc.abstractmethod
    async def get_local_path(self, storage_key: str) -> str:
        """
        Returns a local filesystem path for processing (downloads to temporary cache if remote).
        """
        pass

    @abc.abstractmethod
    async def get_file_url(self, storage_key: str, expires_in: int = 3600) -> Optional[str]:
        """
        Returns a signed URL or API download URL for the file.
        """
        pass
