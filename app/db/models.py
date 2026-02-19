"""
SQLAlchemy ORM models for SQLite (HF Spaces compatible).
Tables: users, notebooks, sources, chat_messages
"""
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, DateTime, ForeignKey
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id           = Column(String(36), primary_key=True, default=_uuid)
    email        = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name    = Column(String(255), nullable=True)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    notebooks = relationship("Notebook", back_populates="owner", cascade="all, delete-orphan")


class Notebook(Base):
    __tablename__ = "notebooks"

    id          = Column(String(36), primary_key=True, default=_uuid)
    title       = Column(String(255), nullable=False, default="Untitled Notebook")
    description = Column(Text, nullable=True)
    owner_id    = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner    = relationship("User", back_populates="notebooks")
    sources  = relationship("Source", back_populates="notebook", cascade="all, delete-orphan")
    messages = relationship("ChatMessage", back_populates="notebook", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id           = Column(String(36), primary_key=True, default=_uuid)
    notebook_id  = Column(String(36), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False)
    title        = Column(String(500), nullable=False)
    # Type: pdf | url | youtube | text
    source_type  = Column(String(50), nullable=False)
    # Local file path (relative to UPLOAD_DIR) or None for URL sources
    file_path    = Column(String(1000), nullable=True)
    original_url = Column(String(2000), nullable=True)
    # Status: pending | processing | ready | failed
    status       = Column(String(50), default="pending")
    summary      = Column(Text, nullable=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    notebook = relationship("Notebook", back_populates="sources")
    chunks   = relationship("Chunk", back_populates="source", cascade="all, delete-orphan")


class Chunk(Base):
    """
    Text chunk metadata stored in SQLite.
    The actual embedding vector lives in ChromaDB (keyed by this chunk's id).
    """
    __tablename__ = "chunks"

    id          = Column(String(36), primary_key=True, default=_uuid)
    source_id   = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    content     = Column(Text, nullable=False)
    chunk_index = Column(Integer, nullable=False)
    page_number = Column(Integer, nullable=True)

    source = relationship("Source", back_populates="chunks")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id              = Column(String(36), primary_key=True, default=_uuid)
    notebook_id     = Column(String(36), ForeignKey("notebooks.id", ondelete="CASCADE"), nullable=False)
    # Role: user | assistant
    role            = Column(String(20), nullable=False)
    content         = Column(Text, nullable=False)
    # JSON array of cited chunk ids, e.g. '["uuid1", "uuid2"]'
    cited_chunk_ids = Column(Text, nullable=True)
    created_at      = Column(DateTime, default=datetime.utcnow)

    notebook = relationship("Notebook", back_populates="messages")
