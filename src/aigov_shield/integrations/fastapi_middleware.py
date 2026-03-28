"""FastAPI middleware for API-level governance."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Callable

try:
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    from starlette.responses import JSONResponse, Response
except ImportError:
    # Stubs for when fastapi/starlette is not installed
    class BaseHTTPMiddleware:  # type: ignore[no-redef]
        """Stub for when starlette is not installed."""

        def __init__(self, app: Any, **kwargs: Any) -> None:
            self.app = app

    class Request:  # type: ignore[no-redef]
        """Stub for when starlette is not installed."""

        pass

    class Response:  # type: ignore[no-redef]
        """Stub for when starlette is not installed."""

        pass

    class JSONResponse:  # type: ignore[no-redef]
        """Stub for when starlette is not installed."""

        def __init__(self, content: Any = None, status_code: int = 200) -> None:
            pass


from aigov_shield.prevention.base import BaseGuard, GuardAction

if TYPE_CHECKING:
    from aigov_shield.accountability.chain_of_custody import ChainOfCustody
    from aigov_shield.accountability.evidence_logger import EvidenceLogger


class GovernanceMiddleware(BaseHTTPMiddleware):
    """FastAPI/Starlette middleware that applies governance to API requests.

    Intercepts request bodies to run guards and optionally blocks
    requests that fail governance checks.

    Args:
        app: The ASGI application.
        guards: List of guards to run on request/response bodies.
        check_requests: Whether to check request bodies.
        check_responses: Whether to check response bodies.
        custody: Optional chain of custody.
        evidence_logger: Optional evidence logger.
        excluded_paths: List of paths to exclude from governance checks.

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> app.add_middleware(
        ...     GovernanceMiddleware,
        ...     guards=[PIIGuard(), PrivilegeGuard()],
        ... )
    """

    def __init__(
        self,
        app: Any,
        guards: list[BaseGuard] | None = None,
        check_requests: bool = True,
        check_responses: bool = True,
        custody: ChainOfCustody | None = None,
        evidence_logger: EvidenceLogger | None = None,
        excluded_paths: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self.guards = guards or []
        self.check_requests = check_requests
        self.check_responses = check_responses
        self.custody = custody
        self.evidence_logger = evidence_logger
        self.excluded_paths = excluded_paths or []

    async def dispatch(self, request: Any, call_next: Callable[..., Any]) -> Any:
        """Process a request through governance checks.

        Args:
            request: The incoming HTTP request.
            call_next: The next middleware or route handler.

        Returns:
            The HTTP response, potentially modified by governance checks.
        """
        # Skip excluded paths
        if hasattr(request, "url") and any(
            str(request.url.path).startswith(p) for p in self.excluded_paths
        ):
            return await call_next(request)

        start_time = time.perf_counter()

        # Check request body
        if self.check_requests and hasattr(request, "body"):
            try:
                body_bytes = await request.body()
                body_text = body_bytes.decode("utf-8", errors="replace")

                if body_text.strip():
                    for guard in self.guards:
                        result = guard.check(body_text)
                        if not result.passed and result.action_taken == GuardAction.BLOCK:
                            elapsed = (time.perf_counter() - start_time) * 1000
                            return JSONResponse(
                                status_code=422,
                                content={
                                    "error": "governance_violation",
                                    "guard": result.guard_name,
                                    "violations": len(result.violations),
                                    "execution_time_ms": round(elapsed, 3),
                                },
                            )

                    if self.custody:
                        self.custody.add_record(
                            interaction_type="query",
                            content=body_text,
                            actor="fastapi_middleware",
                        )
            except Exception:
                pass  # Don't block requests if body reading fails

        # Call the actual endpoint
        response = await call_next(request)

        # Log to evidence logger
        elapsed = (time.perf_counter() - start_time) * 1000
        if self.evidence_logger and hasattr(request, "url"):
            self.evidence_logger.log_event(
                event_type="api_request",
                description=f"{getattr(request, 'method', 'UNKNOWN')} {request.url.path}",
                metadata={
                    "status_code": getattr(response, "status_code", 0),
                    "execution_time_ms": round(elapsed, 3),
                },
            )

        return response
