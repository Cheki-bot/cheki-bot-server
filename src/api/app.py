from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import ENV

from .routes import api


def create_app() -> FastAPI:
    """
    Creates and configures a FastAPI application instance.

    Returns:
        FastAPI: A configured FastAPI application instance.
    """
    app = FastAPI()
    app.title = "Checki API"  # type: ignore
    app.version = "0.1.0"
    app.description = "API for Checki bot"

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ENV.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api)
    return app
