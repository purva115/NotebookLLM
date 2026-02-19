"""
init_db.py — Create all SQLite tables at startup.
Called once from app.py before the Gradio app launches.
"""
from app.db.session import engine
from app.db.models import Base


def init_db() -> None:
    """Create all tables defined in models.py if they don't already exist."""
    Base.metadata.create_all(bind=engine)
    print("[DB] SQLite tables initialised.")
