import os
from contextlib import contextmanager

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

load_dotenv()

_engine = None
_session = None


def _build_url() -> str:
    """Monta a URL de conexão com o banco de dados a partir das variáveis de ambiente."""
    return (
        f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}"
        f"@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT', 5432)}/{os.getenv('DB_NAME')}"
    )


def get_engine():
    """Retorna a instância singleton do engine SQLAlchemy."""
    global _engine
    if _engine is None:
        _engine = create_engine(_build_url(), pool_pre_ping=True)
    return _engine


def get_session_factory():
    """Retorna a factory de sessões SQLAlchemy (singleton)."""
    global _session
    if _session is None:
        _session = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _session


@contextmanager
def get_session() -> Session:
    """Context manager que fornece uma sessão de banco de dados com rollback automático em caso de erro."""
    factory = get_session_factory()
    session = factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
