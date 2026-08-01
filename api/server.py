from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router
from config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()
    origins = settings.cors_origin_list
    use_wildcard = (not origins) or (origins == ["*"])

    app = FastAPI(
        title="HireSense AI Agent",
        description="LangGraph deep agent harness for resume screening",
        version="1.0.0",
    )

    if use_wildcard:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )
    else:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_origin_regex=r"https://.*\.vercel\.app",
            allow_credentials=False,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["*"],
        )

    app.include_router(router, prefix="/api/v1")

    @app.on_event("startup")
    async def log_cors_origins() -> None:
        mode = "wildcard(*)" if use_wildcard else f"list+vercel_regex:{origins}"
        print(f"[HireSense] CORS mode={mode}")

    return app


app = create_app()
