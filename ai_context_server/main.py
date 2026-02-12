from fastapi import FastAPI, Query, HTTPException

from filesystem import list_files, read_file
from search import search_code
from git_tools import git_log, git_show

from db_schema import (
    get_tables,
    get_columns,
    get_foreign_keys,
    get_indexes,
)


app = FastAPI(title="AI Context Bridge")


# ---------------- FILESYSTEM ----------------

@app.get("/files")
def files(path: str = ""):
    try:
        return list_files(path)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/file")
def file(path: str = Query(...)):
    try:
        return {"content": read_file(path)}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/search")
def search(q: str):
    return search_code(q)


# ---------------- GIT ----------------

@app.get("/git/log")
def git_history(limit: int = 20):
    try:
        return git_log(limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/git/show")
def git_commit(commit: str):
    try:
        return git_show(commit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ---------------- DATABASE SCHEMA ----------------

@app.get("/db/tables")
def db_tables():
    try:
        return get_tables()
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/db/columns")
def db_columns(table: str):
    try:
        return get_columns(table)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/db/foreign-keys")
def db_foreign_keys(table: str):
    try:
        return get_foreign_keys(table)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/db/indexes")
def db_indexes(table: str):
    try:
        return get_indexes(table)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))