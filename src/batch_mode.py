"""Batch processing helpers for job applications.

Supports parsing a batch list file (URLs or local file paths) and tracking
the state of each job through a persistent JSON file so that the orchestrator
can process multiple applications sequentially without redoing work.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

#: Persistent JSON file tracking per-source application status.
_STATE_PATH = Path("data/batch_state.json")


def parse_batch_list(path: str) -> list[str]:
    """Read a batch list file and return validated source strings.

    Each non-empty, non-comment line is treated as either a URL or a local
    file path.  URLs are kept as-is; file paths are resolved to an absolute
    path and checked for existence on disk.  At most 10 entries are allowed.

    Args:
        path: Filesystem path to the batch list text file.

    Returns:
        Validated list of source strings (URLs or absolute file paths).

    Raises:
        FileNotFoundError: If *path* itself does not exist, or if a listed
            local file path cannot be found on disk.
        ValueError: If the filtered list contains more than 10 entries.
    """
    batch_file = Path(path)

    with batch_file.open("r", encoding="utf-8") as fh:
        raw_lines = fh.readlines()

    sources: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("http://", "https://")):
            sources.append(stripped)
        else:
            resolved = Path(stripped).resolve()
            if not resolved.exists():
                raise FileNotFoundError(f"Batch file not found: {resolved}")
            sources.append(str(resolved))

    if len(sources) > 15:
        raise ValueError("Batch limit exceeded: maximum 15 jobs allowed")

    return sources


def _ensure_state_dir() -> None:
    """Create the parent directory of ``_STATE_PATH`` if it does not exist."""
    _STATE_PATH.parent.mkdir(parents=True, exist_ok=True)


def _load_state() -> dict[str, dict]:
    """Load the batch state from the persistent JSON file.

    Returns:
        The deserialized state dictionary, or an empty ``dict`` if the
        state file does not exist yet.
    """
    _ensure_state_dir()
    if not _STATE_PATH.exists():
        return {}
    with _STATE_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _save_state(state: dict) -> None:
    """Persist *state* to the batch state JSON file.

    Args:
        state: The complete state dictionary to write.
    """
    _ensure_state_dir()
    with _STATE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False)


def is_already_processed(source: str) -> bool:
    """Check whether *source* has already been processed successfully.

    Args:
        source: A URL or absolute file path previously returned by
            :func:`parse_batch_list`.

    Returns:
        ``True`` if the source exists in state with ``"status": "success"``.

    Raises:
        json.JSONDecodeError: If the state file exists but contains invalid
            JSON.
    """
    state = _load_state()
    return state.get(source, {}).get("status") == "success"


def mark_job(
    source: str,
    status: str,
    output_dir: str | None = None,
) -> None:
    """Record the processing result for a single batch job.

    Args:
        source: A URL or absolute file path identifying the job.
        status: The processing outcome (e.g. ``"success"`` or ``"failed"``).
        output_dir: Optional path to the directory where generated
            artifacts were written.

    Raises:
        json.JSONDecodeError: If the state file exists but contains invalid
            JSON.
        OSError: If the state file cannot be written to disk.
    """
    state = _load_state()
    entry: dict = {
        "status": status,
        "timestamp": datetime.now().isoformat(),
    }
    if output_dir is not None:
        entry["output_dir"] = output_dir
    state[source] = entry
    _save_state(state)


def get_batch_summary() -> dict[str, int]:
    """Return aggregate counts for the batch run.

    Returns:
        A dictionary with keys ``"total"``, ``"success"``, and ``"failed"``.
        ``"failed"`` counts every entry whose status is not ``"success"``.

    Raises:
        json.JSONDecodeError: If the state file exists but contains invalid
            JSON.
    """
    state = _load_state()
    total = len(state)
    success = sum(1 for v in state.values() if v.get("status") == "success")
    return {
        "total": total,
        "success": success,
        "failed": total - success,
    }
