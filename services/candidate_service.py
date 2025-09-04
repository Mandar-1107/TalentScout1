from models.candidate import Candidate
from typing import Optional, List

class CandidateService:
    def __init__(self, db):
        self.db = db
        self.collection = db.candidates

    def create_candidate(self, candidate_data: dict) -> str:
        """Create new candidate profile"""
        candidate = Candidate(**candidate_data)
        result = self.collection.insert_one(candidate.model_dump())
        return candidate.candidate_id

    def get_candidate(self, candidate_id: str) -> Optional[Candidate]:
        """Retrieve candidate by ID"""
        candidate_doc = self.collection.find_one(
            {"candidate_id": candidate_id}
        )
        return Candidate(**candidate_doc) if candidate_doc else None

    def update_tech_stack(self, candidate_id: str, tech_stack: list[dict]):
        """Update candidate's tech stack"""
        result = self.collection.update_one(
            {"candidate_id": candidate_id},
            {"$set": {"tech_stack": tech_stack}}
        )
        return result
