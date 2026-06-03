"""Configuration system for the Bonfire project.

Loads settings from ``config.yaml`` at the project root. Required keys
(``api.base_url``, ``api.api_key_env``, ``models.extraction_model``,
``models.writer_model``) must be present; missing required keys raise
:class:`ValueError`. Optional ``settings`` keys fall back to sensible
defaults when absent.
"""

from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ── Path to config.yaml in the project root ─────────────────────────────────
_CONFIG_PATH: Path = Path(__file__).resolve().parent.parent / "config.yaml"

# ── Required keys ────────────────────────────────────────────────────────────

_REQUIRED_API_KEYS = {"base_url", "api_key_env"}
_REQUIRED_MODELS_KEYS = {"extraction_model", "writer_model"}


@dataclass
class ApiConfig:
    """API connection settings."""

    base_url: str
    api_key_env: str


@dataclass
class ModelsConfig:
    """Model identifiers for different tasks."""

    extraction_model: str
    writer_model: str


@dataclass
class SettingsConfig:
    """Runtime parameters (temperature, timeout, token limits).

    Attributes:
        temperature_extraction: Sampling temperature for profile extraction
            (lower = more deterministic JSON).
        temperature_writing: Sampling temperature for cover letter / CV
            text (higher = more creative prose).
        timeout: Maximum time in seconds to wait for an LLM response.
        max_tokens_extraction: Maximum output tokens for profile
            extraction (JSON).
        max_tokens_writing: Maximum output tokens for cover letter / CV
            text.
    """

    temperature_extraction: float = 0.2
    temperature_writing: float = 0.5
    timeout: float = 120.0
    max_tokens_extraction: int = 8192
    max_tokens_writing: int = 4096


@dataclass
class Config:
    """Top-level configuration aggregating all sub-sections."""

    api: ApiConfig
    models: ModelsConfig
    settings: SettingsConfig = field(default_factory=SettingsConfig)


def _load_yaml_config(path: str | Path) -> dict:
    """Read and parse a YAML file, returning the resulting dict.

    Args:
        path: Path to the YAML file.

    Returns:
        The parsed dictionary, or an empty dict if the file is missing,
        empty, or contains invalid YAML.
    """
    try:
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}
    except yaml.YAMLError:
        return {}


def _build_config(raw: dict) -> Config:
    """Build a :class:`Config` from a raw dictionary.

    Args:
        raw: A dictionary with optional ``api``, ``models``, and ``settings``
            sections.

    Returns:
        A fully populated :class:`Config` instance.

    Raises:
        ValueError: If any required key is missing from *raw*.
    """
    api_raw = raw.get("api", {}) or {}
    models_raw = raw.get("models", {}) or {}
    settings_raw = raw.get("settings", {}) or {}

    missing: list[str] = []
    for key in _REQUIRED_API_KEYS:
        if key not in api_raw:
            missing.append(f"api.{key}")
    for key in _REQUIRED_MODELS_KEYS:
        if key not in models_raw:
            missing.append(f"models.{key}")

    if missing:
        raise ValueError(
            f"Missing required configuration keys in config.yaml: {', '.join(missing)}"
        )

    return Config(
        api=ApiConfig(
            base_url=api_raw["base_url"],
            api_key_env=api_raw["api_key_env"],
        ),
        models=ModelsConfig(
            extraction_model=models_raw["extraction_model"],
            writer_model=models_raw["writer_model"],
        ),
        settings=SettingsConfig(
            temperature_extraction=settings_raw.get("temperature_extraction", 0.2),
            temperature_writing=settings_raw.get("temperature_writing", 0.5),
            timeout=settings_raw.get("timeout", 120.0),
            max_tokens_extraction=settings_raw.get("max_tokens_extraction", 8192),
            max_tokens_writing=settings_raw.get("max_tokens_writing", 4096),
        ),
    )


def _load_config(path: str = str(_CONFIG_PATH)) -> Config:
    """Load configuration from a YAML file.

    Args:
        path: Path to the ``config.yaml`` file.

    Returns:
        A fully populated :class:`Config` instance.

    Raises:
        ValueError: If the file is missing, empty, or missing required keys.
    """
    raw = _load_yaml_config(path)
    if not raw:
        raise ValueError(
            f"Configuration file not found or empty: {path}. "
            "Please create a config.yaml with the required fields."
        )
    return _build_config(raw)


# Module-level singleton — loaded once at import time.
CONFIG: Config = _load_config()
