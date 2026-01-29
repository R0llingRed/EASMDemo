from fastapi import FastAPI

from server.app.api.router import api_router
from server.app.core.logging import setup_logging


def create_app() -> FastAPI:
    setup_logging()
    app = FastAPI(title="EASM Server", version="0.0.1")
    app.include_router(api_router)
    return app


app = create_app()
