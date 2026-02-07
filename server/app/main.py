from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from server.app.api.router import api_router
from server.app.core.logging import setup_logging
from shared.config import settings


def create_app() -> FastAPI:
    settings.validate_runtime()
    setup_logging()
    app = FastAPI(title="EASM Server", version="0.0.1")

    if settings.cors_enabled:
        allow_origins = settings.get_cors_allow_origins() or ["*"]
        app.add_middleware(
            CORSMiddleware,
            allow_origins=allow_origins,
            allow_credentials=settings.cors_allow_credentials and "*" not in allow_origins,
            allow_methods=settings.get_cors_allow_methods() or ["*"],
            allow_headers=settings.get_cors_allow_headers() or ["*"],
        )

    app.include_router(api_router)
    return app


app = create_app()
