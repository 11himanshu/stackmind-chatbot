import os
import time
import requests
from requests.exceptions import ReadTimeout, ConnectionError, HTTPError

from core.logger import get_logger

logger = get_logger(__name__)

ENABLE_WEB_SEARCH = os.getenv("ENABLE_WEB_SEARCH", "false").lower() == "true"

# ============================================================
# CONFIG (explicit, safe defaults)
# ============================================================

MAX_RETRIES = 3                 # total attempts
INITIAL_BACKOFF_SECONDS = 1     # exponential base
REQUEST_TIMEOUT_SECONDS = 8


def run_web_search(query: str) -> str:
    """
    Perform a safe, read-only web search with resilience.

    Guarantees:
    - No raw URLs returned
    - Short, summarized text only
    - Exponential backoff on transient failures
    - Failure-safe (never crashes chat)
    """

    if not ENABLE_WEB_SEARCH:
        logger.info("WEB_SEARCH_DISABLED")
        return ""

    api_key = os.getenv("SERPAPI_API_KEY")
    if not api_key:
        logger.warning("WEB_SEARCH_NO_API_KEY")
        return ""

    logger.info("WEB_SEARCH_START | query=%s", query)

    backoff = INITIAL_BACKOFF_SECONDS

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                "https://serpapi.com/search",
                params={
                    "q": query,
                    "engine": "bing",
                    "api_key": api_key,
                    "num": 5
                },
                timeout=REQUEST_TIMEOUT_SECONDS
            )

            # Explicit status handling
            if response.status_code == 401 or response.status_code == 403:
                logger.error(
                    "WEB_SEARCH_AUTH_FAILED | status=%s",
                    response.status_code
                )
                return ""

            if response.status_code == 429:
                logger.warning(
                    "WEB_SEARCH_RATE_LIMITED | attempt=%d",
                    attempt
                )
                raise HTTPError("Rate limited")

            response.raise_for_status()

            data = response.json()

            snippets = []
            for r in data.get("organic_results", [])[:3]:
                snippet = r.get("snippet")
                if snippet:
                    snippets.append(snippet)

            result = "\n".join(snippets)

            logger.info(
                "WEB_SEARCH_SUCCESS | snippets=%d | attempt=%d",
                len(snippets),
                attempt
            )
            return result

        except ReadTimeout:
            logger.warning(
                "WEB_SEARCH_TIMEOUT | attempt=%d | backoff=%ss",
                attempt,
                backoff
            )

        except ConnectionError:
            logger.warning(
                "WEB_SEARCH_CONNECTION_ERROR | attempt=%d | backoff=%ss",
                attempt,
                backoff
            )

        except HTTPError as e:
            logger.warning(
                "WEB_SEARCH_HTTP_ERROR | attempt=%d | error=%s",
                attempt,
                str(e)
            )

        except Exception:
            logger.exception(
                "WEB_SEARCH_UNKNOWN_FAILURE | attempt=%d",
                attempt
            )

        # Backoff before next retry (if any left)
        if attempt < MAX_RETRIES:
            time.sleep(backoff)
            backoff *= 2

    logger.error(
        "WEB_SEARCH_FAILED_AFTER_RETRIES | attempts=%d",
        MAX_RETRIES
    )
    return ""