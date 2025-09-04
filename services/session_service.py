# services/session_service.py
class SessionService:
    def __init__(self, db):
        self.db = db
        self.collection = db.interview_sessions

    async def pause_session(self, session_id: str):
        """Pause an active interview session"""
        await self.collection.update_one(
            {"session_id": session_id},
            {
                "$set": {
                    "status": "paused",
                    "paused_at": datetime.now()
                }
            }
        )

    async def resume_session(self, session_id: str) -> bool:
        """Resume a paused interview session"""
        session = await self.collection.find_one({"session_id": session_id})
        
        if session and session.get("status") == "paused":
            await self.collection.update_one(
                {"session_id": session_id},
                {
                    "$set": {
                        "status": "active",
                        "resumed_at": datetime.now()
                    },
                    "$unset": {"paused_at": ""}
                }
            )
            return True
        return False

    async def get_session_summary(self, session_id: str) -> Dict:
        """Generate comprehensive session summary"""
        session = await self.collection.find_one({"session_id": session_id})
        
        if not session:
            return {}
        
        # Calculate metrics
        total_questions = len(session.get("questions_asked", []))
        duration = self._calculate_duration(session)
        technologies_covered = list(set([
            q.get("technology") for q in session.get("questions_asked", [])
        ]))
        
        return {
            "session_id": session_id,
            "total_questions": total_questions,
            "duration_minutes": duration,
            "technologies_covered": technologies_covered,
            "conversation_length": len(session.get("conversation_history", [])),
            "completion_status": session.get("status"),
            "started_at": session.get("started_at"),
            "completed_at": session.get("completed_at")
        }
