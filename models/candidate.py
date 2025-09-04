from datetime import datetime
import uuid
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, field_validator
from models.common import ProficiencyLevel

class TechStack(BaseModel):
    category: str
    technologies: list[dict]  # {"name": "Python", "proficiency": "Advanced"}

class Candidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    full_name: str
    email: EmailStr
    phone_number: str
    years_experience: int
    desired_positions: list[str]
    current_location: str
    tech_stack: list[TechStack] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    @field_validator("full_name")
    @classmethod
    def validate_full_name(cls, v: str) -> str:
        if len(v.split()) < 2:
            raise ValueError("Full name must contain at least 2 words")
        return v

    @field_validator("years_experience")
    @classmethod
    def validate_experience(cls, v: int) -> int:
        if not 0 <= v <= 50:
            raise ValueError("Years of experience must be between 0 and 50")
        return v
