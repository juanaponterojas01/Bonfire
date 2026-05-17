"""Track job applications in a persistent CSV history log.

Provides functions to record job descriptions and update their application
state (e.g. ``"pending"`` → ``"applied"`` → ``"rejected"``).  The CSV
is stored at ``data/job-history.csv`` and is automatically created on
first use.
"""

from __future__ import annotations

import csv
from pathlib import Path

from src.models import JobDescription

JOB_HISTORY_PATH = Path("data/job-history.csv")
"""Path to the CSV file that stores the job application history.

The file is created automatically on first use with a header row.
Each row represents one job application and tracks its current state
(e.g. ``pending``, ``sent``, ``rejected``).
"""
_HEADERS = ["title", "company", "location", "receiver_name", "email", "required_topics", "url_or_file", "state"]


def _ensure_file_with_headers(path: Path | None = None) -> None:
    """Create the CSV file (and its parent directory) with a header row if
    it does not already exist.

    Args:
        path: Override for the CSV path (used in tests).  Defaults to
            ``JOB_HISTORY_PATH``.
    """
    target = path or JOB_HISTORY_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        with target.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(_HEADERS)


def log_job_entry(
    job: JobDescription,
    source: str,
    state: str = "pending",
    *,
    path: Path | None = None,
) -> bool:
    """Append a job description to the history CSV unless a duplicate exists.

    Duplicates are detected by matching both ``company`` **and**
    ``title``.  If a row with the same pair already exists the entry is
    silently skipped.

    Args:
        job: The ``JobDescription`` to record.
        source: URL or file path from which the job was obtained.
        state: Initial application state (default ``"pending"``).
        path: Override for the CSV path (used in tests).

    Returns:
        ``True`` if the row was appended, ``False`` if it was skipped
        because of a duplicate.
    """
    target = path or JOB_HISTORY_PATH
    _ensure_file_with_headers(target)

    # Check for an existing (company, title) pair
    with target.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["company"] == job.company and row["title"] == job.title:
                return False

    # Append the new row
    with target.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            job.title,
            job.company,
            job.location,
            job.receiver_name or "",
            job.email,
            ";".join(job.required_topics),
            source,
            state,
        ])
    return True


def update_job_state(
    company: str,
    title: str,
    state: str,
    *,
    path: Path | None = None,
) -> bool:
    """Update the ``state`` column for the first row matching *company*
    and *title*.

    The entire CSV is read into memory, updated, and written back so
    that the file remains on disk even if an unexpected error occurs
    part-way through.

    Args:
        company: Company name to match.
        title: Job title to match.
        state: New value for the ``state`` column.
        path: Override for the CSV path (used in tests).

    Returns:
        ``True`` if a matching row was found and updated, ``False``
        otherwise.
    """
    target = path or JOB_HISTORY_PATH
    _ensure_file_with_headers(target)

    rows: list[dict[str, str]] = []
    with target.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    updated = False
    for row in rows:
        if row["company"] == company and row["title"] == title:
            row["state"] = state
            updated = True
            break

    if updated:
        with target.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=_HEADERS)
            writer.writeheader()
            writer.writerows(rows)

    return updated
