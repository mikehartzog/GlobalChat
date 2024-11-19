from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
from sqlalchemy.dialects.postgresql import JSONB

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    preferred_language = Column(String, default="en")
    auto_translate = Column(Boolean, default=False)  # Added properly
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    messages = relationship("Message", back_populates="sender")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    original_language = Column(String)
    sender_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    translations = Column(Text, default='{}')

    # Relationship with user
    sender = relationship("User", back_populates="messages")

    def get_translations(self) -> dict:
        """Return translations as a dictionary"""
        if not self.translations:
            return {}
        try:
            return json.loads(self.translations)
        except json.JSONDecodeError:
            return {}