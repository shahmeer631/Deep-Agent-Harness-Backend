from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    origins = settings.cors_origin_list or [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    app = FastAPI(
        title="HireSense AI Agent",
        description="LangGraph deep agent harness for resume screening",
        version="1.0.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )
    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def log_cors_origins() -> None:
        print(f"[HireSense] CORS allow_origins={origins}")

    return app


app = create_app()
