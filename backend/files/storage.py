import os
import shutil
import uuid
from pathlib import Path
from typing import BinaryIO

from core.logger import get_logger

logger = get_logger(__name__)


class StorageError(Exception):
    pass


class StorageBackend:
    """
    Abstract storage backend.
    """

    def save(
        self,
        *,
        file_stream: BinaryIO,
        original_filename: str
    ) -> str:
        raise NotImplementedError


class LocalStorageBackend(StorageBackend):
    """
    Local filesystem storage backend.
    Default for free + production-safe setup.
    """

    def __init__(self):
        upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
        self.base_path = Path(upload_dir).resolve()

        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
            logger.info(
                "UPLOAD_DIR_READY | path=%s",
                str(self.base_path)
            )
        except Exception:
            logger.exception("UPLOAD_DIR_INIT_FAILED")
            raise StorageError("Failed to initialize upload directory")

    def save(
        self,
        *,
        file_stream: BinaryIO,
        original_filename: str
    ) -> str:
        try:
            ext = Path(original_filename).suffix.lower()
            safe_name = f"{uuid.uuid4().hex}{ext}"
            target_path = self.base_path / safe_name

            with open(target_path, "wb") as out:
                shutil.copyfileobj(file_stream, out)

            logger.info(
                "FILE_SAVED | filename=%s | path=%s",
                original_filename,
                target_path.name
            )

            return target_path.name

        except Exception:
            logger.exception(
                "FILE_SAVE_FAILED | filename=%s",
                original_filename
            )
            raise StorageError("Failed to store file")