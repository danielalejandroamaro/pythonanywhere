import functools

import pydantic
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import MetaData

from config import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

SQLALCHEMY_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
print(f'QLALCHEMY_DATABASE_URL:\n{QLALCHEMY_DATABASE_URL}\n')


def _custom_json_serializer(*args, **kwargs) -> str:
    """
    Encodes json in the same way that pydantic does.
    """
    return json.dumps(*args, default=pydantic.json.pydantic_encoder, **kwargs)


def _create_engine(url, **kwargs):
    if not database_exists(url):
        create_database(url)
    return create_engine(
        url,
        server_side_cursors=True,
        # echo=is_debug,
        # connect_args={"check_same_thread": False}, # posgre, mysql invalid params
        json_serializer=_custom_json_serializer,
        **kwargs
    )


engine = _create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
metadata_obj = MetaData()
metadata_obj.reflect(
    bind=engine,
    views=True
)


def set_session(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        with Session(engine, expire_on_commit=False) as _session:
            try:
                result = func(*args, **kwargs, session=_session)
                _session.commit()
            finally:
                pass
        return result

    return decorator


def set_connection(func):
    @functools.wraps(func)
    def decorator(*args, **kwargs):
        if conn := kwargs.pop('conn', None):
            return func(*args, **kwargs, conn=conn)
        else:
            with engine.connect() as conn:
                result = func(*args, **kwargs, conn=conn)
            return result

    return decorator
