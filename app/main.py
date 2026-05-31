import os
from typing import Any

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, Field

from app.moderator import check_text, load_rules, reload_rules

load_dotenv()

API_KEY = os.getenv("MODERATION_API_KEY", "").strip()

app = FastAPI(
    title="Forbidden Words API",
    description="Simple forbidden words detection API for JS/Python/Discord bots.",
    version="1.0.0",
)


class CheckRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)


class BulkCheckRequest(BaseModel):
    texts: list[str] = Field(..., min_length=1, max_length=100)


def require_api_key(x_api_key: str | None = Header(default=None)) -> None:
    if not API_KEY:
        return
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )


@app.get("/")
def root() -> dict[str, str]:
    return {
        "name": "Forbidden Words API",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health() -> dict[str, Any]:
    rules = load_rules()
    return {"ok": True, "rules": len(rules)}


@app.post("/v1/check", dependencies=[Depends(require_api_key)])
def check(payload: CheckRequest) -> dict[str, Any]:
    return check_text(payload.text)


@app.post("/v1/check/bulk", dependencies=[Depends(require_api_key)])
def check_bulk(payload: BulkCheckRequest) -> dict[str, Any]:
    results = [check_text(text) for text in payload.texts]
    return {
        "blocked": any(item["blocked"] for item in results),
        "results": results,
    }


@app.post("/v1/reload", dependencies=[Depends(require_api_key)])
def reload_word_rules() -> dict[str, Any]:
    reload_rules()
    rules = load_rules()
    return {"ok": True, "rules": len(rules)}
