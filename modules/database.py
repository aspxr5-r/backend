from pymongo import MongoClient
from config import MONGODB_URI, DATABASE_NAME

client = MongoClient(MONGODB_URI)
db = client[DATABASE_NAME]  # Specify the database name here

users = db.users
chat_sessions = db.chat_sessions

def test_connection():
    try:
        client.admin.command('ping')
        print(f"Successfully connected to MongoDB database: {DATABASE_NAME}")
    except Exception as e:
        print(f"Failed to connect to MongoDB: {e}")