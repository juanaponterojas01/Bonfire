"""Extract a structured :class:`UserProfile` from background markdown files.

This module provides the first layer of the Bonfire pipeline. It reads
candidate background information from a directory of Markdown files and
uses an LLM to build a structured ``UserProfile`` object, which is then
validated via Pydantic and persisted as JSON.
"""

import json
from pathlib import Path

from src.models import UserProfile
from src.llm_client import call_llm_parsed
from src.config import CONFIG
from src.utils import render_prompt

RELEVANT_FIELDS = [
    "thermal_simulation", "cfd", "experiments", "mechanical_design",
    "turbomachines", "renewable_energy", "fluid_dynamics", "thermodynamics",
    "programming", "machine_learning","agentic workflows"
]


def _read_md_files(md_source: str) -> dict[str, str]:
    """Read all .md files from *md_source* and return a mapping of filename -> content.

    *md_source* may be either a directory or a single ``.md`` file path.
    When a directory is given, every ``.md`` file inside it is read.  When a
    file is given, only that file is read.

    Each file's stem (filename without the ``.md`` extension) is used as the
    key in the returned dictionary.

    Args:
        md_source: Absolute or relative path to a directory containing
            ``.md`` files, or to a single ``.md`` file.

    Returns:
        A dictionary mapping each filename stem to its full text content.

    Raises:
        FileNotFoundError: When *md_source* does not exist or contains no
            ``.md`` files.
    """
    md_path = Path(md_source)
    if md_path.is_file() and md_path.suffix == ".md":
        return {md_path.stem: md_path.read_text(encoding="utf-8")}

    md_paths = sorted(md_path.glob("*.md"))
    if not md_paths:
        raise FileNotFoundError(f"No .md files found in directory: {md_source}")

    return {
        path.stem: path.read_text(encoding="utf-8")
        for path in md_paths
    }


def _build_extraction_prompt(md_contents: dict[str, str]) -> str:
    """Build a single user prompt from all markdown file contents.

    Args:
        md_contents: Mapping of filenames to their full Markdown content.

    Returns:
        A single string that concatenates every file under a ``### FILE:``
        header, suitable as the ``user_prompt`` for the LLM extraction call.
    """
    sections = [f"### FILE: {filename}\n{content}" for filename, content in md_contents.items()]

    header = "Below are the candidate's background documents. Extract a complete UserProfile from them.\n\n"
    return header + "\n\n---\n\n".join(sections)


def extract_profile_from_md(md_source: str, output_json_path: str) -> UserProfile:
    """Extract a UserProfile from Markdown background file(s).

    Reads ``.md`` file(s) from *md_source* (a directory or a single file),
    builds an extraction prompt from their contents, calls the LLM with a
    structured output schema, and persists the validated result to the given
    JSON path.

    Args:
        md_source: Path to a directory containing ``.md`` files, or to a
            single ``.md`` file with candidate background information.
        output_json_path: Filesystem path where the validated profile will
            be written as pretty-printed JSON.

    Returns:
        The validated :class:`UserProfile` instance.

    Raises:
        FileNotFoundError: If *md_source* does not exist or contains no
            ``.md`` files (propagated from :func:`_read_md_files`).
        ValidationError: If the LLM output does not conform to the
            :class:`UserProfile` schema (propagated from Pydantic).
    """
    md_contents = _read_md_files(md_source)
    user_prompt = _build_extraction_prompt(md_contents)

    profile = call_llm_parsed(
        system_prompt=render_prompt(
            "extract_profile",
            relevant_fields=RELEVANT_FIELDS,
        ),
        user_prompt=user_prompt,
        model=CONFIG.models.extraction_model,
        temperature=0.2,
        response_model=UserProfile,
    )

    output_path = Path(output_json_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(profile.model_dump(), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    return profile
