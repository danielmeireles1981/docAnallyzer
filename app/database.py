from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite+aiosqlite:///./docanallyzer.db"

engine = create_async_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

# Sessão SÍNCRONA (usada no reindex.py)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker as SyncSessionMaker

sync_engine = create_engine("sqlite:///./docanallyzer.db", connect_args={"check_same_thread": False})
SyncSessionLocal = SyncSessionMaker(bind=sync_engine)
