import json
from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./resume_analyzer.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class AnalysisRecord(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    filename = Column(String, nullable=False)
    skills_json = Column(Text, default="[]")
    experience_json = Column(Text, default="[]")
    education_json = Column(Text, default="[]")
    ats_score = Column(Float, default=0.0)
    ats_breakdown_json = Column(Text, default="{}")
    ats_suggestions_json = Column(Text, default="[]")
    suggestions_json = Column(Text, default="[]")

    job_description = Column(Text, nullable=True)
    match_score = Column(Float, nullable=True)
    match_breakdown_json = Column(Text, nullable=True)
    match_suggestions_json = Column(Text, nullable=True)

    def to_analysis_dict(self) -> dict:
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "filename": self.filename,
            "skills": json.loads(self.skills_json or "[]"),
            "experience": json.loads(self.experience_json or "[]"),
            "education": json.loads(self.education_json or "[]"),
            "ats_score": {
                "score": self.ats_score,
                "breakdown": json.loads(self.ats_breakdown_json or "{}"),
                "suggestions": json.loads(self.ats_suggestions_json or "[]"),
            },
            "suggestions": json.loads(self.suggestions_json or "[]"),
            "job_description": self.job_description,
            "match_score": self.match_score,
            "match_breakdown": json.loads(self.match_breakdown_json) if self.match_breakdown_json else None,
            "match_suggestions": json.loads(self.match_suggestions_json) if self.match_suggestions_json else [],
        }


def init_db():
    Base.metadata.create_all(bind=engine)
