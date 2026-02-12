import threading
from typing import Dict, Optional

from core.logger import get_logger
from document_intelligence.schemas.document_index import DocumentIndex

logger = get_logger(__name__)


class DocumentIndexCache:
    """
    In-memory cache (pluggable later to Redis / DB).

    Guarantees:
    - thread-safe
    - no mutation after write (defensive copies)
    """

    _lock = threading.Lock()

    # document_id -> DocumentIndex
    _store: Dict[str, DocumentIndex] = {}

    # conversation_id -> active document_id
    _active_document_by_conversation: Dict[int, str] = {}

    # -------------------------------------------------
    # DOCUMENT INDEX CACHE
    # -------------------------------------------------

    def store(self, index: DocumentIndex) -> None:
        """
        Store a defensive deep copy so cached data
        can never be mutated by callers.
        """
        with self._lock:
            self._store[index.document_id] = index.copy(deep=True)

            logger.debug(
                "INDEX_CACHED | doc_id=%s | blocks=%d",
                index.document_id,
                len(index.blocks),
            )

    def get(self, document_id: str) -> DocumentIndex:
        """
        Always return a defensive deep copy.
        Callers are free to mutate without affecting cache.
        """
        with self._lock:
            if document_id not in self._store:
                raise KeyError(f"Document not indexed: {document_id}")

            return self._store[document_id].copy(deep=True)

    def exists(self, document_id: str) -> bool:
        with self._lock:
            return document_id in self._store

    # -------------------------------------------------
    # CONVERSATION → ACTIVE DOCUMENT TRACKING
    # -------------------------------------------------

    def set_active_document(self, conversation_id: int, document_id: str) -> None:
        """
        Associate a conversation with its active document.

        This enables follow-up questions without re-uploading files.
        """
        with self._lock:
            self._active_document_by_conversation[conversation_id] = document_id

            logger.debug(
                "ACTIVE_DOCUMENT_SET | conversation_id=%s | document_id=%s",
                conversation_id,
                document_id,
            )

    def get_active_document(self, conversation_id: int) -> Optional[str]:
        """
        Resolve the active document for a conversation, if any.
        """
        with self._lock:
            return self._active_document_by_conversation.get(conversation_id)