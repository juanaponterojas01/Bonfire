"""Read Markdown files from a directory.

This module provides a helper to load all ``.md`` files in a given directory
and return their contents keyed by filename stem.
"""

from pathlib import Path


def _read_md_files(md_directory: str) -> dict[str, str]:
    """Read all .md files in *md_directory* and return a mapping of filename -> content.

    Each file's stem (filename without the ``.md`` extension) is used as the
    key in the returned dictionary.

    Args:
        md_directory: Absolute or relative path to the directory containing
            ``.md`` files.

    Returns:
        A dictionary mapping each filename stem to its full text content.

    Raises:
        FileNotFoundError: When the directory contains no ``.md`` files.
    """
    md_dir = Path(md_directory)
    md_paths = sorted(md_dir.glob("*.md"))
    if not md_paths:
        raise FileNotFoundError(f"No .md files found in directory: {md_directory}")

    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in md_paths
    }
