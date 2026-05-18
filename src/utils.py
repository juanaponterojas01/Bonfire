"""
This script contains useful functions for building and managing job applications.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path

from src.models import PersonalInfo


LANGUAGES: dict[str, str] = {
    "spanish": "es",
    "german": "de",
    "english": "en",
}

_MONTHS_MAPPING: dict[str, list[str]] = {
    "January": ["Januar", "Enero"],
    "February": ["Februar", "Febrero"],
    "March": ["März", "Marzo"],
    "April": ["April", "Abril"],
    "May": ["Mai", "Mayo"],
    "June": ["Juni", "Junio"],
    "July": ["Juli", "Julio"],
    "August": ["August", "Agosto"],
    "September": ["September", "Septiembre"],
    "October": ["Oktober", "Octubre"],
    "November": ["November", "Noviembre"],
    "December": ["Dezember", "Diciembre"],
}


def create_dir(dir_location: str | Path) -> Path:
    """Create a directory at the given path. Creates parent directories as needed.

    Args:
        dir_location: The directory path to create.

    Returns:
        The created Path object.

    Raises:
        OSError: If directory creation fails.
    """
    path = Path(dir_location)
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_todays_date(language: str) -> str:
    """
    Get today's date in the specified language (en, de, es).

    Args:
        language: Language code — "en" for English, "de" for German, "es" for Spanish.

    Returns:
        Today's date formatted as a string in the requested language.
    """
    today = date.today().strftime("%B %d, %Y")
    if language == "en":
        return today

    today_as_list = today.split(" ")
    if language == "de":
        month = _MONTHS_MAPPING[today_as_list[0]][0]
    else:
        month = _MONTHS_MAPPING[today_as_list[0]][1]
    return month + " " + today_as_list[1] + " " + today_as_list[2]


def set_file_name(apply_doc: str, language: str, personal_info: PersonalInfo) -> str:
    """
    Return the localized filename for a given application document type.

    Args:
        apply_doc: Document type — "curriculum" or "motiv_letter".
        language: Language code — "en", "de", or "es".

    Returns:
        The localized filename for the requested document.

    Raises:
        ValueError: If apply_doc is not a recognized document type.
    """
    parts = personal_info.name.split()
    if len(parts) < 2:
        name_abbrev = parts[0]
    else:
        name_abbrev = parts[0][0] + "." + parts[-1]
    curriculum_mapping = {
        "en": f"{name_abbrev}_resume.pptx",
        "de": f"{name_abbrev}_Lebenslauf.pptx",
        "es": f"{name_abbrev}_hoja_de_vida.pptx",
    }

    motiv_letter_mapping = {
        "en": f"{name_abbrev}_cover_letter.docx",
        "de": f"{name_abbrev}_Anschreiben.docx",
        "es": f"{name_abbrev}_carta_de_motivación.docx",
    }

    if apply_doc == "curriculum":
        return curriculum_mapping[language]

    if apply_doc == "motiv_letter":
        return motiv_letter_mapping[language]

    raise ValueError(f"Unknown document type: '{apply_doc}'. Expected 'curriculum' or 'motiv_letter'.")


def render_prompt(template_name: str, **kwargs) -> str:
    """Load a ``.md`` template from the ``system_prompts/`` directory and
    perform safe variable substitution with mismatch detection.

    The resolved template path is ``<project_root>/system_prompts/<template_name>.md``.
    Each keyword argument ``key=value`` replaces every occurrence of the
    placeholder ``{key}`` in the template file. Substitutions are applied in
    order of descending key length (longest keys first) to prevent accidental
    partial replacement when one variable name is a substring of another.

    After substitution, the function scans the rendered text with the regex
    ``\\{[a-zA-Z_][a-zA-Z0-9_]*\\}`` to detect any remaining unreplaced
    placeholders. If any are found, a ``ValueError`` is raised, listing the
    unreplaced variables so the caller can correct the template or the
    supplied keyword arguments.

    Args:
        template_name: Name of the template file **without** the ``.md``
            extension (e.g. ``"cover_letter_system"``).
        **kwargs: One or more variable names and their replacement values.
            Each key is matched against ``{key}`` placeholders in the template
            file. The value is converted to a string via ``str()`` before
            substitution.

    Returns:
        The fully rendered template content as a UTF-8 decoded string, with
        all matched ``{variable}`` placeholders replaced by their corresponding
        values.

    Raises:
        FileNotFoundError: If the file
            ``<project_root>/system_prompts/<template_name>.md`` does not
            exist or is not a regular file.
        ValueError: If, after all substitutions have been applied, the text
            still contains unreplaced ``{variable}`` placeholders. The error
            message lists every unmatched variable name to help diagnose
            mismatches between the template and the supplied keyword arguments.
    """
    project_root = Path(__file__).resolve().parent.parent
    template_path = project_root / "system_prompts" / f"{template_name}.md"

    if not template_path.is_file():
        raise FileNotFoundError(f"Template file not found: {template_path}")

    text = template_path.read_text(encoding="utf-8")

    for key in sorted(kwargs, key=len, reverse=True):
        text = text.replace(f"{{{key}}}", str(kwargs[key]))

    leftover = re.findall(r"\{[a-zA-Z_][a-zA-Z0-9_]*\}", text)
    if leftover:
        raise ValueError(
            f"Unreplaced variable(s) found in template '{template_name}.md': "
            f"{', '.join(leftover)}. "
            "Check that the variable name in the .md file matches the kwarg "
            "passed to render_prompt()."
        )

    return text
