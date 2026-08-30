import os
import shutil
import uuid
import aiofiles
from abc import ABC, abstractmethod
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings

class StorageService(ABC):
    @abstractmethod
    async def save_file(self, file: UploadFile, subfolder: str = "") -> dict:
        """Saves an uploaded file and returns metadata: {'url': str, 'filename': str, 'size': int, 'mime': str}"""
        pass

    @abstractmethod
    async def delete_file(self, file_url: str) -> bool:
        """Deletes a file by its stored URL/path."""
        pass

    @abstractmethod
    def get_absolute_path(self, file_url: str) -> str:
        """Resolves the local absolute path for audio processing."""
        pass


class LocalStorageService(StorageService):
    def __init__(self, base_dir: str = settings.UPLOAD_DIR):
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    async def save_file(self, file: UploadFile, subfolder: str = "") -> dict:
        # Validate MIME type
        if file.content_type not in settings.ALLOWED_AUDIO_MIMES:
            # Fallback: check file extension if browser provided generic octet-stream
            ext = os.path.splitext(file.filename or "")[1].lower()
            valid_exts = [".mp3", ".wav", ".m4a", ".ogg", ".mp4", ".aac", ".flac"]
            if ext not in valid_exts:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unsupported file type: {file.content_type}. Allowed audio formats: MP3, WAV, M4A, OGG, MP4."
                )

        target_dir = os.path.join(self.base_dir, subfolder) if subfolder else self.base_dir
        os.makedirs(target_dir, exist_ok=True)

        # Generate collision-free filename
        file_ext = os.path.splitext(file.filename or "audio.mp3")[1]
        unique_name = f"{uuid.uuid4().hex}{file_ext}"
        destination_path = os.path.join(target_dir, unique_name)

        size_bytes = 0
        max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024

        async with aiofiles.open(destination_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):  # 1MB chunks
                size_bytes += len(chunk)
                if size_bytes > max_bytes:
                    # Clean up partial file
                    await out_file.close()
                    if os.path.exists(destination_path):
                        os.remove(destination_path)
                    raise HTTPException(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        detail=f"Audio file exceeds maximum size of {settings.MAX_UPLOAD_SIZE_MB}MB."
                    )
                await out_file.write(chunk)

        # Build relative URL for API consumption
        rel_path = os.path.join(subfolder, unique_name).replace("\\", "/") if subfolder else unique_name
        audio_url = f"/api/episodes/media/{rel_path}"

        return {
            "url": audio_url,
            "filename": file.filename or unique_name,
            "stored_filename": unique_name,
            "file_size": size_bytes,
            "mime_type": file.content_type or "audio/mpeg",
            "local_path": destination_path,
        }

    async def delete_file(self, file_url: str) -> bool:
        try:
            rel_path = file_url.replace("/api/episodes/media/", "")
            target_path = os.path.join(self.base_dir, rel_path)
            if os.path.exists(target_path):
                os.remove(target_path)
                return True
        except Exception:
            pass
        return False

    def get_absolute_path(self, file_url: str) -> str:
        rel_path = file_url.replace("/api/episodes/media/", "")
        return os.path.join(self.base_dir, rel_path)


storage_service = LocalStorageService()
