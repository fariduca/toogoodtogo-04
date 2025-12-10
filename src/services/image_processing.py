"""Image processing service for business photos and offer images.

Handles:
- Image upload from Telegram
- Image validation (format, size, dimensions)
- Image resizing/compression
- Storage to filesystem or S3
"""

from io import BytesIO
from pathlib import Path
from uuid import uuid4

from PIL import Image

from src.logging import get_logger
from src.storage.image_store import ImageStoreProtocol

logger = get_logger(__name__)

# Image constraints
MAX_FILE_SIZE_MB = 5
MAX_DIMENSION = 2048
THUMBNAIL_SIZE = (400, 400)
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}


class ImageProcessor:
    """Handles image validation, processing, and storage."""

    def __init__(self, image_store: ImageStoreProtocol):
        """Initialize with image storage backend."""
        self.image_store = image_store

    async def process_telegram_photo(
        self, file_bytes: bytes, file_id: str
    ) -> tuple[str, str]:
        """
        Process photo uploaded via Telegram.

        Args:
            file_bytes: Raw image bytes from Telegram
            file_id: Telegram file ID for tracking

        Returns:
            Tuple of (image_url, thumbnail_url)

        Raises:
            ValueError: If image validation fails
        """
        # Validate file size
        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise ValueError(f"Image too large: {size_mb:.2f}MB (max {MAX_FILE_SIZE_MB}MB)")

        # Load and validate image
        try:
            image = Image.open(BytesIO(file_bytes))
        except Exception as e:
            raise ValueError(f"Invalid image file: {e}")

        if image.format not in ALLOWED_FORMATS:
            raise ValueError(
                f"Unsupported format: {image.format}. Allowed: {', '.join(ALLOWED_FORMATS)}"
            )

        logger.info(
            "image_received",
            file_id=file_id,
            format=image.format,
            size=f"{image.width}x{image.height}",
        )

        # Resize if needed
        if image.width > MAX_DIMENSION or image.height > MAX_DIMENSION:
            image = self._resize_image(image, MAX_DIMENSION)
            logger.info("image_resized", new_size=f"{image.width}x{image.height}")

        # Create thumbnail
        thumbnail = self._create_thumbnail(image)

        # Save images
        image_filename = f"{uuid4()}.jpg"
        thumbnail_filename = f"{uuid4()}_thumb.jpg"

        # Convert to JPEG bytes
        image_bytes = self._to_jpeg_bytes(image)
        thumbnail_bytes = self._to_jpeg_bytes(thumbnail)

        # Store images
        image_url = await self.image_store.save(image_filename, image_bytes)
        thumbnail_url = await self.image_store.save(thumbnail_filename, thumbnail_bytes)

        logger.info(
            "image_processed",
            file_id=file_id,
            image_url=image_url,
            thumbnail_url=thumbnail_url,
        )

        return image_url, thumbnail_url

    def _resize_image(self, image: Image.Image, max_dimension: int) -> Image.Image:
        """Resize image maintaining aspect ratio."""
        ratio = min(max_dimension / image.width, max_dimension / image.height)
        new_size = (int(image.width * ratio), int(image.height * ratio))
        return image.resize(new_size, Image.Resampling.LANCZOS)

    def _create_thumbnail(self, image: Image.Image) -> Image.Image:
        """Create thumbnail maintaining aspect ratio."""
        thumbnail = image.copy()
        thumbnail.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
        return thumbnail

    def _to_jpeg_bytes(self, image: Image.Image, quality: int = 85) -> bytes:
        """Convert image to JPEG bytes."""
        # Convert RGBA to RGB if needed
        if image.mode in ("RGBA", "P"):
            rgb_image = Image.new("RGB", image.size, (255, 255, 255))
            rgb_image.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = rgb_image

        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        return buffer.getvalue()

    async def delete_image(self, image_url: str) -> bool:
        """Delete image from storage."""
        try:
            # Extract filename from URL
            filename = Path(image_url).name
            await self.image_store.delete(filename)
            logger.info("image_deleted", image_url=image_url)
            return True
        except Exception as e:
            logger.error("image_deletion_failed", image_url=image_url, error=str(e))
            return False
