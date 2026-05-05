"""Pydantic data models for the CV-to-job matching application.

This module defines all data structures used throughout the application,
including models for personal information, education history, project
summaries, skills, user profiles, job descriptions, qualification matching
results, and dynamically generated CV content zones. All models inherit
from ``pydantic.BaseModel`` to provide automatic validation, serialisation,
and deserialisation.

Typical usage example::

    profile = UserProfile(
        personal_info=PersonalInfo(...),
        education=[...],
        experience=[...],
        skills=[...],
        projects=[...],
    )
    job = JobDescription(title="Software Engineer", ...)
"""

from pydantic import BaseModel
from typing import Optional


class PersonalInfo(BaseModel):
    """Contact and personal identification details for a single user.

    Stores the core biographical information needed to identify the user
    and reach them for professional opportunities.

    Attributes:
        name: Full name of the individual.
        address: Complete postal or street address
        email: Primary email address used for professional correspondence.
        phone: Contact telephone number including country code when
            applicable.
        linkedin: Optional URL to the individual's LinkedIn profile page.
            When not provided the field defaults to ``None``.
    """

    name: str
    address: str
    email: str
    phone: str
    linkedin: Optional[str] = None


class Education(BaseModel):
    """A single educational qualification entry on a user's CV.

    This model captures the essential details of a degree, diploma, or
    certificate earned at an academic institution. It supports listing
    multiple subjects studied and an optional thesis title for research
    oriented programmes.

    Attributes:
        degree: The full name or abbreviation of the qualification
            (e.g. "M.Sc. Mechanical Engineering", "B.A. Economics").
        institution: The name of the university, college, or awarding body.
        subjects: Ordered list of subjects, modules, or specialisations
            taken as part of the degree.
        thesis_title: Optional title of the final thesis or dissertation.
            Only populated when the degree required a written thesis.
        year: Calendar year in which the degree was awarded or is
            expected to be completed (e.g. "2024").
    """

    degree: str
    institution: str
    subjects: list[str]
    thesis_title: Optional[str] = None
    year: str


class ProjectSummary(BaseModel):
    """Concise summary of a project or work experience entry.

    Used to represent both professional industry positions and academic or
    personal projects. The ``type`` field distinguishes between the
    different contexts so the matching logic can treat them accordingly.

    Attributes:
        name: Short, descriptive name for the project or position
            (e.g. "CFD Analysis of Turbine Blades").
        type: Category of the experience. Must be one of ``"thesis"``,
            ``"industry"``, or ``"academic"``.
        role: The title or role held during the project
            (e.g. "Research Assistant", "Lead Developer").
        duration: Human-readable duration string
            (e.g. "Jan 2023 – Jun 2023").
        key_contribution: A single sentence summarising the most
            impactful contribution made.
        technologies: Ordered list of tools, frameworks, programming
            languages, or software used (e.g. ``["Python", "OpenFOAM"]``).
        topics: Domain-specific topic tags that describe the subject
            area (e.g. ``["thermal_simulation", "cfd"]``). These are used
            by the AI matching engine to align with job requirements.
    """

    name: str
    type: str  # "thesis", "industry", "academic"
    role: str
    duration: str
    key_contribution: str
    technologies: list[str]
    topics: list[str]  # e.g., ["thermal_simulation", "cfd"]


class Skill(BaseModel):
    """A single skill entry categorised by domain and proficiency level.

    Skills are organised into four categories so the application can
    prioritise and present them contextually (e.g. technical skills in a
    dedicated section, languages separately).

    Attributes:
        category: The domain the skill belongs to. Must be one of
            ``"technical"``, ``"software"``, ``"language"``, or ``"soft"``.
        name: The canonical name of the skill
            (e.g. "Python", "Project Management", "German").
        proficiency: Self-assessed or inferred level of expertise. Must be
            one of ``"beginner"``, ``"intermediate"``, ``"advanced"``, or
            ``"expert"``.
    """

    category: str  # "technical", "software", "language", "soft"
    name: str
    proficiency: str  # "beginner", "intermediate", "advanced", "expert"


class UserProfile(BaseModel):
    """Top-level model representing a complete user CV / profile.

    Aggregates all personal, educational, professional, and project
    information into a single structured object. This is the primary
    input to the matching engine and is also used to populate the
    dynamically generated CV document.

    Attributes:
        personal_info: The user's name, address, and contact details.
        education: One or more educational entries ordered from most
            recent to oldest.
        experience: Professional work history. Each entry reuses
            :class:`ProjectSummary` with ``type`` set to ``"industry"``.
        skills: Flat list of all skills the user has declared, across
            all categories.
        projects: Academic, personal, or open-source projects. Each entry
            reuses :class:`ProjectSummary` with ``type`` typically set to
            ``"academic"`` or ``"thesis"``.
    """

    personal_info: PersonalInfo
    education: list[Education]
    experience: list[ProjectSummary]  # Reusing ProjectSummary for work exp
    skills: list[Skill]
    projects: list[ProjectSummary]


class JobDescription(BaseModel):
    """Raw and processed data for a single job posting.

    Stores the original job advertisement text alongside metadata such
    as title, company, and location. The ``required_topics`` list is
    intended to be populated by an AI extraction step and is used to
    drive the qualification matching process.

    Attributes:
        title: The job title as advertised (e.g. "Senior Data Scientist").
        company: Name of the hiring organisation.
        location: Geographic location of the position
            (e.g. "Munich, Germany" or "Remote").
        raw_text: The full, unmodified text of the job advertisement or
            description.
        required_topics: Keyword or topic tags extracted by an AI
            pipeline (e.g. ``["machine_learning", "python", "sql"]``).
            Populated asynchronously after the initial creation.
    """

    title: str
    company: str
    location: str
    raw_text: str
    required_topics: list[str]  # Extracted by AI later


class QualificationMatch(BaseModel):
    """The result of matching a single job requirement against the user's
    profile.

    Each instance represents one requirement from a job description and
    the evidence (or lack thereof) found in the user's CV, along with a
    qualitative assessment of how well they align.

    Attributes:
        requirement: The specific qualification, skill, or experience
            item demanded by the job (e.g. "5+ years of Python experience").
        user_evidence: The relevant excerpt from the user's CV that
            supports or contradicts the requirement. Empty string when
            no evidence is found.
        match_level: Qualitative strength of the match. Must be one of
            ``"strong"`` (clear, explicit evidence), ``"partial"``
            (indirect or incomplete evidence), or ``"missing"`` (no
            supporting evidence found).
    """

    requirement: str
    user_evidence: str
    match_level: str  # "strong", "partial", "missing"


class JobMatchResult(BaseModel):
    """Complete analysis of how well a user profile matches a job
    description.

    This is the top-level output of the matching engine. It aggregates
    per-requirement matches into an overall recommendation with
    supporting reasoning, explicitly listing identified gaps and
    strengths.

    Attributes:
        required_qualifications: A list of individual qualification
            matches, one per requirement extracted from the job posting.
        gaps: Human-readable descriptions of areas where the user's
            profile does not meet the job requirements (e.g. "No
            experience with Docker").
        strengths: Human-readable descriptions of areas where the
            user's profile exceeds or strongly meets the job requirements
            (e.g. "10+ years of Python exceeds the 3-year requirement").
        recommendation: Overall hiring recommendation. Must be one of
            ``"strong_match"``, ``"moderate_match"``, or ``"weak_match"``.
        reasoning: Free-text explanation justifying the overall
            recommendation, referencing specific matches and gaps.
    """

    required_qualifications: list[QualificationMatch]
    gaps: list[str]
    strengths: list[str]
    recommendation: str  # "strong_match", "moderate_match", "weak_match"
    reasoning: str


class CVDynamicZones(BaseModel):
    """AI-generated content sections for a tailored CV document.

    After the matching process, the AI engine produces custom-written
    text for the key sections of a CV so that the final document is
    optimised for the target job. Each field corresponds to a distinct
    visual zone in the generated CV layout.

    Attributes:
        professional_summary: A 2–3 sentence career summary written to
            highlight the qualifications most relevant to the target job.
        bachelor_subjects: One sentence explaining 2 or 3 relevant academic
            subjects from the user's bachelor's degree.
        master_subjects: One sentence explaining 2 or 3 relevant academic
            subjects from the user's master's degree..
    """

    professional_summary: str
    bachelor_subjects: str
    master_subjects: str

