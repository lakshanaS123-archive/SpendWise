import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from django.conf import settings

logger = logging.getLogger("spendwise.mongodb")

try:
    from pymongo import MongoClient
    from pymongo.errors import PyMongoError
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False
    PyMongoError = Exception


class MongoService:
    """
    MongoDB service for storing chat conversations and user feedback.
    Gracefully handles connection failures without crashing the application.
    """

    _client: Optional[Any] = None

    @classmethod
    def get_client(cls):
        """
        Returns a cached or new MongoClient instance with a fast connection timeout.
        """
        if not PYMONGO_AVAILABLE:
            return None

        uri = getattr(settings, "MONGODB_URI", "").strip()
        if not uri:
            return None

        if cls._client is None:
            try:
                # 3000ms server selection timeout to prevent blocking if MongoDB is unreachable
                cls._client = MongoClient(
                    uri,
                    serverSelectionTimeoutMS=3000,
                    connectTimeoutMS=3000,
                )
            except Exception as e:
                logger.warning(f"Failed to initialize MongoClient: {e}")
                return None

        return cls._client

    @classmethod
    def get_database(cls):
        client = cls.get_client()
        if client is None:
            return None
        db_name = getattr(settings, "MONGODB_DATABASE", "spendwise")
        try:
            return client[db_name]
        except Exception as e:
            logger.warning(f"Error accessing MongoDB database {db_name}: {e}")
            return None

    @classmethod
    def check_health(cls) -> Dict[str, Any]:
        """
        Pings MongoDB server and returns connection health dictionary.
        """
        if not PYMONGO_AVAILABLE:
            return {
                "status": "unavailable",
                "reason": "pymongo library not installed",
                "connected": False,
            }

        uri = getattr(settings, "MONGODB_URI", "").strip()
        if not uri:
            return {
                "status": "unconfigured",
                "reason": "MONGODB_URI environment variable is not configured",
                "connected": False,
            }

        client = cls.get_client()
        if client is None:
            return {
                "status": "disconnected",
                "reason": "Could not create MongoDB client",
                "connected": False,
            }

        try:
            client.admin.command("ping")
            return {
                "status": "connected",
                "database": getattr(settings, "MONGODB_DATABASE", "spendwise"),
                "connected": True,
            }
        except Exception as e:
            logger.warning(f"MongoDB ping failed: {e}")
            return {
                "status": "disconnected",
                "reason": "Server connection failed or timed out",
                "connected": False,
            }

    @classmethod
    def save_message(
        cls,
        conversation_id: str,
        user_id: Optional[int],
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Appends a chat message to the conversation document in MongoDB.
        """
        db = cls.get_database()
        if db is None:
            return False

        try:
            now = datetime.now(timezone.utc)
            msg_doc = {
                "message_id": str(uuid.uuid4()),
                "role": role,
                "content": content[:4000],  # Validate reasonable length
                "timestamp": now.isoformat(),
                "metadata": metadata or {},
            }

            db.conversations.update_one(
                {"conversation_id": conversation_id},
                {
                    "$setOnInsert": {
                        "conversation_id": conversation_id,
                        "user_id": user_id,
                        "created_at": now.isoformat(),
                    },
                    "$set": {"updated_at": now.isoformat()},
                    "$push": {"messages": msg_doc},
                },
                upsert=True,
            )
            return True
        except Exception as e:
            logger.warning(f"Failed to save chat message to MongoDB: {e}")
            return False

    @classmethod
    def get_conversation_history(
        cls,
        conversation_id: str,
        user_id: Optional[int] = None,
    ) -> Optional[List[Dict[str, Any]]]:
        """
        Retrieves messages for a conversation if authorized.
        """
        db = cls.get_database()
        if db is None:
            return None

        try:
            doc = db.conversations.find_one({"conversation_id": conversation_id})
            if not doc:
                return []

            # Privacy & isolation check
            doc_user_id = doc.get("user_id")
            if doc_user_id is not None and user_id is not None and doc_user_id != user_id:
                logger.warning(
                    f"Access denied: User {user_id} tried to read conversation of user {doc_user_id}"
                )
                return None

            return doc.get("messages", [])
        except Exception as e:
            logger.warning(f"Failed to fetch conversation history from MongoDB: {e}")
            return None

    @classmethod
    def save_feedback(
        cls,
        conversation_id: str,
        user_id: Optional[int],
        rating: int,
        feedback_text: str,
    ) -> Optional[str]:
        """
        Saves user feedback for a conversation in MongoDB feedback collection.
        Returns feedback_id on success or None on error.
        """
        db = cls.get_database()
        if db is None:
            return None

        try:
            feedback_id = str(uuid.uuid4())
            doc = {
                "feedback_id": feedback_id,
                "conversation_id": conversation_id,
                "user_id": user_id,
                "rating": max(1, min(5, int(rating))),
                "feedback_text": feedback_text[:2000].strip(),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            db.feedback.insert_one(doc)
            return feedback_id
        except Exception as e:
            logger.warning(f"Failed to save feedback to MongoDB: {e}")
            return None
