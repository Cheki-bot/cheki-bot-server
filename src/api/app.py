"""
This module contains the FastAPI application for the project.

It defines the main application instance and includes routes for the root endpoint and health check.
"""

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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=ENV.allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api)

    return app
