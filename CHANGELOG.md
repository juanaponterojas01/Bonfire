# Changelog

All notable changes to Bonfire will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-06-01

First public release.

### Added
- Configurable runtime via `config.yaml` (API base URL, API key env-var name, extraction model, writer model, temperature, timeout) with required-key validation in `src/config.py`.
- Automatic path fallback in `src/orchestrator.py` — the pipeline transparently uses `examples/` when `templates/` or `data/background_md/` are empty, so a fresh clone runs without manual file copying.
- `examples/` directory with tracked dummy applicant profiles (John Smith, Johannes Schmidt, Juan Pérez), generic DOCX/PPTX templates in en/de/es, three fake job postings, and an `.env.example` template.
- MIT `LICENSE` file and `__version__ = "0.1.0"` exposed in `src/__init__.py`.
- `data/batch_example.txt` example batch list.
- `future_work.md` roadmap document tracking post-0.1.0 improvements.
- Test suite expanded to 171 tests, including `tests/test_examples.py` and `tests/test_path_fallback.py` validating publication-readiness invariants.

### Changed
- README rewritten: added Architecture, First Run/Examples, Quick Start, and Batch Mode sections; updated CLI table, project structure, config-based model documentation, and version badge.
- `requirements.txt`: removed unused `docxtpl`; added `pyyaml>=6.0`.
- `src/llm_client.py` now reads the API key from `CONFIG.api.api_key_env` instead of a hardcoded env-var name; matching docstring updated.
- System-prompts table in README now lists all 7 prompts, including `evaluate_job_match.md`.

### Fixed
- `src/llm_client.py` was hardcoding `os.getenv("OPENCODE_API_KEY")` while the config layer advertised the env-var name as configurable — now honors `CONFIG.api.api_key_env`.
- `data/job-history.csv` was tracked in the repo despite containing user-PII — now gitignored and untracked from the index.
- `src/context_selector.py` no longer carries a TODO marker referencing tiktoken (integration is tracked in `future_work.md`).
- Stale `# Or litellm if preferred` comment removed from `requirements.txt`.

### Removed
- `scripts/generate_templates.py` and the empty `scripts/` directory (template generation now happens once at publication prep).
- `docxtpl>=0.16.7` from `requirements.txt` (unused).

### Notes
- The `evaluate_job_match` function and its prompt (`system_prompts/evaluate_job_match.md`) are implemented and tested but not yet wired into the orchestrator. Surfacing the result in the pipeline is tracked in `future_work.md` as the first high-priority item.
- `tiktoken>=0.5.0` remains in `requirements.txt` for the planned accurate token-counting integration (see `future_work.md`).
