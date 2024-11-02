from typing import Generator
from sqlmodel import Session, SQLModel, create_engine

DATABASE_URL = "sqlite:///./perfumes.db"
engine = create_engine(DATABASE_URL, echo=True)


def init_db():
    """Create all tables in the database"""
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    with Session(engine) as session:
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
