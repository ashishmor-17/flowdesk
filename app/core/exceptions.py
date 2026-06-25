from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error":{
                "type": "HTTPException",
                "message": exc.detail,
                "details": exc.headers if exc.headers else None
            }
        },
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