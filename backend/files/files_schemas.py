from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileUploadResponse(BaseModel):
    file_id: str
    filename: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime


class FileMeta(BaseModel):
    file_id: str
    filename: str
    mime_type: str
    size_bytes: int
    uploaded_at: datetime