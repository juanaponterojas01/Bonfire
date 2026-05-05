"""
This script contains useful functions for building and managing job applications.
"""
from __future__ import annotations

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


def create_dir(dir_location: str | Path) -> None:
    """
    Create a directory at the given path. Creates parent directories as needed.

    Args:
        dir_location: The directory path to create.
    """
    try:
        Path(dir_location).mkdir(parents=True, exist_ok=True)
    except PermissionError:
        print(f"Permission denied: Unable to create '{dir_location}'.")
    except Exception as e:
        print(f"An error occurred: {e}")


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


def set_file_name(apply_doc: str, language: str, personal_info:PersonalInfo) -> str:
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
