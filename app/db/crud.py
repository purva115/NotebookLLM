"""
CRUD operations for all models.
All functions take a SQLAlchemy Session and return ORM objects.
"""
from __future__ import annotations
import json
from datetime import datetime
from typing import Optional, List

from sqlalchemy.orm import Session

from app.db.models import User, Notebook, Source, Chunk, ChatMessage
from app.core.security import hash_password, verify_password


# ── Users ─────────────────────────────────────────────────────────────────────

def create_user(db: Session, email: str, password: str, full_name: Optional[str] = None) -> User:
    user = User(email=email, hashed_password=hash_password(password), full_name=full_name)
    db.add(user)
    db.flush()
    return user


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if user and verify_password(password, user.hashed_password):
        return user
    return None


# ── Notebooks ─────────────────────────────────────────────────────────────────

def create_notebook(db: Session, owner_id: str, title: str = "Untitled Notebook",
                    description: Optional[str] = None) -> Notebook:
    nb = Notebook(owner_id=owner_id, title=title, description=description)
    db.add(nb)
    db.flush()
    return nb


def get_notebooks(db: Session, owner_id: str) -> List[Notebook]:
    return db.query(Notebook).filter(Notebook.owner_id == owner_id).order_by(Notebook.updated_at.desc()).all()


def get_notebook(db: Session, notebook_id: str, owner_id: str) -> Optional[Notebook]:
    return db.query(Notebook).filter(
        Notebook.id == notebook_id, Notebook.owner_id == owner_id
    ).first()


def update_notebook(db: Session, notebook_id: str, owner_id: str,
                    title: Optional[str] = None, description: Optional[str] = None) -> Optional[Notebook]:
    nb = get_notebook(db, notebook_id, owner_id)
    if nb:
        if title is not None:
            nb.title = title
        if description is not None:
            nb.description = description
        nb.updated_at = datetime.utcnow()
        db.flush()
    return nb


def delete_notebook(db: Session, notebook_id: str, owner_id: str) -> bool:
    nb = get_notebook(db, notebook_id, owner_id)
    if nb:
        db.delete(nb)
        db.flush()
        return True
    return False


# ── Sources ───────────────────────────────────────────────────────────────────

def create_source(db: Session, notebook_id: str, title: str, source_type: str,
                  file_path: Optional[str] = None, original_url: Optional[str] = None) -> Source:
    src = Source(notebook_id=notebook_id, title=title, source_type=source_type,
                 file_path=file_path, original_url=original_url, status="pending")
    db.add(src)
    db.flush()
    return src


def get_sources(db: Session, notebook_id: str) -> List[Source]:
    return db.query(Source).filter(Source.notebook_id == notebook_id).order_by(Source.created_at).all()


def update_source_status(db: Session, source_id: str, status: str,
                         summary: Optional[str] = None) -> None:
    src = db.query(Source).filter(Source.id == source_id).first()
    if src:
        src.status = status
        if summary is not None:
            src.summary = summary
        db.flush()


# ── Chunks ────────────────────────────────────────────────────────────────────

def create_chunks(db: Session, source_id: str, chunks: List[dict]) -> List[Chunk]:
    """chunks: list of {content, chunk_index, page_number}"""
    objs = [
        Chunk(source_id=source_id, content=c["content"],
              chunk_index=c["chunk_index"], page_number=c.get("page_number"))
        for c in chunks
    ]
    db.add_all(objs)
    db.flush()
    return objs


def get_chunks_by_ids(db: Session, chunk_ids: List[str]) -> List[Chunk]:
    return db.query(Chunk).filter(Chunk.id.in_(chunk_ids)).all()


# ── Chat Messages ─────────────────────────────────────────────────────────────

def save_message(db: Session, notebook_id: str, role: str, content: str,
                 cited_chunk_ids: Optional[List[str]] = None) -> ChatMessage:
    msg = ChatMessage(
        notebook_id=notebook_id,
        role=role,
        content=content,
        cited_chunk_ids=json.dumps(cited_chunk_ids) if cited_chunk_ids else None,
    )
    db.add(msg)
    db.flush()
    return msg


def get_chat_history(db: Session, notebook_id: str) -> List[ChatMessage]:
    return db.query(ChatMessage).filter(
        ChatMessage.notebook_id == notebook_id
    ).order_by(ChatMessage.created_at).all()
