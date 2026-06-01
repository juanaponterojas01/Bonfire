# Bonfire — AI-Powered Job Application Generator

**Version:** 0.1.0

**Bonfire** is an LLM-driven pipeline that automatically generates tailored cover letters and CVs from a single job posting. It takes job advertisement text, extracts structured information, writes personalized application documents, and renders them into professional DOCX and PPTX templates — all from the command line.

Built for job seekers, automation enthusiasts, and AI agents, Bonfire handles the repetitive parts of job applications so you can focus on what matters.

This program allows the creation of personalized application documents based on the user's own background and style for cover letters and resumes, so the generated documents don't seem generic.

* User background can be provided via text files like `.md`. It is possible to extract this information from degree certificates and PDFs using Python libraries like `pypdf` or tools like PDF OCR. Most current AI assistants are able to do this.
* Your own document style can be defined by creating templates as `.docx` and `.pptx` files.

---

## Features

- **🤖 LLM-Powered Content Generation** — Uses a dual-model architecture: a fast extraction model for structured JSON tasks and a creative writer model for natural-sounding prose.
- **📄 End-to-End Pipeline** — From raw job text to polished DOCX cover letter and PPTX CV in a single command.
- **🌍 Multi-Language Support** — Generate applications in English, German, and Spanish out of the box.
- **🎨 Fully Customizable** — Swap in your own DOCX/PPTX templates with `[placeholder]` strings. Tweak system prompts to match your industry, tone, or personal style.
- **⚡ Parallelized Pipeline** — Profile loading, job parsing, and content generation run in parallel threads via `ThreadPoolExecutor`, cutting total runtime by ~40–50%.
- **🧩 Structured Profile Extraction** — Reads your background from Markdown files and extracts a validated Pydantic `UserProfile` with skills, education, experience, and projects.
- **⚙️ Automation-Ready** — Designed to be invoked by AI agents (like OpenClaw) to fully automate the job search → application pipeline.
- **🔑 Minimal Setup** — Single environment variable (`OPENCODE_API_KEY`), simple CLI, no databases or web servers.
- **📦 Batch Processing** — Process multiple job postings in a single run with automatic state tracking and resume capability.

---

## Architecture

Bonfire is organized as a sequential pipeline, with each step handled by a dedicated module:

```
Job Posting (raw text)
       │
       V
┌────────────────────┐     ┌───────────────────────┐
│  profile_extractor │ ───>|  user_profile.json    │
│  (MD → structured) │     │  (cached Pydantic)    │
└────────────────────┘     └───────────────────────┘
       │
       V        ┌───────────────────┐
       ├───────>│  job_evaluator    │───> JobDescription (title, company,
       │        │  (LLM extraction) │     location, topics, receiver)
       │        └───────────────────┘
       │
       │        ┌───────────────────┐
       └───────>│  content_writer   │───> Cover letter body (free text)
                │  (LLM generation) │───> CVDynamicZones (structured JSON)
                │                   │───> email.yaml (inline format)
                └───────────────────┘
                       │
                       V
       ┌───────────────────┐    ┌───────────────────────┐
       │  docx_generator   │───>|  cover_letter.docx    │
       │  (template fill)  │    └───────────────────────┘
       └───────────────────┘
              │
              V
       ┌──────────────────┐    ┌───────────────────────┐
       │  pptx_generator  │───>|  cv.pptx              │
       │  (template fill) │    └───────────────────────┘
       └──────────────────┘
```

> **Note on performance:** Profile loading, job parsing, and background reading run in parallel via `ThreadPoolExecutor`. Cover-letter generation, CV dynamic-zone generation, and email generation also run in parallel, cutting the effective critical path from five sequential LLM calls to two parallel rounds.

### Key Modules

| Module | Responsibility |
|---|---|
| `src/orchestrator.py` | Pipeline coordinator — loads profile, runs all steps, returns output paths |
| `src/profile_extractor.py` | Reads `data/background_md/*.md` and extracts a structured `UserProfile` via LLM |
| `src/job_evaluator.py` | Parses raw job text into `JobDescription` (title, company, location, topics, receiver name with gender) |
| `src/content_writer.py` | Generates cover letter body (writer model) and CV dynamic zones (extraction model) |
| `src/docx_generator.py` | Renders cover letters by replacing `[placeholder]` strings in DOCX templates |
| `src/pptx_generator.py` | Renders CVs by replacing `[placeholder]` strings in PPTX templates |
| `src/llm_client.py` | Lightweight LLM client wrapping `litellm` with two-model support and JSON parsing |
| `src/models.py` | Pydantic models: `UserProfile`, `JobDescription`, `CVDynamicZones`, `PersonalInfo`, etc. |
| `src/utils.py` | Date formatting, localized filename generation, `render_prompt()` template loader |
| `src/batch_mode.py` | Batch list parsing, state tracking, and summary for multi-job runs |
| `src/config.py` | Loads runtime settings from `config.yaml` (model names, temperature, API config) |

### Data Models

All data is validated through Pydantic models defined in `src/models.py`:

- **`PersonalInfo`** — Name, address, email, phone, LinkedIn
- **`Education`** — Degree, institution, subjects, thesis title, year
- **`ProjectSummary`** — Project/experience entry with name, type, role, duration, technologies, topics
- **`Skill`** — Skill with category (technical/software/language/soft) and proficiency level
- **`UserProfile`** — Top-level profile aggregating personal info, education, experience, skills, projects
- **`JobDescription`** — Job title, company, location, receiver name, contact email, raw text, required topics
- **`CVDynamicZones`** — AI-generated professional summary, bachelor subjects, master subjects

---

## Customization

Bonfire is designed to be deeply customizable without touching the core pipeline logic.

### 1. DOCX / PPTX Templates

Create your own cover letter and CV templates using any word processor or presentation software. Insert `[placeholder]` strings where you want dynamic content to appear:

| Placeholder | Source |
|---|---|
| `[date]` | Today's date (localized) |
| `[company_name]` | Extracted from job posting |
| `[location]` | Extracted from job posting |
| `[greeting]` | Auto-generated salutation ("Dear Mr...") |
| `[letter_body]` | AI-generated cover letter text |
| `[professional_summary]` | AI-generated CV summary |
| `[bachelor_subjects]` | AI-generated bachelor's subjects text |
| `[master_subjects]` | AI-generated master's subjects text |

Place your templates in `templates/{lang}/` where `{lang}` is a supported language code: `en` (English), `de` (German), or `es` (Spanish).

### 2. System Prompts

Every LLM system prompt lives in `system_prompts/` as a standalone Markdown file. You can edit any prompt to change the writing style, tone, structure, or extraction behavior — no Python code changes required.

Prompts are loaded at runtime by the `render_prompt()` utility in `src/utils.py`, which:
- Reads the `.md` file from `system_prompts/<template_name>.md`
- Substitutes every `{variable_name}` placeholder with the corresponding keyword argument passed from Python
- Sorts substitutions by descending key length (longest keys first) to avoid accidental partial matches when one variable name is a substring of another
- Raises a clear `ValueError` listing any unreplaced `{variable}` placeholders, helping you diagnose mismatches between the template and the code

| Template File | Used By | Purpose | Placeholder Variables |
|---|---|---|---|
| `extract_profile.md` | `profile_extractor.py` | Extract structured `UserProfile` from Markdown background files | `{relevant_fields}` |
| `extract_job_topics.md` | `job_evaluator.py` | Select domain topics from a predefined vocabulary | `{valid_topics}` |
| `extract_job_description.md` | `job_evaluator.py` | Extract structured `JobDescription` (title, company, location, receiver, email, topics) | `{valid_topics}` |
| `cover_letter.md` | `content_writer.py` | Generate personalized 4-paragraph cover letter body | `{text_language}`, `{job_raw_text}`, `{profile_summary}`, `{relevant_details}`, `{country}` |
| `cv_dynamic_zones.md` | `content_writer.py` | Generate professional summary and subject descriptions for CV | `{text_language}` |
| `email_yaml.md` | `content_writer.py` | Generate YAML-formatted application email with subject, greeting, body, farewell | `{text_language}`, `{job_raw_text}`, `{profile_json}`, `{job_title}`, `{job_email}`, `{candidate_name}` |

> **Tip:** The topic vocabulary is defined by the `RELEVANT_FIELDS` list in `src/profile_extractor.py` and reused as `VALID_TOPICS` in `src/job_evaluator.py`. Editing that list updates the domain topics available to both extraction prompts.

### 3. LLM Models

Model selection is configured in `config.yaml` at the project root:

```yaml
models:
  extraction_model: "deepseek-v4-flash"   # For structured JSON extraction
  writer_model: "minimax-m2.7"            # For creative writing
```

Edit `config.yaml` to switch to any model available via your LLM provider API key (for instance OpenCode), based on the OpenAI API call structure. The extraction model should be good at following schemas; the writer model should be good at natural prose and also at multilingual tasks if you want to create applications in other languages. It is also strongly recommended to use fast models, so the timeout limit of the API call is harder to hit and because it allows faster automation when batch mode is being used to create multiple job applications.

You can also adjust the generation temperature for each model:

```yaml
settings:
  temperature_extraction: 0.2    # Lower = more deterministic JSON output
  temperature_writing: 0.5       # Higher = more creative prose
  timeout: 120.0                 # LLM request timeout in seconds
```

### 4. Background Data

Your professional background is stored in `data/background_md/`. Create one Markdown file per section (education, experience, projects, skills) and the LLM will extract a structured profile from them. The extracted profile is cached in `data/user_profile.json`.

---

## First Run / Examples

The project ships with ready-to-use example data so you can test the pipeline immediately without any setup beyond your API key.

- **`examples/`** — Contains fictional applicant profiles and generic DOCX/PPTX templates for all three supported languages.
  - `examples/data/background_md/` — Dummy background files for **John Smith** (EN), **Johannes Schmidt** (DE), and **Juan Pérez** (ES).
  - `examples/templates/` — Generic cover letter and CV templates with all the required `[placeholder]` strings.
- **`templates/`** and **`data/background_md/`** — These directories are for **your** real templates and background files. They are ignored by git (see `.gitignore`).

**Automatic fallback:** If you haven't added your own templates or background yet, Bonfire uses the examples automatically. The pipeline first looks in `templates/{lang}/` and `data/background_md/`; if those directories are empty, it falls back to `examples/templates/{lang}/` and `examples/data/background_md/`. This means you can run the very first test without any manual file copying.

---

## Installation

### Prerequisites

- Python **3.11 or higher**
- An LLM-provider API key

### Setup

```bash
# 1. Clone the repository
git clone <repo-url>
cd bonfire_app

# 2. (Recommended) Create a virtual environment
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Create your .env file from the example template
cp examples/.env.example .env

# 5. Edit .env and add your OpenCode API key
#    OPENCODE_API_KEY=sk-...

# Alternatively, set the environment variable directly:
# export OPENCODE_API_KEY=sk-...   # Linux/macOS
# set OPENCODE_API_KEY=sk-...      # Windows
```

### Quick Start

Once setup is complete, you can immediately test the pipeline using the included example data:

```bash
python main.py --file examples/jobs/fake_job_english.txt --language en
```

This will:
1. Load the dummy profile for **John Smith** from the example background files (automatic fallback).
2. Parse the fake English job posting for a "Senior CFD Engineer" position.
3. Generate a tailored cover letter and CV.
4. Save the output to `output/` using the generic example templates.

> **Note:** The example templates and dummy backgrounds are intentionally generic. After verifying the pipeline works, replace them with your own:
> - Add your real background Markdown files to `data/background_md/`.
> - Copy the example templates from `examples/templates/{lang}/` to `templates/{lang}/` and customize them with your branding.

### Dependencies

- `litellm>=1.83.0` — Unified LLM interface
- `python-docx>=1.1.0` — DOCX template rendering
- `python-pptx>=1.0.2` — PPTX template rendering
- `pydantic>=2.0.0` — Data validation and schemas
- `python-dotenv>=1.0.0` — Environment variable loading
- `requests>=2.31.0` — HTTP client for Jina AI URL scraping
- `openai>=1.0.0` — Underlying API transport
- `tiktoken>=0.5.0` — Token counting
- `pytest>=8.0.0` — Testing

---

## Usage

### Basic Usage

```bash
# From a job posting file (German)
python main.py --file examples/jobs/fake_job_german.txt --language de

# From raw job text (English)
python main.py --job-text "We are hiring a Senior CFD Engineer..." --language en

# From a job posting file (Spanish)
python main.py --file examples/jobs/fake_job_spanish.txt --language es

# From a URL
python main.py --url "https://example.com/careers/software-engineer" --language en

# Clean all generated output folders
python main.py --clean-output
```

### Batch Mode

Process multiple job postings in a single run with automatic state tracking:

```bash
python main.py --batch data/batch_example.txt --language en
```

**Batch file format** — A plain text file with one job source per line. Each line can be a local file path or a URL. Lines starting with `#` are ignored. Maximum 15 jobs per batch.

```
# Example batch file
examples/jobs/fake_job_english.txt
examples/jobs/fake_job_german.txt
https://example.com/careers/software-engineer
```

**State tracking** — Bonfire maintains a persistent state file at `data/batch_state.json` that records the status of every job processed (`success` or `failed`) along with the output directory. If the batch run is interrupted (e.g., a network timeout or rate limit), re-running the same command will **skip** previously successful jobs and **retry** only the failed or unfinished ones.

**Summary output** — After processing all jobs, Bonfire prints a summary:

```
Batch complete — 3 succeeded, 1 failed, 0 skipped
```

This makes batch mode ideal for automation: run a batch list, check the summary, and handle any failures programmatically.

> **Note:** `--batch` is mutually exclusive with `--file`, `--job-text`, and `--url`. Use `--clean-output` independently to reset all output folders.

### CLI Arguments

| Argument | Description |
|---|---|
| `--file` | Path to a file containing the raw job posting text |
| `--job-text` | Raw job posting text passed directly on the command line |
| `--url` | URL of a job posting to fetch and scrape |
| `--batch` | Path to a text file listing job sources (URLs or file paths, one per line) |
| `--language` | Output language: `en` (English), `de` (German), or `es` (Spanish). Default: `de` |
| `--clean-output` | Remove all generated output folders and exit |

> **Note:** `--file`, `--job-text`, `--url`, and `--batch` are mutually exclusive — you must provide exactly one (or use `--clean-output` alone).

### What Happens

The pipeline runs in two parallelized phases to minimize wall-clock time:

**Phase 1 (parallel)** — All three I/O steps kick off simultaneously:
1. **Profile Loading** — Loads `data/user_profile.json` if it exists, otherwise extracts it from `data/background_md/*.md` files (with automatic fallback to `examples/data/background_md/`).
2. **Job Parsing** — Sends the job posting to the LLM to extract title, company, location, required topics, and contact person with gender detection.
3. **Background Reading** — Loads the language-specific background summary.

**Phase 2 (parallel)** — Once Phase 1 completes, the three content-generation LLM calls run concurrently:
4. **Cover Letter Generation** — Writes a tailored 4-paragraph cover letter body using the writer model, grounded in your actual profile.
5. **CV Dynamic Zones** — Generates a professional summary and subject descriptions tailored to the job.
6. **Email Generation** — Generates a concise YAML-formatted application email with subject, recipient, greeting, body, and farewell using the writer model.

**Phase 3 (sequential)** — Fast, local processing:
7. **File Writing** — Saves the generated email to `email.yaml`, fills the DOCX and PPTX templates with all generated content, and writes the final files.

> **URL Scraping Limitations:** Bonfire fetches job pages via [Jina AI Reader](https://r.jina.ai/), which handles JavaScript-rendered content better than a plain HTTP request. However, some sites (e.g., LinkedIn, Indeed) block external readers or require authentication. When a URL fails because it is blocked or returns no usable text, it is automatically logged to `data/blacklist.txt` so you can avoid those sites in the future. If `--url` fails, save the text manually and use `--file` or `--job-text` instead.
>
> **Job History Logging:** Every job processed by the pipeline is automatically recorded in `data/job-history.csv` with an initial state of `pending`. This history tracks each application by company, title, location, contact email, and source URL. A future automation feature will allow updating the state to `sent` once an application has been submitted, enabling a fully automated job-search workflow.
>
> **Batch Mode State Tracking:** When using `--batch`, Bonfire maintains `data/batch_state.json` to track per-job status. This enables resume capability — re-running the same batch file will skip already-successful jobs and retry only failed or unfinished ones. The state file is JSON-formatted and can be inspected or reset manually.

### Output

Generated documents are saved to `output/{company_name}/`:

```
output/
└── Acme Corp/
    ├── J.Doe_Anschreiben.docx      (cover letter)
    ├── J.Doe_Lebenslauf.pptx       (CV)
    └── email.yaml                  (application email in LLM-generated format)
```

> **Note:** `email.yaml` is generated entirely by the LLM using an inline format prompt — no DOCX/PPTX template or post-processing is involved. The output begins with `subject:` and `to:` YAML-style fields followed by the email greeting, body, and farewell.

Filenames are localized per language and abbreviated with the user's initials (e.g., `J.Doe_cover_letter.docx`, `J.Doe_carta_de_motivación.docx`).

---

## Automation & Agent Integration

Bonfire is purpose-built for integration with AI agents like **OpenClaw** or **Hermes** to create a fully automated job application workflow:

```
1. Agent scrapes job boards or receives job postings
2. Agent downloads/clips the job description text
3. Agent invokes Bonfire:
       python main.py --file /tmp/job.txt --language de
4. Bonfire generates all application documents
5. Agent submits the application via the company portal or email
```

The pipeline returns a clean result dictionary with `success`, `reason` (on failure), and output file paths, making it trivial to integrate into larger automation scripts.

**Note:** Integration with AI agents hasn't been tested yet. Still, I think it is feasible.

### Programmatic Usage

The pipeline can also be called directly from Python:

```python
from src.orchestrator import run_job_pipeline

result = run_job_pipeline(
    job_text="We are hiring a CFD engineer...",
    language="en",
)

if result["success"]:
    print(f"Documents saved to {result['output_dir']}")
else:
    print(f"Failed: {result['reason']}")
```

---

## Project Structure

```
bonfire_app/
├── main.py                     # CLI entry point
├── config.yaml                 # Runtime configuration (models, temperatures, API)
├── .env                        # OPENCODE_API_KEY (not committed)
├── requirements.txt            # Python dependencies
│
├── data/                       # Your working data (user-specific, ignored by git)
│   ├── user_profile.json       # Cached structured profile (auto-generated)
│   ├── job-history.csv         # Job application history log (auto-generated)
│   ├── blacklist.txt           # URLs that failed scraping (auto-generated)
│   ├── batch_state.json        # Batch processing state (auto-generated)
│   ├── batch_example.txt       # Example batch list file
│   ├── background_md/          # Your real background as Markdown files
│   │   ├── background_deutsch.md
│   │   ├── background_english.md
│   │   └── background_español.md
│
├── examples/                   # Fictional example data (always committed)
│   ├── .env.example            # Template for .env (committed)                  
│   ├── data/background_md/     # Dummy profiles: John Smith, Johannes Schmidt, Juan Pérez
│   │   ├── background_deutsch.md
│   │   ├── background_english.md
│   │   └── background_español.md
│   ├── jobs/                   # Example job postings for testing
│   │   ├── fake_job_english.txt
│   │   ├── fake_job_german.txt
│   │   └── fake_job_spanish.txt
│   └── templates/              # Generic fallback templates
│       ├── de/
│       ├── en/
│       └── es/
│
├── src/
│   ├── __init__.py
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── profile_extractor.py    # User profile extraction from MD
│   ├── job_evaluator.py        # Job description extraction
│   ├── content_writer.py       # Cover letter & CV content generation
│   ├── docx_generator.py       # DOCX template rendering
│   ├── pptx_generator.py       # PPTX template rendering
│   ├── llm_client.py           # LLM client (litellm wrapper)
│   ├── models.py               # Pydantic data models
│   ├── batch_mode.py           # Batch list parsing, state tracking, summary
│   ├── config.py               # config.yaml loader with required-key validation
│   └── utils.py                # Date formatting, filenames, template rendering
│
├── system_prompts/              # LLM system prompts as editable Markdown templates
│   ├── cover_letter.md
│   ├── cv_dynamic_zones.md
│   ├── email_yaml.md
│   ├── extract_job_topics.md
│   ├── extract_job_description.md
│   └── extract_profile.md
│
├── templates/                   # Your real templates (user-specific, ignored by git)
│   ├── de/                     # German templates
│   │   ├── cover_letter_template.docx
│   │   └── cv_template.pptx
│   ├── en/                     # English templates
│   │   ├── cover_letter_template.docx
│   │   └── cv_template.pptx
│   └── es/                     # Spanish templates
│       ├── cover_letter_template.docx
│       └── cv_template.pptx
│
├── output/                     # Generated documents (auto-created)
├── tests/                      # Test suite
└── README.md                   # This file
```

> **Note:** Directories marked as "ignored by git" (`templates/`, `data/background_md/`) are reserved for your personal files. The `examples/` directory provides generic fallback content that is always committed. See `.gitignore` for the exact rules.

---

## Template Placeholders Reference

### Cover Letter Template (`cover_letter_template.docx`)

| Placeholder | Description |
|---|---|
| `[date]` | Current date in the target language (e.g., "Mai 05, 2026") |
| `[company_name]` | Company name extracted from the job posting |
| `[location]` | Job location extracted from the posting |
| `[greeting]` | Formal salutation (personalized or generic) |
| `[letter_body]` | The full AI-generated cover letter text |
| `[candidate_name]` | Your full name from `profile.personal_info.name` |
| `[candidate_address]` | Your street address from `profile.personal_info.address` |
| `[candidate_email]` | Your email address from `profile.personal_info.email` |
| `[candidate_phone]` | Your phone number from `profile.personal_info.phone` |
| `[candidate_linkedin]` | Your LinkedIn profile URL from `profile.personal_info.linkedin` |

### CV Template (`cv_template.pptx`)

| Placeholder | Description |
|---|---|
| `[professional_summary]` | 2–3 sentence career summary tailored to the job |
| `[bachelor_subjects]` | One sentence highlighting 2–3 relevant bachelor's subjects |
| `[master_subjects]` | One sentence highlighting 2–3 relevant master's subjects |

---

## Requirements

- **Python**: 3.11+
- **API Key**: A valid API key from your LLM provider (e.g., [OpenCode](https://opencode.ai)). The environment variable name is configured in `config.yaml`; the example template uses `OPENCODE_API_KEY`.
- **Operating System**: Windows, macOS, or Linux

---

## Contributing

Contributions are welcome! Here are some areas where help would be appreciated:

- **Additional language support** — Add new language mappings, prompts, and templates
- **Template gallery** — Create and share beautiful cover letter and CV templates
- **Output formats** — Support for PDF, LaTeX, or HTML output
- **Job board scrapers** — Integration modules for LinkedIn, Indeed, etc.
- **Prompt engineering** — Improve writing quality and extraction accuracy

Please open an issue or pull request on the project repository.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

## Acknowledgements

- Built with [litellm](https://github.com/BerriAI/litellm) for model-agnostic LLM access
- DOCX and PPTX manipulation via [python-docx](https://github.com/python-openxml/python-docx) and [python-pptx](https://github.com/scanny/python-pptx)
- Data validation via [Pydantic](https://docs.pydantic.dev/)
- URL scraping via [Jina AI Reader](https://r.jina.ai/)
