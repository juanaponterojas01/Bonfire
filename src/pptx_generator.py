"""Render CVs from PPTX templates using placeholder replacement across all shapes.

This module fills a German `.pptx` CV template by replacing `[placeholder]`
strings with actual content. It handles the common PPTX issue where text is
split across multiple XML `<a:r>` runs inside shapes and text frames.
"""

from pathlib import Path
from pptx import Presentation

from src.models import CVDynamicZones, JobDescription, UserProfile
from src.utils import get_todays_date


def _replace_text_in_shape(shape, old_text: str, new_text: str) -> None:
    """Replace *old_text* with *new_text* in a single shape's text frame.

    Handles text split across multiple XML runs within a paragraph.

    Args:
        shape: A python-pptx shape object (may have nested grouped shapes).
        old_text: The placeholder string to search for.
        new_text: The value to replace the placeholder with.
    """
    if shape.has_text_frame:
        for paragraph in shape.text_frame.paragraphs:
            full_text = "".join(run.text for run in paragraph.runs)
            if old_text not in full_text:
                continue
            replaced = full_text.replace(old_text, new_text)
            if paragraph.runs:
                for run in paragraph.runs:
                    run.text = ""
                paragraph.runs[0].text = replaced

    if hasattr(shape, "shapes"):
        for sub_shape in shape.shapes:
            _replace_text_in_shape(sub_shape, old_text, new_text)


def _replace_text_in_pptx(prs: Presentation, old_text: str, new_text: str) -> None:
    """Iterate through all slides and shapes, replacing *old_text* with *new_text*.

    Args:
        prs: The python-pptx Presentation object to modify in place.
        old_text: The placeholder string to search for.
        new_text: The value to replace the placeholder with.
    """
    for slide in prs.slides:
        for shape in slide.shapes:
            _replace_text_in_shape(shape, old_text, new_text)


def _format_education(profile: UserProfile) -> str:
    """Format education entries as multi-line text.

    Args:
        profile: The user's complete profile.

    Returns:
        A formatted string with degree, institution, year, and optional thesis
        for each education entry, separated by blank lines.
    """
    entries = []
    for edu in profile.education:
        lines = [
            f"{edu.degree} — {edu.institution}",
            edu.year,
        ]
        if edu.thesis_title:
            lines.append(f"Thesis: {edu.thesis_title}")
        entries.append("\n".join(lines))
    return "\n\n".join(entries)


def _format_skills(profile: UserProfile) -> str:
    """Group skills by category and format as labelled lists.

    Args:
        profile: The user's complete profile.

    Returns:
        A formatted string with skills grouped under their category headings.
    """
    category_order = ["technical", "software", "language", "soft"]
    category_labels = {
        "technical": "Technical",
        "software": "Software",
        "language": "Language",
        "soft": "Soft",
    }
    grouped: dict[str, list[str]] = {cat: [] for cat in category_order}
    for skill in profile.skills:
        if skill.category in grouped:
            grouped[skill.category].append(skill.name)

    lines = []
    for cat in category_order:
        if grouped[cat]:
            lines.append(f"{category_labels[cat]}: {', '.join(grouped[cat])}")
    return "\n".join(lines)


def _format_work_experience(profile: UserProfile) -> str:
    """Format static work experience info (dates, titles, companies).

    Args:
        profile: The user's complete profile.

    Returns:
        A formatted string with each experience entry showing name and
        duration/type, separated by blank lines.
    """
    entries = []
    for exp in profile.experience:
        lines = [
            exp.name,
            f"{exp.duration} | {exp.type}",
        ]
        entries.append("\n".join(lines))
    return "\n\n".join(entries)


def _format_relevant_subjects(dynamic_zones: CVDynamicZones) -> str:
    """Format relevant academic subjects as a bulleted list.

    Args:
        dynamic_zones: The AI-generated dynamic CV content.

    Returns:
        A string with each subject prefixed by a bullet point.
    """
    return "\n".join(f"• {subject}" for subject in dynamic_zones.relevant_subjects)


def _format_selected_projects(dynamic_zones: CVDynamicZones) -> str:
    """Format selected projects as a numbered list with descriptions.

    Args:
        dynamic_zones: The AI-generated dynamic CV content.

    Returns:
        A string with each project numbered and its description indented.
    """
    lines = []
    for i, project in enumerate(dynamic_zones.selected_projects, 1):
        lines.append(f"{i}. {project['name']}")
        lines.append(f"   {project['description']}")
    return "\n".join(lines)


def _build_cv_context(
    job: JobDescription,
    profile: UserProfile,
    dynamic_zones: CVDynamicZones,
    language: str,
) -> dict[str, str]:
    """Build a context dictionary mapping placeholders to formatted values.

    Args:
        job: The target job description.
        profile: The user's complete profile.
        dynamic_zones: The AI-generated dynamic CV content.
        language: Language code for date formatting.

    Returns:
        A dictionary where keys are placeholder strings and values are
        the formatted text to replace them with.
    """
    context: dict[str, str] = {
        "[date]": get_todays_date(language),
        "[professional_summary]": dynamic_zones.professional_summary,
        "[relevant_subjects]": _format_relevant_subjects(dynamic_zones),
        "[skills]": _format_skills(profile),
        "[education]": _format_education(profile),
        "[selected_projects]": _format_selected_projects(dynamic_zones),
        "[personal_info_name]": profile.personal_info.name,
        "[personal_info_address]": profile.personal_info.address,
        "[personal_info_email]": profile.personal_info.email,
        "[personal_info_phone]": profile.personal_info.phone,
        "[personal_info_linkedin]": profile.personal_info.linkedin or "",
        "[work_experience]": _format_work_experience(profile),
    }

    for exp_name, bullets in dynamic_zones.work_descriptions.items():
        key = f"[work_descriptions:{exp_name}]"
        context[key] = "\n".join(f"• {b}" for b in bullets)

    return context


def render_cv(
    template_path: str | Path,
    output_path: str | Path,
    job: JobDescription,
    profile: UserProfile,
    dynamic_zones: CVDynamicZones,
    language: str,
) -> str:
    """Render a CV from a PPTX template by replacing placeholders.

    Args:
        template_path: Path to the .pptx template file.
        output_path: Path where the rendered CV will be saved.
        job: The target job description.
        profile: The user's complete profile.
        dynamic_zones: The AI-generated dynamic CV content.
        language: Language code for date formatting.

    Returns:
        The output path as a string.
    """
    prs = Presentation(str(template_path))
    context = _build_cv_context(job, profile, dynamic_zones, language)

    for placeholder, value in context.items():
        _replace_text_in_pptx(prs, placeholder, value)

    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return str(output_path)
