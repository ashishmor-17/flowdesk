from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .core.exceptions import http_exception_handler, unhandled_exception_handler

app= FastAPI()

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)