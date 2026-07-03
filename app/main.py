from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import http_exception_handler, unhandled_exception_handler
from app.api.v1.auth import router as auth_router
from app.api.v1.organizations import router as org_router
from app.api.v1.projects import router as projects_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.comments import router as comments_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.users import router as users_router


app= FastAPI()

app.include_router(auth_router, prefix="/api/v1")
app.include_router(org_router, prefix="/api/v1")
app.include_router(projects_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(comments_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
