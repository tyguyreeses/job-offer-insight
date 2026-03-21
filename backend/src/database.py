from __future__ import annotations

import os
from collections.abc import Callable, Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, SQLModel, create_engine

DEFAULT_DB_URL = "sqlite:///./data/job_offer_insight.db"


def create_engine_from_settings(database_url: str, *, echo: bool = False) -> Engine:
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, echo=echo, connect_args=connect_args)


def create_db_and_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(engine)


def make_session_dependency(engine: Engine) -> Callable[[], Generator[Session, None, None]]:
    def _get_session() -> Generator[Session, None, None]:
        with Session(engine) as session:
            yield session

    return _get_session


_default_engine = create_engine_from_settings(os.getenv("DATABASE_URL", DEFAULT_DB_URL))
get_session = make_session_dependency(_default_engine)
