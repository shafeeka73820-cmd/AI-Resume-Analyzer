import json
import uuid
from pathlib import Path
from datetime import datetime, timezone

from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel

from app.services.parser_service import extract_text
from app.services.analyzer_service import analyze_resume, score_against_jd

router = APIRouter(prefix="/api")


class AnalyzeRequest(BaseModel):
    resumeText: str
    jobDescription: str = "general software engineering role"
    userEmail: str = "anonymous@example.com"
    resumeName: str = "resume.pdf"


@router.get("/health")
async def health_check():
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.post("/upload")
async def upload_file(resume: UploadFile = File(...)):
    ext = Path(resume.filename).suffix.lower()
    if ext not in (".pdf", ".docx", ".txt"):
        raise HTTPException(400, "Only PDF, DOCX, and TXT files are allowed")

    content = await resume.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(400, "File size exceeds 10MB limit")

    tmp = Path("uploads") / f"{uuid.uuid4().hex}{ext}"
    tmp.parent.mkdir(exist_ok=True)
    tmp.write_bytes(content)

    try:
        text = extract_text(tmp)
    except Exception as e:
        tmp.unlink(missing_ok=True)
        raise HTTPException(500, f"Failed to parse file: {e}")

    tmp.unlink(missing_ok=True)
    return {"text": text, "filename": resume.filename}


@router.post("/analyze")
async def analyze(req: AnalyzeRequest):
    try:
        analysis = analyze_resume(req.resumeText, req.resumeName)
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {e}")

    try:
        match = score_against_jd(req.resumeText, req.jobDescription)
    except Exception:
        match = None

    # Build response matching the Django API format
    matched_keywords = []
    missing_keywords = []
    if match and hasattr(match, "breakdown"):
        matched_keywords = ["keyword_" + str(i) for i in range(3)]
        missing_keywords = ["missing_" + str(i) for i in range(3)]

    breakdown = dict(analysis.ats_score.breakdown) if analysis.ats_score.breakdown else {}

    suggestions_full = list(analysis.suggestions) if analysis.suggestions else []
    if analysis.ats_score.suggestions:
        suggestions_full.extend(analysis.ats_score.suggestions)

    return {
        "id": str(uuid.uuid4()),
        "user_email": req.userEmail,
        "resume_name": req.resumeName,
        "ats_score": analysis.ats_score.score,
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "suggestions": suggestions_full,
        "breakdown": breakdown,
        "skills": [s.model_dump() for s in analysis.skills],
        "experience": [e.model_dump() for e in analysis.experience],
        "education": [e.model_dump() for e in analysis.education],
        "roadmap": [
            {"month": "Month 1", "title": "Foundations", "items": ["Review core concepts"]},
            {"month": "Month 2", "title": "Build Projects", "items": ["Apply skills in practice"]},
            {"month": "Month 3", "title": "Polish & Apply", "items": ["Refine portfolio"]},
        ],
        "skill_improvement": [
            {"skill": s.name, "steps": [f"Improve {s.name} proficiency"], "resources": []}
            for s in analysis.skills[:3]
        ],
        "sample_roadmaps": [],
    }
