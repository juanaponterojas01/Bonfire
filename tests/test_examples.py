"""Verify that example assets generated in previous steps exist and are loadable."""

from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE_DIR = _PROJECT_ROOT / "examples" / "templates"
_BACKGROUND_DIR = _PROJECT_ROOT / "examples" / "data" / "background_md"

_LANGUAGES = ["en", "de", "es"]


def test_example_cover_letter_templates_exist():
    """Verify cover_letter_template.docx exists for all supported languages."""
    for lang in _LANGUAGES:
        path = _TEMPLATE_DIR / lang / "cover_letter_template.docx"
        assert path.is_file(), f"Missing: {path}"


def test_example_cv_templates_exist():
    """Verify cv_template.pptx exists for all supported languages."""
    for lang in _LANGUAGES:
        path = _TEMPLATE_DIR / lang / "cv_template.pptx"
        assert path.is_file(), f"Missing: {path}"


def test_background_md_files_exist_and_non_empty():
    """Verify each background markdown file exists and has content."""
    expected_files = [
        "background_english.md",
        "background_deutsch.md",
        "background_español.md",
    ]
    for filename in expected_files:
        path = _BACKGROUND_DIR / filename
        assert path.is_file(), f"Missing: {path}"
        assert path.stat().st_size > 0, f"Empty: {path}"


def test_background_md_files_contain_header():
    """Verify each background markdown file contains at least one '#' header."""
    for path in sorted(_BACKGROUND_DIR.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        assert "#" in content, f"No header found in {path.name}"
