from typing import List
from pydantic import BaseModel


class TextReplacement(BaseModel):
    block_id: str
    old_text: str
    new_text: str


class PdfPatchPlan(BaseModel):
    document_id: str
    replacements: List[TextReplacement]