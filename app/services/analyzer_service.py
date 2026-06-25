from app.models.schemas import (
    ResumeAnalysis,
    Skill,
    Experience,
    Education,
    ATSScore,
    SemanticMatchResult,
)
from app.services.llm_client import parse_json_from_llm
from app.services.matcher_service import compute_semantic_match

ANALYSIS_PROMPT = """You are an expert resume analyzer. Analyze the following resume text and return a JSON object with this exact structure:
{
    "skills": [
        {"name": "<skill>", "category": "<Technical|Soft|Domain>", "proficiency": "<Beginner|Intermediate|Advanced|Expert>"}
    ],
    "experience": [
        {"company": "<company>", "role": "<role>", "duration": "<duration>", "description": ["<point1>", "<point2>"]}
    ],
    "education": [
        {"institution": "<inst>", "degree": "<degree>", "field": "<field>", "year": "<year>"}
    ],
    "ats_score": {
        "score": <0-100>,
        "breakdown": {
            "formatting": <0-100>,
            "keywords": <0-100>,
            "experience": <0-100>,
            "education": <0-100>,
            "skills": <0-100>
        },
        "suggestions": ["<suggestion1>", "<suggestion2>"]
    },
    "suggestions": ["<overall_suggestion1>", "<overall_suggestion2>"]
}

Resume text:
{resume_text}

Return ONLY valid JSON, no markdown or extra text."""


def get_ai_analysis(resume_text: str, filename: str) -> ResumeAnalysis:
    return analyze_resume(resume_text, filename)

def analyze_resume(resume_text: str, filename: str) -> ResumeAnalysis:
    data = parse_json_from_llm(ANALYSIS_PROMPT.format(resume_text=resume_text))

    skills = [Skill(**s) for s in data.get("skills", [])]
    experience = [Experience(**e) for e in data.get("experience", [])]
    education = [Education(**e) for e in data.get("education", [])]
    ats = ATSScore(**data.get("ats_score", {}))
    suggestions = data.get("suggestions", [])

    return ResumeAnalysis(
        filename=filename,
        skills=skills,
        experience=experience,
        education=education,
        ats_score=ats,
        suggestions=suggestions,
    )


def score_against_jd(
    resume_text: str, job_description: str
) -> SemanticMatchResult:
    return compute_semantic_match(resume_text, job_description)
