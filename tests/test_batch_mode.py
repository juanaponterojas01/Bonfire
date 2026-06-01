"""Tests for ``src.batch_mode`` using isolated temporary files."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src import batch_mode


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_batch_list(path: Path, *lines: str) -> Path:
    """Write a batch list file and return its path."""
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _touch(path: Path) -> Path:
    """Create an empty file (and parent dirs) so it exists on disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    return path


def _write_state(state_path: Path, state: dict) -> None:
    """Write a state dict to *state_path* as JSON."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _read_state(state_path: Path) -> dict:
    """Read the JSON state file at *state_path*."""
    if not state_path.exists():
        return {}
    return json.loads(state_path.read_text(encoding="utf-8"))


@pytest.fixture
def isolated_state(monkeypatch, tmp_path):
    """Redirect ``batch_mode._STATE_PATH`` to a temporary file.

    The real ``data/batch_state.json`` is never read or written during tests.
    """
    temp_state_file = tmp_path / "batch_state.json"
    monkeypatch.setattr(batch_mode, "_STATE_PATH", temp_state_file)
    return temp_state_file


# ===================================================================
# parse_batch_list
# ===================================================================

class TestParseBatchList:
    """Tests for :func:`batch_mode.parse_batch_list`."""

    def test_should_return_urls_unchanged(self, tmp_path):
        """URL entries should pass through exactly as written."""
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "https://example.com/job/1",
            "http://jobs.example.org/dev",
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == [
            "https://example.com/job/1",
            "http://jobs.example.org/dev",
        ]

    def test_should_resolve_local_paths_to_absolute(self, tmp_path):
        """Local file entries should be resolved to absolute paths."""
        cv = _touch(tmp_path / "docs" / "cv.pdf")
        cl = _touch(tmp_path / "docs" / "cover_letter.pdf")
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            str(cv),
            str(cl),
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == [str(cv.resolve()), str(cl.resolve())]

    def test_should_skip_comment_lines(self, tmp_path):
        """Lines starting with '#' should be ignored."""
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "# This is a comment",
            "https://example.com/job",
            "# Another comment",
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == ["https://example.com/job"]

    def test_should_skip_empty_lines(self, tmp_path):
        """Blank lines (or whitespace-only) should be ignored."""
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "",
            "   ",
            "https://example.com/job",
            "",
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == ["https://example.com/job"]

    def test_should_handle_mixed_content(self, tmp_path):
        """A realistic batch file mixing URLs, paths, comments, and blanks."""
        cv = _touch(tmp_path / "resume.pdf")
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "# Batch for today",
            "https://example.com/alpha",
            "",
            str(cv),
            "# skip this one for now",
            "https://example.com/beta",
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == [
            "https://example.com/alpha",
            str(cv.resolve()),
            "https://example.com/beta",
        ]

    def test_should_raise_file_not_found_for_missing_batch_file(self, tmp_path):
        """When the batch list file itself does not exist, raise FileNotFoundError."""
        missing = tmp_path / "does_not_exist.txt"

        with pytest.raises(FileNotFoundError):
            batch_mode.parse_batch_list(str(missing))

    def test_should_raise_file_not_found_for_missing_local_entry(self, tmp_path):
        """When a listed local path does not exist on disk, raise FileNotFoundError."""
        missing_file = tmp_path / "missing.pdf"
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "https://example.com/job",
            str(missing_file),
        )

        with pytest.raises(FileNotFoundError, match="Batch file not found"):
            batch_mode.parse_batch_list(str(batch_file))

    def test_should_raise_value_error_when_more_than_fifteen_entries(self, tmp_path):
        """A batch list with > 15 entries must raise ValueError."""
        cv = _touch(tmp_path / "cv.pdf")
        lines = [str(cv)] * 8 + [f"https://example.com/job/{i}" for i in range(8)]
        batch_file = _write_batch_list(tmp_path / "batch.txt", *lines)

        with pytest.raises(ValueError, match="Batch limit exceeded"):
            batch_mode.parse_batch_list(str(batch_file))

    def test_should_accept_exactly_fifteen_entries(self, tmp_path):
        """Fifteen entries is the maximum allowed and should not raise."""
        cv = _touch(tmp_path / "cv.pdf")
        lines = [str(cv)] * 8 + [f"https://example.com/job/{i}" for i in range(7)]
        batch_file = _write_batch_list(tmp_path / "batch.txt", *lines)

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert len(sources) == 15

    def test_should_treat_whitespace_only_as_empty(self, tmp_path):
        """Lines containing only spaces or tabs should be skipped."""
        batch_file = _write_batch_list(
            tmp_path / "batch.txt",
            "\t",
            "https://example.com/job",
            "   ",
        )

        sources = batch_mode.parse_batch_list(str(batch_file))

        assert sources == ["https://example.com/job"]


# ===================================================================
# is_already_processed
# ===================================================================

class TestIsAlreadyProcessed:
    """Tests for :func:`batch_mode.is_already_processed`."""

    def test_should_return_false_when_state_file_missing(self, isolated_state):
        """When no state file exists, every source is unprocessed."""
        assert isolated_state.exists() is False

        result = batch_mode.is_already_processed("https://example.com/job")

        assert result is False

    def test_should_return_false_when_source_not_in_state(self, isolated_state):
        """A source absent from the state dict is not processed."""
        _write_state(isolated_state, {"https://other.com/job": {"status": "success"}})

        result = batch_mode.is_already_processed("https://example.com/job")

        assert result is False

    def test_should_return_true_when_status_is_success(self, isolated_state):
        """A source with status 'success' is considered processed."""
        source = "https://example.com/job"
        _write_state(isolated_state, {source: {"status": "success"}})

        result = batch_mode.is_already_processed(source)

        assert result is True

    def test_should_return_false_when_status_is_failed(self, isolated_state):
        """A source with status 'failed' is not considered processed."""
        source = "https://example.com/job"
        _write_state(isolated_state, {source: {"status": "failed"}})

        result = batch_mode.is_already_processed(source)

        assert result is False

    def test_should_return_false_when_source_has_unrecognized_status(self, isolated_state):
        """Only 'success' counts as processed; any other status does not."""
        source = "https://example.com/job"
        _write_state(isolated_state, {source: {"status": "in_progress"}})

        result = batch_mode.is_already_processed(source)

        assert result is False


# ===================================================================
# mark_job
# ===================================================================

class TestMarkJob:
    """Tests for :func:`batch_mode.mark_job`."""

    def test_should_record_success_with_timestamp(self, isolated_state):
        """After marking success, the source is retrievable as processed."""
        source = "https://example.com/job"

        batch_mode.mark_job(source, "success")

        state = _read_state(isolated_state)
        assert source in state
        assert state[source]["status"] == "success"
        assert "timestamp" in state[source]

    def test_should_record_failed_status(self, isolated_state):
        """A failed job should be stored and NOT count as processed."""
        source = "https://example.com/job"

        batch_mode.mark_job(source, "failed")

        state = _read_state(isolated_state)
        assert state[source]["status"] == "failed"
        assert batch_mode.is_already_processed(source) is False

    def test_should_optionally_record_output_dir(self, isolated_state):
        """When *output_dir* is given, it should appear in the state entry."""
        source = "https://example.com/job"

        batch_mode.mark_job(source, "success", output_dir="/tmp/output/42")

        state = _read_state(isolated_state)
        assert state[source]["output_dir"] == "/tmp/output/42"

    def test_should_not_record_output_dir_when_none(self, isolated_state):
        """When *output_dir* is omitted, the key should be absent."""
        source = "https://example.com/job"

        batch_mode.mark_job(source, "success")

        state = _read_state(isolated_state)
        assert "output_dir" not in state[source]

    def test_should_overwrite_previous_state_for_same_source(self, isolated_state):
        """Marking the same source twice must replace the old entry."""
        source = "https://example.com/job"
        batch_mode.mark_job(source, "failed", output_dir="/old")

        batch_mode.mark_job(source, "success", output_dir="/new")

        state = _read_state(isolated_state)
        assert len(state) == 1
        assert state[source]["status"] == "success"
        assert state[source]["output_dir"] == "/new"

    def test_should_preserve_other_sources_when_overwriting(self, isolated_state):
        """Updating one source must not affect other entries."""
        batch_mode.mark_job("a", "failed")
        batch_mode.mark_job("b", "success")

        batch_mode.mark_job("a", "success")

        state = _read_state(isolated_state)
        assert len(state) == 2
        assert state["a"]["status"] == "success"
        assert state["b"]["status"] == "success"


# ===================================================================
# get_batch_summary
# ===================================================================

class TestGetBatchSummary:
    """Tests for :func:`batch_mode.get_batch_summary`."""

    def test_should_return_zero_counts_when_state_empty(self, isolated_state):
        """An empty state should yield all-zero counts."""
        summary = batch_mode.get_batch_summary()

        assert summary == {"total": 0, "success": 0, "failed": 0}

    def test_should_count_success_and_failed_correctly(self, isolated_state):
        """A mix of success and failed entries should produce correct tallies."""
        batch_mode.mark_job("a", "success")
        batch_mode.mark_job("b", "failed")
        batch_mode.mark_job("c", "success")
        batch_mode.mark_job("d", "failed")

        summary = batch_mode.get_batch_summary()

        assert summary == {"total": 4, "success": 2, "failed": 2}

    def test_should_count_all_success(self, isolated_state):
        """When all entries succeeded, failed should be zero."""
        for i in range(3):
            batch_mode.mark_job(f"job_{i}", "success")

        summary = batch_mode.get_batch_summary()

        assert summary == {"total": 3, "success": 3, "failed": 0}

    def test_should_count_all_failed(self, isolated_state):
        """When all entries failed, success should be zero."""
        for i in range(3):
            batch_mode.mark_job(f"job_{i}", "failed")

        summary = batch_mode.get_batch_summary()

        assert summary == {"total": 3, "success": 0, "failed": 3}

    def test_should_treat_unrecognized_status_as_failed(self, isolated_state):
        """Any status that is not 'success' counts toward the failed tally."""
        _write_state(isolated_state, {
            "a": {"status": "success"},
            "b": {"status": "in_progress"},
            "c": {"status": "pending"},
        })

        summary = batch_mode.get_batch_summary()

        assert summary == {"total": 3, "success": 1, "failed": 2}
