from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from app import settings

_engine = create_engine(settings.POSTGRES_CONNECTION_STRING)
_session_local = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

Base = declarative_base()


def get_db():
    db = _session_local()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()
