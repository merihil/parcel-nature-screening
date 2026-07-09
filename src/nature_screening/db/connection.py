from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from nature_screening.config import settings


def get_engine() -> Engine:
    return create_engine(settings.database_url)
