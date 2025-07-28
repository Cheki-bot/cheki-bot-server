"""
This module contains the FastAPI application for the project.

It defines the main application instance and includes routes for the root endpoint and health check.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import ENV


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

    @app.get("/")
    async def root():  # noqa: unused-argument
        """
        Root endpoint that returns a simple "Hello World" message.

        Returns:
            dict: A dictionary with a "message" key containing the "Hello World" string.
        """
        return {"message": "Hello World"}

    @app.get("/checkhealth")
    async def check_health():  # noqa: unused-argument
        """
        Health check endpoint that returns the status of the application.

        Returns:
            dict: A dictionary with a "status" key indicating the health status.
        """
        return {"status": "ok"}

    return app
