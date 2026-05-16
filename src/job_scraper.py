"""Fetch and extract plain text from online job descriptions.

This module provides a single function — :func:`fetch_job_text` — that
retrieves a web page via the Jina AI Reader API and returns cleaned,
readable text suitable for downstream processing by the job-evaluation
pipeline.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

import requests

_JINA_READER_BASE = "https://r.jina.ai/"
_BLACKLIST_PATH = Path("data/blacklist.txt")


def _log_blacklist(url: str, reason: str) -> None:
    """Append *url* to the blacklist file if it is not already present."""
    _BLACKLIST_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | {url} | {reason}\n"

    existing = ""
    if _BLACKLIST_PATH.exists():
        existing = _BLACKLIST_PATH.read_text(encoding="utf-8")

    if url not in existing:
        with _BLACKLIST_PATH.open("a", encoding="utf-8") as f:
            f.write(entry)


def fetch_job_text(url: str, timeout: int = 10) -> str:
    """Fetch a job posting URL and return its plain-text content.

    Uses the Jina AI Reader API to extract clean, readable text from
    any web page.

    Args:
        url: The web address of the job posting (must use http or https).
        timeout: Maximum number of seconds to wait for the server response.

    Returns:
        Plain text of the job posting.

    Raises:
        ValueError: If the URL does not use the http or https scheme.
        RuntimeError: If the request times out, the connection fails, the
            server responds with an HTTP error, or the page yields no usable
            text.
    """
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError(
            f"Unsupported URL scheme '{parsed.scheme}'. "
            f"Only http:// and https:// are allowed."
        )

    reader_url = _JINA_READER_BASE + url

    try:
        response = requests.get(
            reader_url,
            timeout=timeout,
            allow_redirects=True,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError(
            f"Request timed out after {timeout} seconds for URL: {url}. "
            f"The server may be blocking scrapers or the page is too slow."
        ) from None
    except requests.exceptions.ConnectionError:
        raise RuntimeError(
            f"Failed to connect to {url}. "
            f"Check that the URL is correct and your network is working."
        ) from None
    except requests.exceptions.HTTPError as exc:
        status = exc.response.status_code if exc.response is not None else "?"
        reason = exc.response.reason if exc.response is not None else "Unknown"
        _log_blacklist(url, f"HTTP {status} {reason}")
        raise RuntimeError(
            f"HTTP {status} {reason} for URL: {url}. "
            f"The page may require authentication or be blocking scrapers."
        ) from None

    text = response.text.strip()

    if not text:
        _log_blacklist(url, "No usable text found")
        raise RuntimeError(
            f"No usable text found on page: {url}. "
            f"The page may be empty, JavaScript-rendered, or require "
            f"authentication."
        )

    return text
