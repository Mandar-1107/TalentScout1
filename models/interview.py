from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class ConversationMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime
    question_id: Optional[str] = None
    technology: Optional[str] = None

class InterviewSession(BaseModel):
    session_id: str = Field(default_factory=lambda: __import__('uuid').uuid4().hex)
    candidate_id: str
    status: str = "active"  # "active", "paused", "completed"
    tech_plan: list[dict] = Field(default_factory=list)
    current_tech_index: int = 0
    conversation_history: list[ConversationMessage] = Field(default_factory=list)
    tech_ratings: dict = Field(default_factory=dict)  # Technology-wise ratings
    answer_ratings: list[dict] = Field(default_factory=list)  # Individual answer ratings
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    average_rating: Optional[float] = None
    total_points: float = 0  # Accumulate total points
    max_possible_points: float = 0  # Track maximum possible points
    total_rating_display: str = "0/0"  # Display format like "15/30"

    def update_total_rating(self, points: float, max_points: float):
        """Update the total rating when new points are added"""
        self.total_points += points
        self.max_possible_points += max_points
        self.total_rating_display = f"{round(self.total_points)}/{round(self.max_possible_points)}"
        if self.max_possible_points > 0:
            self.average_rating = (self.total_points / self.max_possible_points) * 10
