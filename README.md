# Bonfire — AI-Powered Job Application Generator

**Bonfire** is an LLM-driven pipeline that automatically generates tailored cover letters and CVs from a single job posting. It takes raw job advertisement text, extracts structured information, writes personalized application documents, and renders them into professional DOCX and PPTX templates — all from the command line.

Built for job seekers, automation enthusiasts, and AI agents, Bonfire handles the repetitive parts of job applications so you can focus on what matters.

---

## Features

- **🤖 LLM-Powered Content Generation** — Uses a dual-model architecture: a fast extraction model for structured JSON tasks and a creative writer model for natural-sounding prose.
- **📄 End-to-End Pipeline** — From raw job text to polished DOCX cover letter and PPTX CV in a single command.
- **🌍 Multi-Language Support** — Generate applications in English, German, and Spanish out of the box.
- **🎨 Fully Customizable** — Swap in your own DOCX/PPTX templates with `[placeholder]` strings. Tweak system prompts to match your industry, tone, or personal style.
- **✅ Content Validation** — Automatically checks generated text against your real profile to catch hallucinations.
- **🧩 Structured Profile Extraction** — Reads your background from Markdown files and extracts a validated Pydantic `UserProfile` with skills, education, experience, and projects.
- **⚙️ Automation-Ready** — Designed to be invoked by AI agents (like OpenClaw) to fully automate the job search → application pipeline.
- **🔑 Minimal Setup** — Single environment variable (`OPENCODE_API_KEY`), simple CLI, no databases or web servers.

---

## Architecture

Bonfire is organized as a sequential pipeline, with each step handled by a dedicated module:

```
Job Posting (raw text)
       │
       ▼
┌────────────────────┐     ┌───────────────────────┐
│  profile_extractor │ ───▶  user_profile.json    │
│  (MD → structured) │     │  (cached Pydantic)    │
└────────────────────┘     └───────────────────────┘
       │
       ▼
┌───────────────────┐
│  job_evaluator    │───▶ JobDescription (title, company,
│  (LLM extraction) │     location, topics, receiver)
└───────────────────┘
       │
       ▼
┌───────────────────┐
│  content_writer   │───▶ Cover letter body (free text)
│  (LLM generation) │───▶ CVDynamicZones (structured JSON)
└───────────────────┘
       │
       ▼
┌───────────────────┐
│ content_validator │───▶ Hallucination check against profile
└───────────────────┘
       │
       ▼
┌───────────────────┐    ┌───────────────────────┐
│  docx_generator   │───▶ cover_letter.docx     │
│  (template fill)  │    └───────────────────────┘
└───────────────────┘
       │
       ▼
┌──────────────────┐    ┌───────────────────────┐
│  pptx_generator  │───▶ cv.pptx               │
│  (template fill) │    └───────────────────────┘
└──────────────────┘
```

### Key Modules

| Module | Responsibility |
|---|---|
| `src/orchestrator.py` | Pipeline coordinator — loads profile, runs all steps, returns output paths |
| `src/profile_extractor.py` | Reads `data/background_md/*.md` and extracts a structured `UserProfile` via LLM |
| `src/job_evaluator.py` | Parses raw job text into `JobDescription` (title, company, location, topics, receiver name with gender) |
| `src/content_writer.py` | Generates cover letter body (writer model) and CV dynamic zones (extraction model) |
| `src/content_validator.py` | Validates generated text against the user profile to flag unsupported claims |
| `src/docx_generator.py` | Renders cover letters by replacing `[placeholder]` strings in DOCX templates |
| `src/pptx_generator.py` | Renders CVs by replacing `[placeholder]` strings in PPTX templates |
| `src/llm_client.py` | Lightweight LLM client wrapping `litellm` with two-model support and JSON parsing |
| `src/models.py` | Pydantic models: `UserProfile`, `JobDescription`, `CVDynamicZones`, `PersonalInfo`, etc. |
| `src/utils.py` | Date formatting, localized filename generation |

### Data Models

All data is validated through Pydantic models defined in `src/models.py`:

- **`PersonalInfo`** — Name, address, email, phone, LinkedIn
- **`Education`** — Degree, institution, subjects, thesis title, year
- **`ProjectSummary`** — Project/experience entry with name, type, role, duration, technologies, topics
- **`Skill`** — Skill with category (technical/software/language/soft) and proficiency level
- **`UserProfile`** — Top-level profile aggregating personal info, education, experience, skills, projects
- **`JobDescription`** — Job title, company, location, receiver name, raw text, required topics
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

Place your templates in `templates/{lang}/` where `{lang}` is `en`, `de`, or `es`.

### 2. System Prompts

Every LLM call uses a system prompt that you can edit to change writing style, tone, structure, or extraction behavior:

- **`src/profile_extractor.py`** — `PROFILE_EXTRACTION_SYSTEM_PROMPT`: Controls how the LLM extracts your profile from Markdown files. Edit the `RELEVANT_FIELDS` list to change the domain topic vocabulary.
- **`src/job_evaluator.py`** — System prompts for extracting job title, company, topics, and receiver name.
- **`src/content_writer.py`** — Prompts for cover letter generation (paragraph structure, tone per country) and CV dynamic zones.
- **`src/content_validator.py`** — Prompt for hallucination detection.

### 3. LLM Models

In `src/llm_client.py`:

```python
EXTRACTION_MODEL = "kimi-k2.5"          # For structured JSON extraction
WRITER_MODEL = "deepseek-v4-flash"        # For creative writing
```

Swap these to any model available via your OpenCode API key. The extraction model should be good at following schemas; the writer model should be good at natural prose.

### 4. Background Data

Your professional background is stored in `data/background_md/`. Create one Markdown file per section (education, experience, projects, skills) and the LLM will extract a structured profile from them. The extracted profile is cached in `data/user_profile.json`.

---

## Installation

### Prerequisites

- Python **3.11 or higher**
- An [OpenCode](https://opencode.ai) API key

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

# 4. Set your OpenCode API key
# Either create a .env file:
echo "OPENCODE_API_KEY=sk-..." > .env

# Or set an environment variable:
# export OPENCODE_API_KEY=sk-...   # Linux/macOS
# set OPENCODE_API_KEY=sk-...      # Windows
```

### Dependencies

- `litellm>=1.83.0` — Unified LLM interface
- `python-docx>=1.1.0` — DOCX template rendering
- `python-pptx>=1.0.2` — PPTX template rendering
- `pydantic>=2.0.0` — Data validation and schemas
- `python-dotenv>=1.0.0` — Environment variable loading
- `openai>=1.0.0` — Underlying API transport
- `tiktoken>=0.5.0` — Token counting
- `pytest>=8.0.0` — Testing

---

## Usage

### Basic Usage

```bash
# From a job posting file (German)
python main.py --job-file data/fake_job_german.txt --language de

# From raw job text (English)
python main.py --job-text "We are hiring a Senior CFD Engineer..." --language en

# From a job posting file (Spanish)
python main.py --job-file data/fake_job_spanish.txt --language es
```

### CLI Arguments

| Argument | Description |
|---|---|
| `--job-file` | Path to a file containing the raw job posting text |
| `--job-text` | Raw job posting text passed directly on the command line |
| `--language` | Output language: `en` (English), `de` (German), or `es` (Spanish). Default: `de` |

> **Note:** `--job-file` and `--job-text` are mutually exclusive — you must provide exactly one.

### What Happens

1. **Profile Loading** — Loads `data/user_profile.json` if it exists, otherwise extracts it from `data/background_md/*.md` files.
2. **Job Parsing** — Sends the job posting to the LLM to extract title, company, location, required topics, and contact person with gender detection.
3. **Cover Letter Generation** — Writes a tailored 4-paragraph cover letter body using the writer model, grounded in your actual profile.
4. **Content Validation** — Checks the generated letter for unsupported claims.
5. **CV Dynamic Zones** — Generates a professional summary and subject descriptions tailored to the job.
6. **Document Rendering** — Fills the templates with all generated content and saves the final files.

### Output

Generated documents are saved to `output/{company_name}/`:

```
output/
└── Acme Corp/
    ├── J.Doe_Anschreiben.docx      (cover letter)
    └── J.Doe_Lebenslauf.pptx       (CV)
```

Filenames are localized per language and abbreviated with the user's initials (e.g., `J.Doe_cover_letter.docx`, `J.Doe_carta_de_motivación.docx`).

---

## Automation & Agent Integration

Bonfire is purpose-built for integration with AI agents like **OpenClaw** to create a fully automated job application workflow:

```
1. Agent scrapes job boards or receives job postings
2. Agent downloads/clips the job description text
3. Agent invokes Bonfire:
       python main.py --job-file /tmp/job.txt --language de
4. Bonfire generates all application documents
5. Agent submits the application via the company portal or email
```

The pipeline returns a clean result dictionary with `success`, `reason` (on failure), and output file paths, making it trivial to integrate into larger automation scripts.

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
├── requirements.txt            # Python dependencies
├── .env                        # OPENCODE_API_KEY (not committed)
├── data/
│   ├── user_profile.json       # Cached structured profile (auto-generated)
│   ├── background_md/          # Your background as Markdown files
│   │   ├── background_deutsch.md
│   │   ├── background_english.md
│   │   └── background_español.md
│   ├── fake_job_german.txt     # Example job posting (DE)
│   ├── fake_job_english.txt    # Example job posting (EN)
│   └── fake_job_spanish.txt    # Example job posting (ES)
├── src/
│   ├── __init__.py
│   ├── orchestrator.py         # Pipeline coordinator
│   ├── profile_extractor.py    # User profile extraction from MD
│   ├── job_evaluator.py        # Job description extraction
│   ├── content_writer.py       # Cover letter & CV content generation
│   ├── content_validator.py    # Hallucination checking
│   ├── docx_generator.py       # DOCX template rendering
│   ├── pptx_generator.py       # PPTX template rendering
│   ├── llm_client.py           # LLM client (litellm wrapper)
│   ├── models.py               # Pydantic data models
│   └── utils.py                # Date formatting, filenames
├── templates/
│   ├── de/                     # German templates
│   │   ├── cover_letter_template.docx
│   │   └── cv_template.pptx
│   ├── en/                     # English templates
│   │   ├── cover_letter_template.docx
│   │   └── cv_template.pptx
│   └── es/                     # Spanish templates
│       ├── cover_letter_template.docx
│       └── cv_template.pptx
├── output/                     # Generated documents (auto-created)
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
└── README.md                   # This file
```

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

### CV Template (`cv_template.pptx`)

| Placeholder | Description |
|---|---|
| `[professional_summary]` | 2–3 sentence career summary tailored to the job |
| `[bachelor_subjects]` | One sentence highlighting 2–3 relevant bachelor's subjects |
| `[master_subjects]` | One sentence highlighting 2–3 relevant master's subjects |

---

## Requirements

- **Python**: 3.11+
- **API Key**: Valid `OPENCODE_API_KEY` from [OpenCode](https://opencode.ai)
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
- Powered by [OpenCode](https://opencode.ai) for inference
- DOCX and PPTX manipulation via [python-docx](https://github.com/python-openxml/python-docx) and [python-pptx](https://github.com/scanny/python-pptx)
- Data validation via [Pydantic](https://docs.pydantic.dev/)
