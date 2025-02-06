from pymongo import MongoClient, ASCENDING, TEXT, DESCENDING
from datetime import datetime
import bcrypt
import os

# Connection setup
uri = "mongodb+srv://koushik83:Sumada081@cluster0.4w12y.mongodb.net/?retryWrites=true&w=majority"
client = MongoClient(uri)
db = client.chatbot

# Test connection immediately
try:
    client.admin.command('ping')
    print("Connected successfully!")
except Exception as e:
    print(e)

def init_database():
    """Initialize database collections and indexes"""
    try:
        # Users Collection
        if "users" not in db.list_collection_names():
            db.create_collection("users")
        db.users.create_index([("email", ASCENDING)], unique=True)
        db.users.create_index([("username", ASCENDING)], unique=True)
        db.users.create_index([("phoneNumber", ASCENDING)])
        db.users.create_index([("firstName", ASCENDING)])
        db.users.create_index([("lastName", ASCENDING)])
        db.users.create_index([("role.institutionId", ASCENDING)])
        db.users.create_index([("role.type", ASCENDING)])
        db.users.create_index([("status", ASCENDING)])

        # Roles Collection
        if "roles" not in db.list_collection_names():
            db.create_collection("roles")
        db.roles.create_index([("name", ASCENDING)], unique=True)

        # Access Logs Collection
        if "accessLogs" not in db.list_collection_names():
            db.create_collection("accessLogs")
        db.accessLogs.create_index([("userId", ASCENDING), ("timestamp", DESCENDING)])
        db.accessLogs.create_index([("action", ASCENDING)])
        db.accessLogs.create_index([("institutionId", ASCENDING)])

        # Institutions Collection
        if "institutions" not in db.list_collection_names():
            db.create_collection("institutions")
        db.institutions.create_index([("name", ASCENDING)])
        db.institutions.create_index([("apiKey", ASCENDING)], unique=True)
        db.institutions.create_index([("status", ASCENDING)])

        # Documents Collection
        if "documents" not in db.list_collection_names():
            db.create_collection("documents")
        db.documents.create_index([("institutionId", ASCENDING)])
        db.documents.create_index([("uploadedBy", ASCENDING)])
        db.documents.create_index([("status", ASCENDING)])
        db.documents.create_index([("content.text", TEXT)])
        db.documents.create_index([("createdAt", DESCENDING)])

        # Chat Sessions Collection
        if "chatSessions" not in db.list_collection_names():
            db.create_collection("chatSessions")
        db.chatSessions.create_index([("institutionId", ASCENDING)])
        db.chatSessions.create_index([("userId", ASCENDING)])
        db.chatSessions.create_index([("status", ASCENDING)])
        db.chatSessions.create_index([("lastActivityAt", DESCENDING)])

        # Messages Collection
        if "messages" not in db.list_collection_names():
            db.create_collection("messages")
        db.messages.create_index([("sessionId", ASCENDING)])
        db.messages.create_index([("institutionId", ASCENDING)])
        db.messages.create_index([("userId", ASCENDING)])
        db.messages.create_index([("createdAt", DESCENDING)])

        # Analytics Collection
        if "analytics" not in db.list_collection_names():
            db.create_collection("analytics")
        db.analytics.create_index([("institutionId", ASCENDING)])
        db.analytics.create_index([("period.type", ASCENDING)])
        db.analytics.create_index([("period.start", ASCENDING)])

        # Usage Collection
        if "usage" not in db.list_collection_names():
            db.create_collection("usage")
        db.usage.create_index([("institutionId", ASCENDING)])
        db.usage.create_index([("date", ASCENDING)])
        db.usage.create_index([("resourceType", ASCENDING)])

        print("Collections and indexes created successfully!")
        
        # Insert initial data
        setup_initial_data()
        
        print("Database initialization completed successfully!")
        return True
    except Exception as e:
        print(f"Database initialization failed: {e}")
        return False

def setup_initial_data():
    """Insert initial data if collections are empty"""
    try:
        # Create roles if they don't exist
        if db.roles.count_documents({}) == 0:
            roles = [
                {
                    "name": "super_admin",
                    "permissions": [
                        "manage_all_institutions",
                        "manage_institutional_admins",
                        "system_configuration",
                        "view_system_analytics",
                        "manage_roles",
                        "manage_users"
                    ],
                    "description": "System-wide administrator with full access",
                    "status": "active",
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                },
                {
                    "name": "institutional_admin",
                    "permissions": [
                        "manage_institution",
                        "manage_users",
                        "manage_documents",
                        "view_analytics",
                        "manage_chat_sessions"
                    ],
                    "description": "Administrator for a specific institution",
                    "status": "active",
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                },
                {
                    "name": "user",
                    "permissions": [
                        "chat_access",
                        "view_documents",
                        "view_history"
                    ],
                    "description": "Regular user with basic access",
                    "status": "active",
                    "createdAt": datetime.utcnow(),
                    "updatedAt": datetime.utcnow()
                }
            ]
            db.roles.insert_many(roles)
            print("Roles created successfully!")

        # Create super admin if doesn't exist
        if db.users.count_documents({"username": "koushik83"}) == 0:
            hashed_password = bcrypt.hashpw("Chippi081".encode('utf-8'), bcrypt.gensalt())
            super_admin = {
                "username": "koushik83",
                "email": "koushik83@admin.com",
                "passwordHash": hashed_password,
                "firstName": "Koushik",
                "lastName": "Admin",
                "phoneNumber": "+1234567890",
                "role": {
                    "type": "super_admin",
                    "permissions": [
                        "manage_all_institutions",
                        "manage_institutional_admins",
                        "system_configuration",
                        "view_system_analytics",
                        "manage_roles",
                        "manage_users"
                    ]
                },
                "status": "active",
                "metadata": {
                    "lastLogin": None,
                    "lastPasswordChange": datetime.utcnow(),
                    "failedLoginAttempts": 0,
                    "twoFactorEnabled": False
                },
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            db.users.insert_one(super_admin)
            print("Super admin created successfully!")

        # Create default institution if doesn't exist
        if db.institutions.count_documents({}) == 0:
            default_institution = {
                "name": "Default Institution",
                "type": "business",
                "apiKey": os.urandom(24).hex(),
                "status": "active",
                "subscription": {
                    "plan": "basic",
                    "status": "active",
                    "features": ["chat", "document_upload", "basic_analytics"],
                    "limits": {
                        "maxUsers": 100,
                        "maxStorage": 5368709120,  # 5GB in bytes
                        "maxQueries": 10000
                    },
                    "expiresAt": None
                },
                "config": {
                    "chatbot": {
                        "name": "Assistant",
                        "welcomeMessage": "Hello! How can I help you today?",
                        "fallbackMessage": "I'm sorry, I couldn't understand that."
                    },
                    "allowedFileTypes": ["pdf", "docx", "txt"],
                    "languages": ["en"]
                },
                "createdAt": datetime.utcnow(),
                "updatedAt": datetime.utcnow()
            }
            institution = db.institutions.insert_one(default_institution)
            print("Default institution created successfully!")

        print("Initial data setup completed successfully!")
    except Exception as e:
        print(f"Error setting up initial data: {e}")
        raise

def get_db():
    """Get database instance"""
    return db

if __name__ == "__main__":
    if init_database():
        print("Database setup complete!")
    else:
        print("Database setup failed!")
