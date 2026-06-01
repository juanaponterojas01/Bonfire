"""Tests for ``src.job_history`` using isolated temporary CSV files."""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.job_history import (
    _HEADERS,
    _ensure_file_with_headers,
    log_job_entry,
    update_job_state,
)
from src.models import JobDescription


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _make_job(
    title: str = "Software Engineer",
    company: str = "Acme Corp",
    location: str = "Remote",
    receiver_name: str | None = None,
    email: str = "",
    required_topics: list[str] | None = None,
) -> JobDescription:
    return JobDescription(
        title=title,
        company=company,
        location=location,
        receiver_name=receiver_name,
        email=email,
        raw_text="We are looking for...",
        required_topics=required_topics if required_topics is not None else ["python", "docker"],
    )


# ---------------------------------------------------------------------------
# _ensure_file_with_headers
# ---------------------------------------------------------------------------

def test_ensure_file_creates_file_and_headers(tmp_path: Path):
    """When the CSV does not exist it should be created with a header row."""
    csv_path = tmp_path / "history.csv"
    _ensure_file_with_headers(csv_path)

    assert csv_path.is_file()
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader)
        assert "email" in headers
        assert headers == _HEADERS


def test_ensure_file_creates_parent_directory(tmp_path: Path):
    """The parent directory should be created if it is missing."""
    csv_path = tmp_path / "deeply" / "nested" / "history.csv"
    _ensure_file_with_headers(csv_path)

    assert csv_path.parent.is_dir()
    assert csv_path.is_file()


def test_ensure_file_idempotent(tmp_path: Path):
    """Calling the function twice must not duplicate the header."""
    csv_path = tmp_path / "history.csv"
    _ensure_file_with_headers(csv_path)
    _ensure_file_with_headers(csv_path)

    rows = _read_csv(csv_path)
    # After two calls there should still be zero data rows.
    assert len(rows) == 0


# ---------------------------------------------------------------------------
# log_job_entry
# ---------------------------------------------------------------------------

def test_log_job_entry_writes_row(tmp_path: Path):
    """A job should be appended when the CSV is fresh."""
    csv_path = tmp_path / "history.csv"
    job = _make_job()

    result = log_job_entry(job, source="https://example.com/job/1", path=csv_path)

    assert result is True
    rows = _read_csv(csv_path)
    assert len(rows) == 1
    assert rows[0]["title"] == "Software Engineer"
    assert rows[0]["company"] == "Acme Corp"
    assert rows[0]["url_or_file"] == "https://example.com/job/1"
    assert rows[0]["state"] == "pending"


def test_log_job_entry_deduplicates_by_company_and_title(tmp_path: Path):
    """A second entry with the same company+title must return False."""
    csv_path = tmp_path / "history.csv"
    job = _make_job()

    first = log_job_entry(job, source="src_a", path=csv_path)
    second = log_job_entry(job, source="src_b", path=csv_path)

    assert first is True
    assert second is False
    rows = _read_csv(csv_path)
    assert len(rows) == 1
    assert rows[0]["url_or_file"] == "src_a"


def test_log_job_entry_allows_different_title_same_company(tmp_path: Path):
    """Different titles at the same company are treated as distinct."""
    csv_path = tmp_path / "history.csv"

    log_job_entry(_make_job(title="Backend Dev", company="ACME"), source="a", path=csv_path)
    log_job_entry(_make_job(title="Frontend Dev", company="ACME"), source="b", path=csv_path)

    rows = _read_csv(csv_path)
    assert len(rows) == 2


def test_log_job_entry_joins_required_topics(tmp_path: Path):
    """``required_topics`` should be semicolon-joined in the CSV."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(required_topics=["machine_learning", "python", "sql"])

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["required_topics"] == "machine_learning;python;sql"


def test_log_job_entry_empty_required_topics(tmp_path: Path):
    """An empty ``required_topics`` list should become an empty string."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(required_topics=[])

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["required_topics"] == ""


def test_log_job_entry_receiver_name_none(tmp_path: Path):
    """``receiver_name=None`` should be written as an empty string."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(receiver_name=None)

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["receiver_name"] == ""


def test_log_job_entry_receiver_name_present(tmp_path: Path):
    """A non-None ``receiver_name`` should be preserved."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(receiver_name="Dr. Müller")

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["receiver_name"] == "Dr. Müller"


def test_log_job_entry_email_empty_by_default(tmp_path: Path):
    """``email`` should default to an empty string in the CSV."""
    csv_path = tmp_path / "history.csv"
    job = _make_job()

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["email"] == ""


def test_log_job_entry_email_present(tmp_path: Path):
    """A non-empty ``email`` should be preserved."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(email="hr@acme.com")

    log_job_entry(job, source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["email"] == "hr@acme.com"


def test_log_job_entry_default_state_is_pending(tmp_path: Path):
    """When no *state* is passed the column should be ``"pending"``."""
    csv_path = tmp_path / "history.csv"
    log_job_entry(_make_job(), source="x", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["state"] == "pending"


def test_log_job_entry_custom_state(tmp_path: Path):
    """An explicit *state* value should be stored."""
    csv_path = tmp_path / "history.csv"
    log_job_entry(_make_job(), source="x", state="applied", path=csv_path)

    rows = _read_csv(csv_path)
    assert rows[0]["state"] == "applied"


# ---------------------------------------------------------------------------
# update_job_state
# ---------------------------------------------------------------------------

def test_update_state_finds_and_updates_matching_row(tmp_path: Path):
    """A row matching company+title should have its state changed."""
    csv_path = tmp_path / "history.csv"
    log_job_entry(_make_job(title="Dev", company="Co"), source="a", path=csv_path)
    log_job_entry(_make_job(title="QA", company="Co"), source="b", path=csv_path)

    result = update_job_state("Co", "Dev", "applied", path=csv_path)

    assert result is True
    rows = _read_csv(csv_path)
    assert rows[0]["state"] == "applied"  # Dev row
    assert rows[1]["state"] == "pending"  # QA row untouched


def test_update_state_returns_false_when_no_match(tmp_path: Path):
    """When no row matches company+title the function returns False."""
    csv_path = tmp_path / "history.csv"
    log_job_entry(_make_job(), source="a", path=csv_path)

    result = update_job_state("Nonexistent", "Ghost", "applied", path=csv_path)

    assert result is False
    # Existing row must be untouched
    rows = _read_csv(csv_path)
    assert rows[0]["state"] == "pending"


def test_update_state_only_updates_first_match(tmp_path: Path):
    """If duplicates somehow exist only the first is updated."""
    csv_path = tmp_path / "history.csv"
    job = _make_job(title="Dev", company="Co")

    # Manually create two identical rows to simulate a rare edge case.
    _ensure_file_with_headers(csv_path)
    with csv_path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Dev", "Co", "Remote", "", "", "py", "a", "pending"])
        writer.writerow(["Dev", "Co", "Remote", "", "", "py", "b", "pending"])

    result = update_job_state("Co", "Dev", "rejected", path=csv_path)
    assert result is True

    rows = _read_csv(csv_path)
    assert rows[0]["state"] == "rejected"
    assert rows[1]["state"] == "pending"


def test_update_state_on_empty_csv_returns_false(tmp_path: Path):
    """An empty CSV (headers only) has no rows to update."""
    csv_path = tmp_path / "history.csv"
    _ensure_file_with_headers(csv_path)

    result = update_job_state("Co", "Dev", "applied", path=csv_path)

    assert result is False
