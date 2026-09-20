import os
import io
import pytest
from unittest.mock import MagicMock, patch
from app.services.storage.local import LocalStorageService
from app.services.storage.s3 import S3StorageService
from app.services.storage import get_storage_service
from app.core.config import settings

@pytest.mark.asyncio
async def test_local_storage_service_crud(tmp_path):
    storage = LocalStorageService(base_dir=str(tmp_path))
    
    # 1. Test upload bytes
    key = "courses/1/test_document.txt"
    uploaded_key = await storage.upload_bytes(b"Hello Academic World", key, content_type="text/plain")
    assert uploaded_key == key
    
    # 2. Test file exists
    assert await storage.file_exists(key) is True
    assert await storage.file_exists("nonexistent.txt") is False
    
    # 3. Test download bytes
    downloaded = await storage.download_bytes(key)
    assert downloaded == b"Hello Academic World"
    
    # 4. Test get local path
    local_path = await storage.get_local_path(key)
    assert os.path.exists(local_path)
    
    # 5. Test upload file stream
    stream = io.BytesIO(b"Stream content data")
    stream_key = "courses/1/stream.pdf"
    await storage.upload_file(stream, stream_key, content_type="application/pdf")
    assert await storage.download_bytes(stream_key) == b"Stream content data"
    
    # 6. Test delete
    deleted = await storage.delete_file(key)
    assert deleted is True
    assert await storage.file_exists(key) is False

@pytest.mark.asyncio
async def test_local_storage_traversal_protection(tmp_path):
    storage = LocalStorageService(base_dir=str(tmp_path))
    with pytest.raises(ValueError):
        storage._get_full_path("../../etc/passwd")

@pytest.mark.asyncio
async def test_s3_storage_service_with_mocks():
    mock_boto_client = MagicMock()
    mock_boto_client.get_object.return_value = {"Body": io.BytesIO(b"S3 file data")}
    mock_boto_client.head_object.return_value = {}

    with patch("boto3.session.Session.client", return_value=mock_boto_client):
        s3 = S3StorageService(
            bucket_name="test-bucket",
            endpoint_url="https://s3.example.com",
            access_key="mock-key",
            secret_key="mock-secret",
            region="us-east-1"
        )
        
        # Test upload
        key = "courses/10/syllabus.pdf"
        await s3.upload_bytes(b"S3 file data", key, content_type="application/pdf")
        mock_boto_client.put_object.assert_called_once()
        
        # Test download
        downloaded = await s3.download_bytes(key)
        assert downloaded == b"S3 file data"
        
        # Test exists
        assert await s3.file_exists(key) is True
        
        # Test delete
        deleted = await s3.delete_file(key)
        assert deleted is True
        mock_boto_client.delete_object.assert_called_once()

def test_storage_service_factory():
    with patch.object(settings, "STORAGE_PROVIDER", "local"):
        with patch("app.services.storage._storage_instance", None):
            svc = get_storage_service()
            assert isinstance(svc, LocalStorageService)
