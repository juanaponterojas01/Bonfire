"""Layer 2 of the context management system: select the most relevant background
details for a given job description.

This module implements the selection and scoring logic that determines which
project and experience details to include in the context window passed to the
AI matching engine. It consumes the Pydantic models defined in
:mod:`src.models` (in particular :class:`ProjectSummary`, :class:`UserProfile`,
and :class:`JobDescription`) and returns a concatenated, relevance-sorted
string of Markdown content within a configurable token budget.

Two modes are supported:

1.  **Multi-file mode** (backward-compatible) — accepts a ``md_files`` dict
    mapping filename stems to Markdown content. Projects and experience entries
    are scored against job topics, matched to files via heuristic name
    matching, and included within the budget.

2.  **Single-text mode** (hybrid) — accepts a single ``background_text`` string
    whose sections (delimited by ``###`` / ``####`` headers) are scored against
    the structured ``UserProfile``. A compact skills block relevant to the job
    is prepended, and sections are selected by score within the token budget.

The selection process for multi-file mode follows a two-phase approach:

1.  **Scored phase** — every project and experience entry from the user profile
    is scored against the job's required topics. Entries whose associated
    Markdown file fits within the budget are included in descending order of
    relevance.
2.  **Fallback phase** — any remaining token budget is filled with unmatched
    Markdown files so that the AI engine receives as much context as possible.
"""

import re

from src.models import JobDescription, ProjectSummary, Skill, UserProfile


# Rough heuristic: 1 token ≈ 4 characters.
CHARS_PER_TOKEN = 4

SECTION_SEPARATOR = "\n\n---\n\n"


def _estimate_tokens(text: str) -> int:
    """Estimate the number of tokens a string occupies from its character length.

    Args:
        text: The string whose token count is to be estimated.

    Returns:
        The estimated token count as an integer.
    """
    return len(text) // CHARS_PER_TOKEN


def _score_relevance(item: ProjectSummary, job_topics: list[str]) -> float:
    """Score how relevant a project or experience entry is to a set of job topics.

    The score is computed as the number of case-insensitive topic tags that the
    item shares with the job description. When no job topics are provided a
    neutral default score of 0.5 is returned so that all entries remain eligible
    for selection during the fallback phase.

    Args:
        item: The project or experience entry whose topics will be compared.
        job_topics: The list of required topic tags extracted from the job
            description.

    Returns:
        A float representing the relevance score. Returns 0.5 when
        ``job_topics`` is empty, otherwise the count of overlapping topics.
    """
    if not job_topics:
        return 0.5

    item_topics = {t.lower() for t in item.topics}
    job_set = {t.lower() for t in job_topics}
    overlap = item_topics & job_set
    return float(len(overlap))


def _normalize_name(name: str) -> str:
    """Normalise a project or file name for heuristic matching.

    The normalisation applies the following transformations in order:

    1.  Convert the entire string to lowercase.
    2.  Replace spaces and hyphens with underscores.
    3.  Strip any character that is not a lowercase letter, digit, or underscore.

    Args:
        name: The raw project or file name to normalise.

    Returns:
        The normalised name string, ready for substring-based comparison.
    """
    normalized = name.lower()
    normalized = re.sub(r"[\s-]+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def _match_project_to_md(project_name: str, md_files: dict[str, str]) -> str | None:
    """Find the Markdown content whose file name best matches a project name.

    This is a best-effort heuristic that performs substring matching between
    the normalised project name and each normalised file key. It is not
    guaranteed to find the correct file when multiple candidates share similar
    names.

    Args:
        project_name: The name of the project or experience entry to match.
        md_files: A dictionary mapping filename stems to their full text content

    Returns:
        The full text content of the best-matching Markdown file, or ``None``
        if no heuristic match is found.
    """
    norm_project = _normalize_name(project_name)
    for key, content in md_files.items():
        norm_key = _normalize_name(key)
        if norm_project in norm_key or norm_key in norm_project:
            return content
    return None


def _score_and_sort_items(
    profile: UserProfile, job_topics: list[str]
) -> list[tuple[ProjectSummary, float]]:
    """Score every project and experience entry against job topics and sort by relevance.

    Args:
        profile: The user profile containing projects and experience entries.
        job_topics: The list of required topic tags from the job description.

    Returns:
        A list of ``(item, score)`` tuples sorted by descending score,
        with alphabetical name as a tiebreaker.
    """
    all_items: list[ProjectSummary] = profile.projects + profile.experience
    scored = [(item, _score_relevance(item, job_topics)) for item in all_items]
    scored.sort(key=lambda x: (-x[1], x[0].name))
    return scored


def _select_matched_files(
    scored_items: list[tuple[ProjectSummary, float]],
    md_files: dict[str, str],
    max_tokens: int,
) -> tuple[list[str], set[str], int]:
    """Select matching Markdown files from scored items within the token budget.

    Args:
        scored_items: Sorted list of ``(item, score)`` tuples.
        md_files: A dictionary mapping filename stems to their full text content.
        max_tokens: The maximum number of tokens allowed in the combined output.

    Returns:
        A tuple of ``(selected_texts, matched_keys, total_tokens)`` where
        *selected_texts* is a list of formatted Markdown sections, *matched_keys*
        is the set of md_files keys that were included, and *total_tokens* is
        the cumulative token count.
    """
    content_to_key = {content: key for key, content in md_files.items()}
    selected_texts: list[str] = []
    total_tokens = 0
    matched_keys: set[str] = set()

    for item, _ in scored_items:
        match = _match_project_to_md(item.name, md_files)
        if match is None:
            continue

        estimated = _estimate_tokens(match)
        if total_tokens + estimated <= max_tokens:
            selected_texts.append(f"### {item.name}\n{match}")
            total_tokens += estimated
            matched_keys.add(content_to_key[match])

    return selected_texts, matched_keys, total_tokens


def _fill_unmatched_files(
    md_files: dict[str, str],
    matched_keys: set[str],
    total_tokens: int,
    max_tokens: int,
) -> tuple[list[str], int]:
    """Fill the remaining token budget with unmatched Markdown files.

    Args:
        md_files: A dictionary mapping filename stems to their full text content.
        matched_keys: The set of keys already included in the selection.
        total_tokens: The current cumulative token count.
        max_tokens: The maximum number of tokens allowed in the combined output.

    Returns:
        A tuple of ``(selected_texts, total_tokens)`` where *selected_texts*
        is a list of formatted Markdown sections for unmatched files and
        *total_tokens* is the updated cumulative count.
    """
    selected_texts: list[str] = []
    unmatched_keys = sorted(set(md_files.keys()) - matched_keys)
    for key in unmatched_keys:
        content = md_files[key]
        estimated = _estimate_tokens(content)
        if total_tokens + estimated <= max_tokens:
            selected_texts.append(f"### {key}\n{content}")
            total_tokens += estimated

    return selected_texts, total_tokens


# ---------------------------------------------------------------------------
# New helpers for the single-text (hybrid) path
# ---------------------------------------------------------------------------


def _split_text_into_sections(text: str) -> dict[str, str]:
    """Split a background Markdown text into sections delimited by ``###`` or ``####`` headers.

    Each line beginning with exactly three or four ``#`` characters is treated
    as a section header.  The header text (stripped of ``#`` and whitespace)
    becomes the key, and everything until the next header becomes the value.

    Args:
        text: The raw background Markdown text to split.

    Returns:
        A dictionary mapping each header string to its body text.
        If no ``###`` or ``####`` headers are found the entire text is
        returned under the key ``"background"``.
    """
    parts = re.split(r"^#{3,4}\s+(.+)$", text, flags=re.MULTILINE)

    if len(parts) <= 1:
        return {"background": text}

    sections: dict[str, str] = {}
    i = 1
    while i < len(parts):
        header = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        sections[header] = body
        i += 2

    return sections


def _score_sections(
    sections: dict[str, str],
    profile: UserProfile,
    job_topics: list[str],
) -> list[tuple[str, str, float]]:
    """Score each background-text section against the job and the user profile.

    For every ``(header, body)`` pair in *sections* the function attempts an
    exact match between the normalised header and the normalised name of each
    project / experience entry in *profile*.  When a match is found the score
    equals the number of case-insensitive topic overlaps between the matched
    project and *job_topics*.  Otherwise the score is the count of *job_topics*
    keywords found via whole-word search in *body*.

    Args:
        sections: Header-to-body mapping produced by
            :func:`_split_text_into_sections`.
        profile: The user profile containing projects and experience entries.
        job_topics: The list of required topic tags from the job description.

    Returns:
        A list of ``(header, body, score)`` tuples sorted by descending score.
    """
    all_projects = profile.projects + profile.experience
    job_topics_lower = [t.lower() for t in job_topics]
    job_topics_set = set(job_topics_lower)

    results: list[tuple[str, str, float]] = []

    for header, body in sections.items():
        norm_header = _normalize_name(header)
        matched_project: ProjectSummary | None = None

        for proj in all_projects:
            if _normalize_name(proj.name) == norm_header:
                matched_project = proj
                break

        if matched_project is not None:
            proj_topics_lower = {t.lower() for t in matched_project.topics}
            score = float(len(proj_topics_lower & job_topics_set))
        else:
            body_lower = body.lower()
            score = 0.0
            for topic in job_topics_lower:
                if re.search(r"\b" + re.escape(topic) + r"\b", body_lower):
                    score += 1.0

        results.append((header, body, score))

    results.sort(key=lambda x: -x[2])
    return results


def _build_skills_block(profile: UserProfile, job_topics: list[str]) -> str:
    """Build a compact Markdown block of skills relevant to the job.

    A skill is included when any of the following holds:

    * ``skill.name.lower()`` is an exact (case-insensitive) match with an
      element of *job_topics*.
    * At least one *job_topic* is a substring of ``skill.name.lower()``.
    * ``skill.category == "technical"`` and the skill name appears in the
      ``technologies`` list of any project / experience entry that shares at
      least one topic with *job_topics*.

    Skills are grouped by ``category`` and sorted alphabetically within each
    group.

    Args:
        profile: The user profile containing the full skills list.
        job_topics: The list of required topic tags from the job description.

    Returns:
        A Markdown string in the format::

            ### Relevant Skills
            - **Technical**: CFD (advanced), Thermal Simulation (advanced) ...
            - **Software**: Python (advanced), PyTorch (intermediate) ...

        Returns an empty string when no skills match the criteria.
    """
    job_topics_lower = [t.lower() for t in job_topics]
    job_topics_set = set(job_topics_lower)

    # Collect technologies from projects that share at least one topic with the job
    all_projects = profile.projects + profile.experience
    matched_techs: set[str] = set()
    for proj in all_projects:
        proj_topics_lower = {t.lower() for t in proj.topics}
        if proj_topics_lower & job_topics_set:
            matched_techs.update(t.lower() for t in proj.technologies)

    by_category: dict[str, list[Skill]] = {}

    for skill in profile.skills:
        name_lower = skill.name.lower()
        include = False

        if name_lower in job_topics_set:
            include = True
        elif any(topic in name_lower for topic in job_topics_lower):
            include = True
        elif skill.category == "technical" and name_lower in matched_techs:
            include = True

        if include:
            by_category.setdefault(skill.category, []).append(skill)

    if not by_category:
        return ""

    lines = ["### Relevant Skills"]
    for category in sorted(by_category.keys()):
        skills = sorted(by_category[category], key=lambda s: s.name)
        skill_strs = [f"{s.name} ({s.proficiency})" for s in skills]
        lines.append(f"- **{category.capitalize()}**: {', '.join(skill_strs)}")

    return "\n".join(lines)


def _assemble_details(
    skills_block: str,
    scored_sections: list[tuple[str, str, float]],
    max_tokens: int,
) -> str:
    """Assemble the final context string from a skills block and scored sections.

    The skills block (if non-empty and within budget) is always placed first.
    Scored sections are then included in descending score order while they fit
    within the remaining token budget.  Any leftover budget is filled with
    sections not yet selected, in alphabetical header order.

    Each section is formatted as ``### {header}\\n{body}`` and sections are
    joined with ``\\n\\n---\\n\\n``.

    Args:
        skills_block: The pre-built relevant-skills Markdown string (may be
            empty).
        scored_sections: List of ``(header, body, score)`` tuples sorted by
            descending score.
        max_tokens: The maximum number of tokens allowed in the combined
            output.

    Returns:
        A single string containing the selected Markdown sections, separated
        by ``\\n\\n---\\n\\n``.  Returns an empty string when nothing fits
        within the budget.
    """
    selected: list[str] = []
    included_headers: set[str] = set()
    total_tokens = 0

    # Always try to include the skills block first
    if skills_block:
        estimated = _estimate_tokens(skills_block)
        if estimated <= max_tokens:
            selected.append(skills_block)
            total_tokens += estimated

    # Scored sections by descending score
    for header, body, _score in scored_sections:
        section_text = f"### {header}\n{body}"
        estimated = _estimate_tokens(section_text)
        if total_tokens + estimated <= max_tokens:
            selected.append(section_text)
            total_tokens += estimated
            included_headers.add(header)

    # Fill remaining budget with unmatched sections in alphabetical order
    unmatched = sorted(
        [(h, b) for h, b, _s in scored_sections if h not in included_headers],
        key=lambda x: x[0],
    )
    for header, body in unmatched:
        section_text = f"### {header}\n{body}"
        estimated = _estimate_tokens(section_text)
        if total_tokens + estimated <= max_tokens:
            selected.append(section_text)
            total_tokens += estimated

    return SECTION_SEPARATOR.join(selected)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def select_relevant_details(
    job: JobDescription,
    profile: UserProfile,
    background_text: str | None = None,
    md_files: dict[str, str] | None = None,
    max_tokens: int = 2000,
) -> str:
    """Select the most relevant Markdown content for a job within a token budget.

    This is the primary entry point for Layer 2 of the context management
    system.  It supports two mutually-exclusive input modes:

    **Multi-file mode** (``md_files`` provided)
        Every project and experience entry in the user's profile is scored
        against the job's required topics using :func:`_score_relevance`.
        Entries are sorted by descending score (and alphabetically by name as a
        tiebreaker).  For each entry, the corresponding Markdown file is
        located via :func:`_match_project_to_md` and, if it fits within the
        remaining token budget, appended to the result.  Unmatched files are
        then added in alphabetical order as fallback.

    **Single-text mode** (``background_text`` provided)
        The background text is split into sections delimited by ``###`` and
        ``####`` headers via :func:`_split_text_into_sections`.  Each section
        is scored against the structured ``UserProfile`` by
        :func:`_score_sections`.  A compact skills block is built with
        :func:`_build_skills_block` and prepended.  Sections are assembled by
        :func:`_assemble_details` within the token budget.

    Args:
        job: The job description whose required topics drive the relevance
            scoring.
        profile: The user profile containing the projects, experience, and
            skills entries to select from.
        background_text: A single Markdown string whose sections correspond to
            the user's project / experience entries.  Mutually exclusive with
            *md_files*.
        md_files: A dictionary mapping filename stems to their full text
            content.  Mutually exclusive with *background_text*.
        max_tokens: The maximum number of tokens allowed in the combined
            output.  Defaults to 2000.

    Returns:
        A single string containing the selected Markdown sections, separated
        by ``\\n\\n---\\n\\n``.  Each section is prefixed with a level-3
        Markdown heading (``###``) bearing the name of the entry or file it
        came from.  Returns an empty string when no content fits within the
        budget.

    Raises:
        ValueError: If both *background_text* and *md_files* are provided.
    """
    if background_text is not None and md_files is not None:
        raise ValueError(
            "Cannot provide both background_text and md_files. "
            "Use one or the other."
        )

    job_topics = job.required_topics

    if md_files is not None:
        # ── Multi-file mode (backward-compatible) ──
        scored = _score_and_sort_items(profile, job_topics)

        matched_texts, matched_keys, total_tokens = _select_matched_files(
            scored, md_files, max_tokens
        )

        unmatched_texts, _total_tokens = _fill_unmatched_files(
            md_files, matched_keys, total_tokens, max_tokens
        )

        all_texts = matched_texts + unmatched_texts
        return SECTION_SEPARATOR.join(all_texts)

    if background_text is not None:
        # ── Single-text (hybrid) mode ──
        sections = _split_text_into_sections(background_text)
        scored = _score_sections(sections, profile, job_topics)
        skills_block = _build_skills_block(profile, job_topics)
        return _assemble_details(skills_block, scored, max_tokens)

    return ""
