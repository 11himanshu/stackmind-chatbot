from core.logger import get_logger
from llm.prompt import detect_intent
from llm.streaming import stream_llm_response

logger = get_logger(__name__)


class ToolRouter:
    """
    Decides how a user message should be handled.

    Responsibilities:
    - Detect intent
    - Route to correct execution path
    - Keep streaming intact

    NOTE:
    - No database access
    - No persistence
    - No side effects
    """

    @staticmethod
    def stream_response(
        *,
        message: str,
        conversation_history: list[dict]
    ):
        """
        Route the request and return a streaming generator.
        """

        intent = detect_intent(message)

        logger.info(
            "TOOL_ROUTER_DECISION | intent=%s",
            intent
        )

        # ----------------------------------------------------
        # For now, all intents still use LLM streaming.
        # Web context is already injected via prompt builder.
        #
        # Later:
        # - image_generation
        # - youtube_analysis
        # - external_tools
        # ----------------------------------------------------

        return stream_llm_response(
            message=message,
            conversation_history=conversation_history
        )