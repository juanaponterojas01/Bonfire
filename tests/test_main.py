"""Tests for the CLI entry point (main.py)."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

from main import _build_argument_parser, _read_job_file, main


def test_read_job_file_reads_content():
    """Verify that _read_job_file returns the contents of an existing file."""
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as tmpdir:
        path = Path(tmpdir) / "job.txt"
        path.write_text("We are hiring.", encoding="utf-8")
        assert _read_job_file(str(path)) == "We are hiring."


def test_read_job_file_not_found_exits():
    """Verify that _read_job_file exits with code 1 for a missing file."""
    with pytest.raises(SystemExit) as exc_info:
        _read_job_file("/nonexistent/path/job.txt")
    assert exc_info.value.code == 1


def test_parser_accepts_job_file():
    """Verify that --job-file with --language parses successfully."""
    parser = _build_argument_parser()
    args = parser.parse_args(["--file", "examples/jobs/fake_job_german.txt", "--language", "de"])
    assert args.file == "examples/jobs/fake_job_german.txt"
    assert args.language == "de"


def test_parser_accepts_job_text():
    """Verify that --job-text with --language parses successfully."""
    parser = _build_argument_parser()
    args = parser.parse_args(["--job-text", "Hiring a CFD engineer...", "--language", "de"])
    assert args.job_text == "Hiring a CFD engineer..."
    assert args.language == "de"


def test_parser_accepts_clean_output():
    """Verify that --clean-output alone parses successfully."""
    parser = _build_argument_parser()
    args = parser.parse_args(["--clean-output"])
    assert args.clean_output is True
    assert args.file is None
    assert args.job_text is None
    assert args.url is None


def test_parser_rejects_both_job_args():
    """Verify that providing both --job-file and --job-text raises SystemExit."""
    parser = _build_argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--file", "x", "--job-text", "y"])


def test_parser_rejects_missing_job_arg():
    """Verify that main() exits with code 1 when no input source is given."""
    with patch.object(sys, "argv", ["main.py", "--language", "de"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1


def test_parser_rejects_invalid_language():
    """Verify that an unsupported language value raises SystemExit."""
    parser = _build_argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--job-text", "Hiring...", "--language", "fr"])


def test_parser_rejects_invalid_threshold():
    """Verify that an unsupported threshold value raises SystemExit."""
    parser = _build_argument_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["--job-text", "Hiring...", "--threshold", "perfect_match"])


@patch("main.run_job_pipeline")
def test_main_success_prints_output(mock_pipeline, capsys):
    """Verify that main() prints success details, exits code 0, and passes source."""
    mock_pipeline.return_value = {
        "success": True,
        "company": "AeroTech GmbH",
        "job_title": "CFD Engineer",
        "recommendation": "strong_match",
        "output_dir": "output/AeroTech",
        "cover_letter": "output/AeroTech/cover.docx",
        "cv": "output/AeroTech/cv.pptx",
    }

    with patch.object(sys, "argv", ["main.py", "--job-text", "Hiring...", "--language", "de"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "successfully" in captured.out
    assert "AeroTech GmbH" in captured.out
    mock_pipeline.assert_called_once_with("Hiring...", "de", source="Hiring...")


@patch("main.run_job_pipeline")
def test_main_passes_source_for_url(mock_pipeline):
    """Verify that --url passes args.url as the source parameter."""
    mock_pipeline.return_value = {
        "success": True,
        "company": "Corp",
        "job_title": "Eng",
        "output_dir": "output/Corp",
        "cover_letter": "output/Corp/cl.docx",
        "cv": "output/Corp/cv.pptx",
    }
    with patch("src.job_scraper.fetch_job_text", return_value="scraped job text"):
        with patch.object(sys, "argv", ["main.py", "--url", "https://example.com/job", "--language", "en"]):
            with pytest.raises(SystemExit):
                main()
    mock_pipeline.assert_called_once_with("scraped job text", "en", source="https://example.com/job")


@patch("main.run_job_pipeline")
def test_main_passes_source_for_job_file(mock_pipeline, tmp_path):
    """Verify that --job-file passes the file path as the source parameter."""
    job_file = tmp_path / "job.txt"
    job_file.write_text("Job description here", encoding="utf-8")

    mock_pipeline.return_value = {
        "success": True,
        "company": "Corp",
        "job_title": "Eng",
        "output_dir": "output/Corp",
        "cover_letter": "output/Corp/cl.docx",
        "cv": "output/Corp/cv.pptx",
    }
    with patch.object(sys, "argv", ["main.py", "--file", str(job_file), "--language", "de"]):
        with pytest.raises(SystemExit):
            main()

    mock_pipeline.assert_called_once_with("Job description here", "de", source=str(job_file))


@patch("main.run_job_pipeline")
def test_main_passes_source_for_job_text_truncated(mock_pipeline):
    """Verify --job-text passes first 80 chars as source."""
    long_text = "A" * 120
    mock_pipeline.return_value = {
        "success": True,
        "company": "Corp",
        "job_title": "Eng",
        "output_dir": "output/Corp",
        "cover_letter": "output/Corp/cl.docx",
        "cv": "output/Corp/cv.pptx",
    }
    with patch.object(sys, "argv", ["main.py", "--job-text", long_text, "--language", "es"]):
        with pytest.raises(SystemExit):
            main()

    mock_pipeline.assert_called_once_with(long_text, "es", source=long_text[:80])


@patch("main.run_job_pipeline")
def test_main_failure_prints_error(mock_pipeline, capsys):
    """Verify that main() prints the failure reason and exits with code 1."""
    mock_pipeline.return_value = {
        "success": False,
        "reason": "Job mismatch",
        "recommendation": "weak_match",
    }

    with patch.object(sys, "argv", ["main.py", "--job-text", "Hiring...", "--language", "de"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "Job mismatch" in captured.out
    assert "weak_match" in captured.out


# ---------------------------------------------------------------------------
# --clean-output tests
# ---------------------------------------------------------------------------

def test_clean_output_alone_removes_dirs(tmp_path, capsys, monkeypatch):
    """--clean-output alone removes output/ subdirectories and exits 0."""
    monkeypatch.chdir(tmp_path)
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "SomeCompany").mkdir()
    (output_dir / "OtherCompany").mkdir()
    (output_dir / "keep_me.txt").write_text("file, not a dir")

    with patch.object(sys, "argv", ["main.py", "--clean-output"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "All output folders removed." in captured.out
    assert not (output_dir / "SomeCompany").exists()
    assert not (output_dir / "OtherCompany").exists()
    assert (output_dir / "keep_me.txt").exists()  # files are not removed


def test_clean_output_combined_with_job_file_errors(capsys):
    """--clean-output + --job-file prints error and exits 1."""
    with patch.object(sys, "argv", ["main.py", "--clean-output", "--file", "x.txt"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "cannot be combined" in captured.err


def test_clean_output_combined_with_url_errors(capsys):
    """--clean-output + --url prints error and exits 1."""
    with patch.object(sys, "argv", ["main.py", "--clean-output", "--url", "https://x.com"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "cannot be combined" in captured.err


def test_clean_output_combined_with_job_text_errors(capsys):
    """--clean-output + --job-text prints error and exits 1."""
    with patch.object(sys, "argv", ["main.py", "--clean-output", "--job-text", "Hiring"]):
        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1

    captured = capsys.readouterr()
    assert "cannot be combined" in captured.err
