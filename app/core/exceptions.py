from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def http_exception_handler(request: Request, exc: HTTPException):
    error_content = {
        "type": "HTTPException",
    }
    if isinstance(exc.detail, dict):
        error_content.update(exc.detail)
    else:
        error_content["message"] = exc.detail

    if exc.headers:
        error_content["details"] = exc.headers

    return JSONResponse(
        status_code=exc.status_code,
        content={"error": error_content},
    )

async def unhandled_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code= 500,
        content={
            "error":{
                "type": "InternalServerError",
                "message": "An unexpected error occurred.",
                "details": str(exc) if str(exc) else None
            }
        }
    )