import os
from datetime import datetime, timedelta
from typing import Optional

class AdminService:
    def __init__(self, db):
        self.db = db
        self.sessions = db.interview_sessions
        self.candidates = db.candidates

    def get_total_interviews(self) -> int:
        return self.sessions.count_documents({})

    def get_interviews_today(self) -> int:
        start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        return self.sessions.count_documents({"started_at": {"$gte": start}})

    def get_avg_interview_duration(self) -> float:
        pipeline = [
            {"$match": {"completed_at": {"$ne": None}, "started_at": {"$ne": None}}},
            {"$project": {
                "duration": {"$divide": [{"$subtract": ["$completed_at", "$started_at"]}, 60000.0]}
            }},
            {"$group": {"_id": None, "avg": {"$avg": "$duration"}}}
        ]
        docs = list(self.sessions.aggregate(pipeline))
        return float(docs[0]["avg"]) if docs else 0.0

    def get_success_rate(self) -> float:
        total = self.sessions.count_documents({})
        if total == 0:
            return 0.0
        completed = self.sessions.count_documents({"status": "completed"})
        return round(100.0 * completed / total, 1)

    def get_daily_interview_counts(self, days: int = 14) -> list:
        start = datetime.utcnow() - timedelta(days=days)
        pipeline = [
            {"$match": {"started_at": {"$gte": start}}},
            {"$group": {
                "_id": {
                    "y": {"$year": "$started_at"},
                    "m": {"$month": "$started_at"},
                    "d": {"$dayOfMonth": "$started_at"}
                },
                "count": {"$sum": 1}
            }},
            {"$sort": {"_id.y": 1, "_id.m": 1, "_id.d": 1}}
        ]
        docs = list(self.sessions.aggregate(pipeline))
        return [{"date": f"{d['_id']['y']:04d}-{d['_id']['m']:02d}-{d['_id']['d']:02d}", "count": d["count"]} for d in docs]

    def get_technology_popularity(self, top_n: int = 15) -> list:
        pipeline = [
            {"$unwind": "$questions_asked"},
            {"$group": {"_id": "$questions_asked.technology", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$limit": top_n}
        ]
        docs = list(self.sessions.aggregate(pipeline))
        return [{"technology": d["_id"] or "Unspecified", "count": d["count"]} for d in docs]

    def get_recent_interviews(self, limit: int = 25) -> list:
        sessions = list(self.sessions.find(
            {},
            {"_id": 0, "candidate_id": 1, "status": 1, "questions_asked": 1, "started_at": 1, "completed_at": 1}
        ).sort("started_at", -1).limit(limit))
        
        result = []
        for s in sessions:
            cand = list(self.candidates.find(
                {"candidate_id": s["candidate_id"]},
                {"_id": 0, "full_name": 1, "desired_positions": 1}
            ).limit(1))
            
            name = cand[0]["full_name"] if cand else "Unknown"
            positions = ", ".join(cand[0].get("desired_positions", [])) if cand else ""
            techs = sorted({q.get("technology", "") for q in s.get("questions_asked", []) if q.get("technology")})
            
            result.append({
                "candidate_name": name,
                "position": positions,
                "status": s.get("status", ""),
                "technologies": ", ".join(techs),
                "started_at": s.get("started_at"),
                "completed_at": s.get("completed_at"),
            })
        return result
