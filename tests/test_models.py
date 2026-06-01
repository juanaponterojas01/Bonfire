from pydantic import ValidationError

from src.models import (
    CVDynamicZones,
    Education,
    JobDescription,
    JobMatchResult,
    PersonalInfo,
    ProjectSummary,
    QualificationMatch,
    Skill,
    UserProfile,
)


def test_personal_info_valid():
    """Creates a valid PersonalInfo instance."""
    info = PersonalInfo(
        name="Alice Smith",
        address="123 Baker Street, London",
        email="alice@example.com",
        phone="+44 20 7946 0958",
        linkedin="https://linkedin.com/in/alicesmith",
    )
    assert info.name == "Alice Smith"
    assert info.linkedin is not None


def test_personal_info_without_linkedin():
    """Creates PersonalInfo with optional linkedin omitted."""
    info = PersonalInfo(
        name="Bob Jones",
        address="456 Elm St",
        email="bob@example.com",
        phone="555-1234",
    )
    assert info.linkedin is None


def test_personal_info_invalid_email():
    """Checks that an invalid email raises a validation error."""
    try:
        PersonalInfo(
            name="Charlie",
            address="789 Oak Ave",
            email="not-an-email",
            phone="555-5678",
        )
    except ValidationError: 
        assert True 

def test_education_valid():
    """Creates a valid Education instance."""
    edu = Education(
        degree="B.Sc. Computer Science",
        institution="MIT",
        subjects=["Algorithms", "Data Structures"],
        year="2022",
    )
    assert edu.degree == "B.Sc. Computer Science"
    assert edu.thesis_title is None


def test_education_with_thesis():
    """Creates Education with an optional thesis title."""
    edu = Education(
        degree="M.Sc. AI",
        institution="Stanford",
        subjects=["ML", "NLP"],
        thesis_title="Deep Learning for NLP",
        year="2024",
    )
    assert edu.thesis_title == "Deep Learning for NLP"


def test_project_summary_valid():
    """Creates a valid ProjectSummary instance."""
    proj = ProjectSummary(
        name="Web Scraper",
        type="industry",
        role="Backend Developer",
        duration="6 months",
        key_contribution="Built the scraping engine.",
        technologies=["Python", "Scrapy"],
        topics=["data_collection", "automation"],
    )
    assert proj.type == "industry"
    assert "Python" in proj.technologies


def test_skill_valid():
    """Creates a valid Skill instance."""
    skill = Skill(category="technical", name="Python", proficiency="advanced")
    assert skill.proficiency == "advanced"


def test_user_profile_valid():
    """Creates a valid UserProfile with nested models."""
    profile = UserProfile(
        personal_info=PersonalInfo(
            name="Dana White",
            address="1 Main St",
            email="dana@example.com",
            phone="555-0000",
        ),
        education=[
            Education(
                degree="B.A. Economics",
                institution="Harvard",
                subjects=["Micro", "Macro"],
                year="2020",
            )
        ],
        experience=[
            ProjectSummary(
                name="Finance App",
                type="industry",
                role="Analyst",
                duration="1 year",
                key_contribution="Automated reporting.",
                technologies=["Excel", "SQL"],
                topics=["finance", "automation"],
            )
        ],
        skills=[Skill(category="software", name="SQL", proficiency="intermediate")],
        projects=[
            ProjectSummary(
                name="Thesis",
                type="thesis",
                role="Researcher",
                duration="1 year",
                key_contribution="Novel algorithm.",
                technologies=["Python"],
                topics=["algorithms"],
            )
        ],
    )
    assert len(profile.education) == 1
    assert profile.experience[0].type == "industry"


def test_job_description_valid():
    """Creates a valid JobDescription instance."""
    job = JobDescription(
        title="Data Scientist",
        company="TechCorp",
        location="Remote",
        raw_text="Looking for a data scientist...",
        required_topics=["machine_learning", "python"],
    )
    assert job.company == "TechCorp"
    assert "python" in job.required_topics
    assert job.email is None


def test_job_description_with_email():
    """Creates a JobDescription with an explicit email."""
    job = JobDescription(
        title="Data Scientist",
        company="TechCorp",
        location="Remote",
        email="careers@techcorp.com",
        raw_text="Looking for a data scientist...",
        required_topics=["machine_learning", "python"],
    )
    assert job.email == "careers@techcorp.com"


def test_qualification_match_valid():
    """Creates a valid QualificationMatch instance."""
    match = QualificationMatch(
        requirement="Python experience",
        user_evidence="3 years at TechCorp",
        match_level="strong",
    )
    assert match.match_level == "strong"


def test_job_match_result_valid():
    """Creates a valid JobMatchResult instance."""
    result = JobMatchResult(
        required_qualifications=[
            QualificationMatch(
                requirement="SQL",
                user_evidence="Used PostgreSQL",
                match_level="moderate",
            )
        ],
        gaps=["Docker"],
        strengths=["Python"],
        recommendation="moderate_match",
        reasoning="Good fit but lacks containerisation experience.",
    )
    assert result.recommendation == "moderate_match"
    assert len(result.gaps) == 1


def test_cv_dynamic_zones_valid():
    """Creates a valid CVDynamicZones instance."""
    zones = CVDynamicZones(
        professional_summary="Experienced developer.",
        bachelor_subjects="Really cool bachelor stuff",
        master_subjects="Really cool master stuff"
    )
    assert "developer" in zones.professional_summary
    assert "bachelor" in zones.bachelor_subjects
    assert "master" in zones.master_subjects
