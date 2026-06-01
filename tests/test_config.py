"""Tests for the configuration system in src.config.py."""

import yaml

import src.config
from src.config import (
    ApiConfig,
    Config,
    ModelsConfig,
    SettingsConfig,
    _build_config,
    _load_yaml_config,
)


# ── Dataclass construction ───────────────────────────────────────────────


def test_api_config_requires_both_arguments():
    """ApiConfig requires base_url and api_key_env; missing args raise TypeError."""
    api = ApiConfig(base_url="https://example.com", api_key_env="MY_KEY")
    assert api.base_url == "https://example.com"
    assert api.api_key_env == "MY_KEY"


def test_models_config_requires_both_arguments():
    """ModelsConfig requires extraction_model and writer_model."""
    models = ModelsConfig(extraction_model="gpt-4", writer_model="gpt-3.5")
    assert models.extraction_model == "gpt-4"
    assert models.writer_model == "gpt-3.5"


def test_settings_config_uses_defaults_when_instantiated_with_no_args():
    """SettingsConfig() without arguments uses built-in defaults."""
    settings = SettingsConfig()

    assert settings.temperature_extraction == 0.2
    assert settings.temperature_writing == 0.5
    assert settings.timeout == 120.0


def test_config_requires_api_and_models():
    """Config requires api and models; settings is optional and defaults."""
    cfg = Config(
        api=ApiConfig(base_url="https://example.com", api_key_env="KEY"),
        models=ModelsConfig(extraction_model="a", writer_model="b"),
    )
    assert cfg.api.base_url == "https://example.com"
    assert cfg.models.extraction_model == "a"
    assert cfg.settings.timeout == 120.0


# ── _load_yaml_config ────────────────────────────────────────────────────


def test_load_yaml_config_returns_parsed_dict_for_valid_yaml(tmp_path):
    """Returns the parsed dictionary when the file contains valid YAML."""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("api:\n  base_url: https://example.com\n  api_key_env: MY_KEY\n")

    result = _load_yaml_config(yaml_file)

    assert result == {"api": {"base_url": "https://example.com", "api_key_env": "MY_KEY"}}


def test_load_yaml_config_returns_empty_dict_when_file_missing(tmp_path):
    """Returns an empty dict when the path does not exist."""
    nonexistent = tmp_path / "does_not_exist.yaml"
    result = _load_yaml_config(nonexistent)
    assert result == {}


def test_load_yaml_config_returns_empty_dict_for_malformed_yaml(tmp_path):
    """Returns an empty dict when the file contains invalid YAML."""
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text(": : : broken: [")

    result = _load_yaml_config(yaml_file)

    assert result == {}


def test_load_yaml_config_returns_empty_dict_for_empty_file(tmp_path):
    """Returns an empty dict when the file exists but is empty."""
    yaml_file = tmp_path / "empty.yaml"
    yaml_file.write_text("")

    result = _load_yaml_config(yaml_file)

    assert result == {}


# ── _build_config ────────────────────────────────────────────────────────


def test_build_config_raises_when_empty_dict():
    """Passing an empty dict raises ValueError because required keys are missing."""
    import pytest

    with pytest.raises(ValueError, match="Missing required configuration keys"):
        _build_config({})


def test_build_config_with_full_dict_uses_all_provided_values():
    """Passing a complete YAML dict uses every provided value."""
    raw = {
        "api": {"base_url": "https://custom.example.com", "api_key_env": "CUSTOM_KEY"},
        "models": {"extraction_model": "custom-extract", "writer_model": "custom-write"},
        "settings": {
            "temperature_extraction": 0.8,
            "temperature_writing": 0.9,
            "timeout": 300,
        },
    }

    cfg = _build_config(raw)

    assert cfg.api.base_url == "https://custom.example.com"
    assert cfg.api.api_key_env == "CUSTOM_KEY"
    assert cfg.models.extraction_model == "custom-extract"
    assert cfg.models.writer_model == "custom-write"
    assert cfg.settings.temperature_extraction == 0.8
    assert cfg.settings.temperature_writing == 0.9
    assert cfg.settings.timeout == 300


def test_build_config_raises_when_models_section_missing():
    """When only the 'api' section is present, models missing raises ValueError."""
    import pytest

    raw = {"api": {"base_url": "https://custom.example.com", "api_key_env": "KEY"}}

    with pytest.raises(ValueError, match="Missing required configuration keys"):
        _build_config(raw)


def test_build_config_uses_defaults_for_optional_settings_keys():
    """When a section exists but is missing optional keys, those keys fall back to defaults."""
    raw = {
        "api": {"base_url": "https://partial.example.com", "api_key_env": "KEY"},
        "models": {"extraction_model": "a", "writer_model": "b"},
        "settings": {"timeout": 60},
    }

    cfg = _build_config(raw)

    assert cfg.api.base_url == "https://partial.example.com"
    assert cfg.api.api_key_env == "KEY"
    assert cfg.models.extraction_model == "a"
    assert cfg.models.writer_model == "b"
    assert cfg.settings.timeout == 60
    assert cfg.settings.temperature_extraction == 0.2
    assert cfg.settings.temperature_writing == 0.5


# ── CONFIG singleton ─────────────────────────────────────────────────────


def test_config_singleton_is_valid_config_instance():
    """The module-level CONFIG object is a properly constructed Config."""
    cfg = src.config.CONFIG

    assert isinstance(cfg, Config)
    assert isinstance(cfg.api, ApiConfig)
    assert isinstance(cfg.models, ModelsConfig)
    assert isinstance(cfg.settings, SettingsConfig)


def test_config_singleton_has_all_required_attributes():
    """CONFIG exposes every expected attribute through its sub-dataclasses."""
    cfg = src.config.CONFIG

    # api
    assert hasattr(cfg.api, "base_url")
    assert hasattr(cfg.api, "api_key_env")
    # models
    assert hasattr(cfg.models, "extraction_model")
    assert hasattr(cfg.models, "writer_model")
    # settings
    assert hasattr(cfg.settings, "temperature_extraction")
    assert hasattr(cfg.settings, "temperature_writing")
    assert hasattr(cfg.settings, "timeout")


def test_config_singleton_values_are_non_empty():
    """Every CONFIG field resolves to a non-empty, usable value."""
    cfg = src.config.CONFIG

    assert cfg.api.base_url
    assert cfg.api.api_key_env
    assert cfg.models.extraction_model
    assert cfg.models.writer_model
    assert isinstance(cfg.settings.temperature_extraction, float)
    assert isinstance(cfg.settings.temperature_writing, float)
    assert isinstance(cfg.settings.timeout, (int, float))
    assert cfg.settings.timeout > 0


def test_config_singleton_values_match_real_config_yaml():
    """CONFIG values reflect the actual config.yaml in the project root."""
    cfg = src.config.CONFIG
    config_path = src.config._CONFIG_PATH

    with config_path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    assert cfg.api.base_url == raw["api"]["base_url"]
    assert cfg.api.api_key_env == raw["api"]["api_key_env"]
    assert cfg.models.extraction_model == raw["models"]["extraction_model"]
    assert cfg.models.writer_model == raw["models"]["writer_model"]
    assert cfg.settings.temperature_extraction == raw["settings"]["temperature_extraction"]
    assert cfg.settings.temperature_writing == raw["settings"]["temperature_writing"]
    assert cfg.settings.timeout == raw["settings"]["timeout"]
