from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
import sys
from pathlib import Path

# Reuse backend engine: repo root + backend dir on path so backend.db and core.logger resolve
_repo_root = Path(__file__).resolve().parents[1]
_backend_dir = _repo_root / "backend"
for _p in (_backend_dir, _repo_root):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)
from backend.db import engine



def get_tables():
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to fetch tables: {str(e)}")


def get_columns(table_name: str):
    try:
        inspector = inspect(engine)
        return inspector.get_columns(table_name)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to fetch columns for {table_name}: {str(e)}")


def get_foreign_keys(table_name: str):
    try:
        inspector = inspect(engine)
        return inspector.get_foreign_keys(table_name)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to fetch foreign keys for {table_name}: {str(e)}")


def get_indexes(table_name: str):
    try:
        inspector = inspect(engine)
        return inspector.get_indexes(table_name)
    except SQLAlchemyError as e:
        raise RuntimeError(f"Failed to fetch indexes for {table_name}: {str(e)}")