from sqlalchemy.orm import Session
from fastapi import UploadFile

from core.logger import get_logger
from files.storage import LocalStorageBackend, StorageError
from files.files_models import UploadedFile

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024  # 25MB


class FileService:

    def __init__(self):
        self.storage = LocalStorageBackend()

    def upload_file(
        self,
        *,
        db: Session,
        user_id: int,
        file: UploadFile
    ) -> UploadedFile:

        try:
            file.file.seek(0, 2)
            size = file.file.tell()
            file.file.seek(0)

            if size > MAX_FILE_SIZE_BYTES:
                raise ValueError("File size exceeds limit")

            stored_name = self.storage.save(
                file_stream=file.file,
                original_filename=file.filename
            )

            record = UploadedFile(
                user_id=user_id,
                file_id=stored_name,
                original_filename=file.filename,
                mime_type=file.content_type or "application/octet-stream",
                size_bytes=size,
                storage_path=stored_name
            )

            db.add(record)
            db.commit()
            db.refresh(record)

            logger.info(
                "FILE_METADATA_SAVED | file_id=%s | user_id=%s",
                record.file_id,
                user_id
            )

            return record

        except StorageError:
            db.rollback()
            raise

        except Exception:
            db.rollback()
            logger.exception("FILE_UPLOAD_FAILED")
            raise

from fastapi import HTTPException
from pathlib import Path
import os


def resolve_file_for_user(
    *,
    db: Session,
    user_id: int,
    file_id: str,
):
    """
    Resolve a file safely for an authenticated user.

    Returns:
        (UploadedFile, absolute_file_path)

    Raises:
        404 if not found or not owned by user
    """

    record = (
        db.query(UploadedFile)
        .filter(
            UploadedFile.file_id == file_id,
            UploadedFile.user_id == user_id,
        )
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    base_path = Path(upload_dir).resolve()

    file_path = base_path / record.storage_path

    return record, str(file_path)