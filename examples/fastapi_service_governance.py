"""Example: FastAPI service with governance middleware.

Demonstrates how to add governance middleware to a FastAPI application.
Requires: pip install aigov-shield[fastapi] uvicorn

Run with: uvicorn examples.fastapi_service_governance:app --reload
"""

from __future__ import annotations

from aigov_shield.prevention import PIIGuard, PrivilegeGuard, GuardAction
from aigov_shield.integrations import GovernanceMiddleware

try:
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
except ImportError:
    print("Install FastAPI: pip install aigov-shield[fastapi]")
    raise

app = FastAPI(title="Governed AI Service")

app.add_middleware(
    GovernanceMiddleware,
    guards=[
        PIIGuard(on_violation=GuardAction.BLOCK),
        PrivilegeGuard(on_violation=GuardAction.BLOCK),
    ],
    excluded_paths=["/health", "/docs", "/openapi.json"],
)


@app.get("/health")
async def health() -> dict:
    """Health check endpoint (excluded from governance)."""
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(payload: dict) -> dict:
    """Analyze text with governance checks applied via middleware."""
    text = payload.get("text", "")
    return {
        "analysis": f"Processed {len(text)} characters",
        "governance": "All checks passed",
    }
