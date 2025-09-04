import os
import logging
from typing import Optional
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Database:
    sync_client: Optional[MongoClient] = None

database = Database()

def get_connection_string() -> str:
    mongodb_url = os.getenv("MONGODB_URL") or os.getenv("MONGODB_URI")
    if not mongodb_url:
        logger.warning("No MONGODB_URL found in environment, using localhost")
        return "mongodb://localhost:27017"
    
    logger.info(f"Using MongoDB connection: {mongodb_url[:30]}...")
    return mongodb_url

def get_database():
    """Synchronous database connection for Streamlit"""
    connection_string = get_connection_string()
    
    try:
        if database.sync_client is None:
            # Basic connection with minimal options
            database.sync_client = MongoClient(connection_string)
            
            # Test the connection
            database.sync_client.admin.command('ping')
            logger.info("✅ Successfully connected to MongoDB")
        
        db_name = os.getenv("MONGODB_DB", "interview_system")
        return database.sync_client[db_name]
        
    except Exception as e:
        logger.error(f"❌ Failed to connect to MongoDB: {e}")
        raise ConnectionError(f"Cannot connect to MongoDB: {e}")

def close_connection():
    if database.sync_client:
        database.sync_client.close()
        database.sync_client = None
        logger.info("Closed MongoDB connection")
