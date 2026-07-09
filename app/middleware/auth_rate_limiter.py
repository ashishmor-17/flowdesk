from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.middleware.rate_limit import allow_request

from app.core.config import get_settings
settings = get_settings()


RATE_LIMIT_RULES = {
    "/api/v1/auth/login": {
        "capacity": 5,
        "refill_rate": 5 / 60,
        "name": "login"
    },
    "/api/v1/auth/signup": {
        "capacity": 3,
        "refill_rate": 3 / 60,
        "name": "signup"
    }
}


class AuthRateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next
    ):
        if not settings.RATE_LIMIT_ENABLED:
            return await call_next(request)
        rule = RATE_LIMIT_RULES.get(
            request.url.path
        )
        if rule and request.method == "POST":
            client_ip = request.client.host
            key = (
                f"token_bucket:"
                f"{rule['name']}:"
                f"{client_ip}"
            )
            allowed, remaining = await allow_request(
                key=key,
                capacity=rule["capacity"],
                refill_rate=rule["refill_rate"]
            )
            if not allowed:
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests"
                        }
                    },
                    headers={
                        "Retry-After": "60"
                    }
                )

        return await call_next(request)