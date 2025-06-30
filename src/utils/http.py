"""HTTP helper utilities with basic retry logic."""
from __future__ import annotations

import logging
import time
from typing import Any

import httpx


LOGGER = logging.getLogger(__name__)


def safe_get(url: str, retries: int = 3, backoff: float = 1.0, **kwargs: Any) -> httpx.Response:
    """Perform a GET request with simple retry and exponential backoff.

    Parameters
    ----------
    url: str
        Target URL.
    retries: int
        Number of attempts before giving up.
    backoff: float
        Initial backoff delay in seconds.
    kwargs: Any
        Additional arguments passed to ``httpx.get``.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            resp = httpx.get(url, timeout=10, **kwargs)
        except Exception as exc:  # network error
            LOGGER.warning("safe_get network error on %s: %s", url, exc)
            if attempt >= retries:
                raise
        else:
            if resp.status_code < 400:
                return resp
            LOGGER.warning("safe_get %s returned %s", url, resp.status_code)
            if attempt >= retries:
                return resp
        time.sleep(backoff)
        backoff *= 2
