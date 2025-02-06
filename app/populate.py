from pymongo import MongoClient
from datetime import datetime
import bcrypt
import os

# MongoDB Connection
uri = "mongodb+srv://koushik83:Sumada081@cluster0.4w12y.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client.chatbot

# Create Dummy Users
def create_users():
    users = [
        {
            "username": "testuser1",
            "email": "testuser1@example.com",
            "passwordHash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "firstName": "John",
            "lastName": "Doe",
            "phoneNumber": "+1111111111",
            "role": {"type": "user"},
            "status": "active",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        },
        {
            "username": "testuser2",
            "email": "testuser2@example.com",
            "passwordHash": bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt()),
            "firstName": "Jane",
            "lastName": "Smith",
            "phoneNumber": "+2222222222",
            "role": {"type": "institutional_admin"},
            "status": "active",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    db.users.insert_many(users)
    print("Users inserted successfully")

# Create Dummy Institutions
def create_institutions():
    institutions = [
        {
            "name": "Test Institution 1",
            "type": "business",
            "apiKey": os.urandom(24).hex(),
            "status": "active",
            "createdAt": datetime.utcnow(),
            "updatedAt": datetime.utcnow()
        }
    ]
    db.institutions.insert_many(institutions)
    print("Institutions inserted successfully")

# Create Dummy Documents
def create_documents():
    documents = [
        {
            "institutionId": "1",
            "uploadedBy": "testuser1",
            "status": "approved",
            "content": {"text": "Company policy on refunds and returns."},
            "createdAt": datetime.utcnow()
        },
        {
            "institutionId": "1",
            "uploadedBy": "testuser2",
            "status": "pending",
            "content": {"text": "Employee handbook and guidelines."},
            "createdAt": datetime.utcnow()
        }
    ]
    db.documents.insert_many(documents)
    print("Documents inserted successfully")

# Create Dummy Chat Sessions
def create_chat_sessions():
    chat_sessions = [
        {
            "institutionId": "1",
            "userId": "testuser1",
            "status": "active",
            "lastActivityAt": datetime.utcnow()
        }
    ]
    db.chatSessions.insert_many(chat_sessions)
    print("Chat sessions inserted successfully")

# Create Dummy Messages
def create_messages():
    messages = [
        {
            "sessionId": "1",
            "institutionId": "1",
            "userId": "testuser1",
            "content": "What is the refund policy?",
            "createdAt": datetime.utcnow()
        },
        {
            "sessionId": "1",
            "institutionId": "1",
            "userId": "chatbot",
            "content": "Our refund policy allows returns within 30 days.",
            "createdAt": datetime.utcnow()
        }
    ]
    db.messages.insert_many(messages)
    print("Messages inserted successfully")

if __name__ == "__main__":
    create_users()
    create_institutions()
    create_documents()
    create_chat_sessions()
    create_messages()
    print("Database populated with dummy data!")
