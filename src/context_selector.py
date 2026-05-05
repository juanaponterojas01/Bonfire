"""Layer 2 of the context management system: select the most relevant background
details for a given job description.

This module implements the selection and scoring logic that determines which
project and experience Markdown files to include in the context window passed
to the AI matching engine. It consumes the Pydantic models defined in
:mod:`src.models` (in particular :class:`ProjectSummary`, :class:`UserProfile`,
and :class:`JobDescription`) and returns a concatenated, relevance-sorted
string of Markdown content within a configurable token budget.

The selection process follows a two-phase approach:

1.  **Scored phase** — every project and experience entry from the user profile
    is scored against the job's required topics. Entries whose associated
    Markdown file fits within the budget are included in descending order of
    relevance.
2.  **Fallback phase** — any remaining token budget is filled with unmatched
    Markdown files so that the AI engine receives as much context as possible.
"""

import re

from src.models import JobDescription, ProjectSummary, UserProfile


# Rough heuristic: 1 token ≈ 4 characters.
# TODO: replace this constant with ``tiktoken`` for more accurate token counting.
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


def select_relevant_details(
    job: JobDescription,
    profile: UserProfile,
    md_files: dict[str, str],
    max_tokens: int = 2000,
) -> str:
    """Select the most relevant Markdown content for a job within a token budget.

    This is the primary entry point for Layer 2 of the context management
    system. It implements a two-phase selection process:

    **Phase 1 — Scored selection**

        Every project and experience entry in the user's profile is scored
        against the job's required topics using :func:`_score_relevance`.
        Entries are sorted by descending score (and alphabetically by name as a
        tiebreaker). For each entry, the corresponding Markdown file is located
        via :func:`_match_project_to_md` and, if it fits within the remaining
        token budget, appended to the result.

    **Phase 2 — Fallback**

        Any Markdown files that were not selected in Phase 1 are added in
        alphabetical order, again subject to the token budget, so that no
        context capacity is wasted.

    Args:
        job: The job description whose required topics drive the relevance
            scoring.
        profile: The user profile containing the projects and experience
            entries to select from.
        md_files: A dictionary mapping filename stems to their full text content

        max_tokens: The maximum number of tokens allowed in the combined
            output. Defaults to 6000.

    Returns:
        A single string containing the selected Markdown sections, separated
        by ``\\n\\n---\\n\\n``. Each section is prefixed with a level-3 Markdown
        heading (``###``) bearing the name of the entry or file it came from.
        Returns an empty string when no content fits within the budget.
    """
    job_topics = job.required_topics

    scored = _score_and_sort_items(profile, job_topics)

    matched_texts, matched_keys, total_tokens = _select_matched_files(
        scored, md_files, max_tokens
    )

    unmatched_texts, _total_tokens = _fill_unmatched_files(
        md_files, matched_keys, total_tokens, max_tokens
    )

    all_texts = matched_texts + unmatched_texts
    return SECTION_SEPARATOR.join(all_texts)
