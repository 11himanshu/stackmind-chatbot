from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import mimetypes
import os

from core.logger import get_logger
from dependencies import get_db, get_current_user_id
from files.service import resolve_file_for_user, FileService

logger = get_logger(__name__)
router = APIRouter(prefix="/files", tags=["files"])

file_service = FileService()


# =========================================================
# FILE UPLOAD
# =========================================================
@router.post("/upload")
def upload_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Authenticated file upload.
    Stores file locally and saves metadata in DB.
    """

    logger.info(
        "FILE_UPLOAD_REQUEST | user_id=%s | filename=%s | content_type=%s",
        user_id,
        file.filename,
        file.content_type,
    )

    try:
        record = file_service.upload_file(
            db=db,
            user_id=user_id,
            file=file,
        )

        logger.info(
            "FILE_UPLOAD_SUCCESS | user_id=%s | file_id=%s",
            user_id,
            record.file_id,
        )

        return {
            "file_id": record.file_id,
            "filename": record.original_filename,
            "mime_type": record.mime_type,
            "size_bytes": record.size_bytes,
        }

    except Exception as e:
        logger.exception(
            "FILE_UPLOAD_ERROR | user_id=%s | filename=%s",
            user_id,
            file.filename,
        )
        raise HTTPException(
            status_code=400,
            detail="Failed to upload file"
        )


# =========================================================
# FILE DOWNLOAD
# =========================================================
@router.get("/{file_id}")
def download_file(
    file_id: str,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Authenticated file access.
    - Inline open for PDFs/images
    - Download for others
    """

    record, file_path = resolve_file_for_user(
        db=db,
        user_id=user_id,
        file_id=file_id,
    )

    if not os.path.exists(file_path):
        logger.error("FILE_MISSING_ON_DISK | %s", file_path)
        raise HTTPException(status_code=404, detail="File not found")

    mime_type, _ = mimetypes.guess_type(record.original_filename)
    mime_type = mime_type or "application/octet-stream"

    inline_types = (
        mime_type.startswith("image/")
        or mime_type == "application/pdf"
    )

    disposition = (
        f'inline; filename="{record.original_filename}"'
        if inline_types
        else f'attachment; filename="{record.original_filename}"'
    )

    logger.info(
        "FILE_ACCESS | user_id=%s | file_id=%s | inline=%s",
        user_id,
        file_id,
        inline_types,
    )

    def file_stream():
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                yield chunk

    return StreamingResponse(
        file_stream(),
        media_type=mime_type,
        headers={
            "Content-Disposition": disposition
        }
    )