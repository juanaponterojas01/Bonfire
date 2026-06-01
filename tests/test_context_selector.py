"""Tests for src.context_selector — Layer 2 context selection and scoring."""

import pytest

from src.context_selector import (
    _assemble_details,
    _build_skills_block,
    _score_sections,
    _split_text_into_sections,
    select_relevant_details,
    CHARS_PER_TOKEN,
)
from src.models import (
    Education,
    JobDescription,
    PersonalInfo,
    ProjectSummary,
    Skill,
    UserProfile,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def personal_info() -> PersonalInfo:
    return PersonalInfo(
        name="John Doe",
        address="123 Main St",
        email="john@example.com",
        phone="+1234567890",
    )


@pytest.fixture
def education() -> list[Education]:
    return [
        Education(
            degree="M.Sc. Mechanical Engineering",
            institution="TU Munich",
            subjects=["Fluid Dynamics", "Numerical Methods"],
            thesis_title="CFD Analysis of Turbine Blades",
            year="2023",
        )
    ]


@pytest.fixture
def make_profile(personal_info, education):
    """Factory fixture to build a UserProfile with given projects, experience, skills."""

    def _build(
        projects: list[ProjectSummary] | None = None,
        experience: list[ProjectSummary] | None = None,
        skills: list[Skill] | None = None,
    ) -> UserProfile:
        return UserProfile(
            personal_info=personal_info,
            education=education,
            experience=experience or [],
            skills=skills or [],
            projects=projects or [],
        )

    return _build


@pytest.fixture
def make_job():
    """Factory fixture to build a JobDescription with given topics."""

    def _build(topics: list[str] | None = None) -> JobDescription:
        return JobDescription(
            title="Test Engineer",
            company="Test Corp",
            location="Remote",
            raw_text="We need someone who knows stuff.",
            required_topics=topics or [],
        )

    return _build


# ---------------------------------------------------------------------------
# _split_text_into_sections
# ---------------------------------------------------------------------------


class TestSplitTextIntoSections:
    def test_should_split_by_headers(self):
        # Arrange
        text = "### Header A\nbody A content\n#### Header B\nbody B content"

        # Act
        result = _split_text_into_sections(text)

        # Assert
        assert result == {
            "Header A": "body A content",
            "Header B": "body B content",
        }

    def test_should_return_background_key_for_plain_text(self):
        # Arrange
        text = "Just some plain text\nwithout any markdown headers."

        # Act
        result = _split_text_into_sections(text)

        # Assert
        assert result == {"background": text}

    def test_should_capture_mixed_levels(self):
        # Arrange
        text = "### Level 3\ncontent three\n#### Level 4\ncontent four\n### Another 3\nmore content"

        # Act
        result = _split_text_into_sections(text)

        # Assert
        assert result == {
            "Level 3": "content three",
            "Level 4": "content four",
            "Another 3": "more content",
        }


# ---------------------------------------------------------------------------
# _score_sections
# ---------------------------------------------------------------------------


class TestScoreSections:
    def test_exact_project_match_scores_by_topic_overlap(self, make_profile, make_job):
        # Arrange
        profile = make_profile(
            projects=[
                ProjectSummary(
                    name="Test Project",
                    type="academic",
                    role="Researcher",
                    duration="2023",
                    key_contribution="Did research.",
                    technologies=["Python", "OpenFOAM"],
                    topics=["cfd", "python"],
                )
            ]
        )
        sections = {"Test Project": "some body text"}

        # Act — one overlapping topic
        job_cfd = make_job(["cfd"])
        result_cfd = _score_sections(sections, profile, job_cfd.required_topics)

        # Act — two overlapping topics
        job_both = make_job(["cfd", "python"])
        result_both = _score_sections(sections, profile, job_both.required_topics)

        # Assert
        assert result_cfd == [("Test Project", "some body text", 1.0)]
        assert result_both == [("Test Project", "some body text", 2.0)]

    def test_should_fallback_to_keyword_scoring_in_body(self, make_profile, make_job):
        # Arrange
        profile = make_profile(projects=[])  # no project matching the header
        sections = {"Unrelated Name": "cfd simulation work with some details"}
        job = make_job(["cfd", "python"])

        # Act
        result = _score_sections(sections, profile, job.required_topics)

        # Assert — only "cfd" found as a whole word in the body
        assert result == [("Unrelated Name", "cfd simulation work with some details", 1.0)]

    def test_should_return_zero_for_empty_job_topics(self, make_profile, make_job):
        # Arrange
        profile = make_profile(
            projects=[
                ProjectSummary(
                    name="Alpha Project",
                    type="academic",
                    role="Dev",
                    duration="2023",
                    key_contribution="Stuff.",
                    technologies=[],
                    topics=["cfd", "python"],
                )
            ]
        )
        sections = {"Alpha Project": "body", "Other Section": "unrelated body"}
        job = make_job([])  # empty topics

        # Act
        result = _score_sections(sections, profile, job.required_topics)

        # Assert — both scores are 0.0 (no topics = empty set, no overlaps, no keywords)
        scores = {header: score for header, _, score in result}
        assert scores["Alpha Project"] == 0.0
        assert scores["Other Section"] == 0.0


# ---------------------------------------------------------------------------
# _build_skills_block
# ---------------------------------------------------------------------------


class TestBuildSkillsBlock:
    def test_should_include_skill_with_exact_topic_match(self, make_profile, make_job):
        # Arrange
        profile = make_profile(
            skills=[Skill(category="technical", name="CFD", proficiency="advanced")]
        )
        job = make_job(["cfd"])

        # Act
        result = _build_skills_block(profile, job.required_topics)

        # Assert
        assert "CFD" in result
        assert "Relevant Skills" in result

    def test_should_include_skill_with_substring_match(self, make_profile, make_job):
        # Arrange
        profile = make_profile(
            skills=[
                Skill(
                    category="software",
                    name="Python Development",
                    proficiency="expert",
                )
            ]
        )
        job = make_job(["python"])

        # Act
        result = _build_skills_block(profile, job.required_topics)

        # Assert — "python" is a substring of "python development"
        assert "Python Development" in result

    def test_should_include_technical_skill_in_matched_project_technologies(
        self, make_profile, make_job
    ):
        # Arrange
        profile = make_profile(
            projects=[
                ProjectSummary(
                    name="Fluid Project",
                    type="academic",
                    role="Researcher",
                    duration="2023",
                    key_contribution="Simulated fluids.",
                    technologies=["openfoam", "paraview"],
                    topics=["cfd"],
                )
            ],
            skills=[
                Skill(category="technical", name="OpenFOAM", proficiency="advanced"),
                Skill(
                    category="software",
                    name="ParaView",
                    proficiency="intermediate",
                ),
            ],
        )
        job = make_job(["cfd"])

        # Act
        result = _build_skills_block(profile, job.required_topics)

        # Assert — OpenFOAM is technical AND in matched project technologies
        assert "OpenFOAM" in result
        # ParaView is software (not technical), so NOT included via technology path
        assert "ParaView" not in result

    def test_should_return_empty_when_no_skills_match(self, make_profile, make_job):
        # Arrange
        profile = make_profile(
            skills=[Skill(category="soft", name="Leadership", proficiency="advanced")]
        )
        job = make_job(["cfd", "python"])

        # Act
        result = _build_skills_block(profile, job.required_topics)

        # Assert
        assert result == ""

    def test_should_group_by_category_and_sort_alphabetically(
        self, make_profile, make_job
    ):
        # Arrange — all four skills contain "cfd" or "python" so they match
        profile = make_profile(
            skills=[
                Skill(category="software", name="Delta Python", proficiency="expert"),
                Skill(category="technical", name="Beta CFD", proficiency="advanced"),
                Skill(category="software", name="Gamma Python", proficiency="intermediate"),
                Skill(category="technical", name="Alpha CFD", proficiency="advanced"),
            ]
        )
        job = make_job(["cfd", "python"])

        # Act
        result = _build_skills_block(profile, job.required_topics)

        # Assert — grouped by category, alphabetically within group
        # Categories are sorted alphabetically: "software" < "technical"
        software_pos = result.index("Software")
        technical_pos = result.index("Technical")
        assert software_pos < technical_pos
        # Within Software: "Delta Python" before "Gamma Python" (D < G)
        assert result.index("Delta Python") < result.index("Gamma Python")
        # Within Technical: "Alpha CFD" before "Beta CFD" (A < B)
        assert result.index("Alpha CFD") < result.index("Beta CFD")


# ---------------------------------------------------------------------------
# _assemble_details
# ---------------------------------------------------------------------------


class TestAssembleDetails:
    def test_should_place_skills_block_first(self):
        # Arrange
        skills_block = "### Relevant Skills\n- **Tech**: CFD (advanced)"
        scored_sections = [
            ("Alpha Project", "alpha body", 5.0),
            ("Beta Project", "beta body", 3.0),
        ]
        max_tokens = 1000  # generous budget

        # Act
        result = _assemble_details(skills_block, scored_sections, max_tokens)

        # Assert — skills block appears before any scored section
        assert result.startswith(skills_block)
        # Alpha (higher score) appears before Beta
        assert result.index("Alpha Project") < result.index("Beta Project")

    def test_should_respect_token_budget(self):
        # Arrange
        # Skills block: ~26 chars → ~6 tokens
        skills_block = "### RS\n- **T**: X (adv)"
        # Section Alpha: "### Alpha\n" + 80 a's = 90 chars → 22 tokens
        # Section Beta:  "### Beta\n"  + 80 b's = 90 chars → 22 tokens
        # total skills + Alpha = 6 + 22 = 28 → fits in max=30
        # total skills + Alpha + Beta = 28 + 22 = 50 → doesn't fit
        scored_sections = [
            ("Alpha", "a" * 80, 10.0),
            ("Beta", "b" * 80, 5.0),
        ]
        max_tokens = 30

        # Act
        result = _assemble_details(skills_block, scored_sections, max_tokens)

        # Assert
        assert "Alpha" in result
        assert "Beta" not in result

    def test_should_not_include_sections_beyond_budget_in_fallback(self):
        """After scored sections consume the budget, fallback sections are excluded."""
        # Arrange
        skills_block = "### RS\n- **T**: X (adv)"
        scored_sections = [
            ("Zeta", "z" * 80, 10.0),
            ("Alpha", "a" * 80, 5.0),
            ("Beta", "b" * 80, 1.0),
        ]
        max_tokens = 30

        # Act
        result = _assemble_details(skills_block, scored_sections, max_tokens)

        # Assert — only skills + highest-scored sections that fit are included
        # Zeta and Alpha together would exceed budget; only the skills and maybe
        # one section should fit.
        sections_included = sum(1 for s in ["Zeta", "Alpha", "Beta"] if s in result)
        assert sections_included <= 2  # at most 1 scored section + skills

    def test_should_return_empty_for_empty_inputs(self):
        # Arrange
        skills_block = ""
        scored_sections: list = []

        # Act
        result = _assemble_details(skills_block, scored_sections, max_tokens=1000)

        # Assert
        assert result == ""


# ---------------------------------------------------------------------------
# select_relevant_details (integration)
# ---------------------------------------------------------------------------


class TestSelectRelevantDetails:
    def test_should_use_background_text_path(self, make_profile, make_job):
        """High-level integration: background_text → skills block + relevant sections."""
        # Arrange
        profile = make_profile(
            projects=[
                ProjectSummary(
                    name="CFD Analysis",
                    type="academic",
                    role="Researcher",
                    duration="2023",
                    key_contribution="Optimized turbine blade design.",
                    technologies=["OpenFOAM"],
                    topics=["cfd", "thermal"],
                ),
                ProjectSummary(
                    name="Web App",
                    type="academic",
                    role="Developer",
                    duration="2022",
                    key_contribution="Built a React dashboard.",
                    technologies=["React"],
                    topics=["web", "frontend"],
                ),
            ],
            skills=[
                Skill(category="technical", name="CFD", proficiency="advanced"),
                Skill(category="software", name="React", proficiency="intermediate"),
            ],
        )
        job = make_job(["cfd", "thermal"])
        background_text = (
            "### CFD Analysis\n"
            "Simulated airflow over turbine blades using OpenFOAM.\n"
            "### Web App\n"
            "Developed a dashboard for real-time sensor data.\n"
            "### Other Stuff\n"
            "Miscellaneous notes about hobbies."
        )

        # Act
        result = select_relevant_details(
            job=job,
            profile=profile,
            background_text=background_text,
            max_tokens=500,
        )

        # Assert — skills block is present
        assert "Relevant Skills" in result
        assert "CFD" in result
        # High-relevance section (CFD Analysis) appears first among sections
        assert "CFD Analysis" in result
        # Rough token budget check (separators are not counted by _estimate_tokens,
        # but the overall output should be roughly within budget)
        assert len(result) // CHARS_PER_TOKEN <= 500 + 5

    def test_should_use_md_files_for_backward_compatibility(
        self, make_profile, make_job
    ):
        """Multi-file mode: matches projects to md_files by name heuristic."""
        # Arrange
        profile = make_profile(
            projects=[
                ProjectSummary(
                    name="CFD Analysis",
                    type="academic",
                    role="Researcher",
                    duration="2023",
                    key_contribution="Simulated airflow.",
                    technologies=["OpenFOAM"],
                    topics=["cfd"],
                )
            ]
        )
        job = make_job(["cfd"])
        md_files = {
            "cfd_analysis": "Detailed CFD simulation results and methodology.",
            "web_app": "Frontend development notes for the dashboard project.",
        }

        # Act
        result = select_relevant_details(
            job=job,
            profile=profile,
            md_files=md_files,
            max_tokens=500,
        )

        # Assert — matched file content is included (normalised name matching)
        assert "CFD Analysis" in result or "cfd_analysis" in result

    def test_should_raise_value_error_for_mutual_exclusivity(
        self, make_profile, make_job
    ):
        # Arrange
        profile = make_profile()
        job = make_job(["cfd"])

        # Act & Assert
        with pytest.raises(
            ValueError, match="Cannot provide both background_text and md_files"
        ):
            select_relevant_details(
                job=job,
                profile=profile,
                background_text="some text",
                md_files={"file": "content"},
            )

    def test_should_return_empty_when_neither_input_provided(
        self, make_profile, make_job
    ):
        # Arrange
        profile = make_profile()
        job = make_job(["cfd"])

        # Act
        result = select_relevant_details(job=job, profile=profile)

        # Assert
        assert result == ""
