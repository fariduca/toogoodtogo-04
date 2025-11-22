"""Image storage abstraction for business pictures."""

from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4


class ImageStoreProtocol(Protocol):
    """Protocol for image storage backends."""

    async def upload(self, image_data: bytes, content_type: str) -> str:
        """Upload image and return public URL."""
        ...

    async def delete(self, image_url: str) -> bool:
        """Delete image by URL."""
        ...


class LocalImageStore:
    """Local filesystem image storage (MVP implementation)."""

    def __init__(self, base_path: str = "./uploads", base_url: str = "/static"):
        """Initialize local image store."""
        self.base_path = Path(base_path)
        self.base_url = base_url
        self.base_path.mkdir(parents=True, exist_ok=True)

    async def upload(self, image_data: bytes, content_type: str) -> str:
        """Save image locally and return relative URL."""
        # Generate unique filename
        ext = content_type.split("/")[-1] if "/" in content_type else "jpg"
        filename = f"{uuid4()}.{ext}"
        filepath = self.base_path / filename

        # Write file
        filepath.write_bytes(image_data)

        return f"{self.base_url}/{filename}"

    async def delete(self, image_url: str) -> bool:
        """Delete image file."""
        try:
            filename = image_url.split("/")[-1]
            filepath = self.base_path / filename
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception:
            pass
        return False


class S3ImageStore:
    """S3-compatible object storage (future implementation)."""

    def __init__(self, bucket: str, endpoint: str, access_key: str, secret_key: str):
        """Initialize S3 image store."""
        self.bucket = bucket
        self.endpoint = endpoint
        # TODO: Initialize boto3 or httpx client
        raise NotImplementedError("S3 storage not yet implemented")

    async def upload(self, image_data: bytes, content_type: str) -> str:
        """Upload to S3 and return public URL."""
        raise NotImplementedError("S3 storage not yet implemented")

    async def delete(self, image_url: str) -> bool:
        """Delete from S3."""
        raise NotImplementedError("S3 storage not yet implemented")
