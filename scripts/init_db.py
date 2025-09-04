from database.connection import get_database

def create_indexes():
    """Create necessary database indexes"""
    db = get_database()
    
    # Candidate collection indexes
    db.candidates.create_index("candidate_id", unique=True)
    db.candidates.create_index("email", unique=True)
    
    # Interview sessions indexes
    db.interview_sessions.create_index("session_id", unique=True)
    db.interview_sessions.create_index("candidate_id")
    db.interview_sessions.create_index("status")
    
    print("Database indexes created successfully!")

if __name__ == "__main__":
    create_indexes()
