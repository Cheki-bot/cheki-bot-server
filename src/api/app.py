from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import ENV
from src.api.utils.auth import hash_password
from src.mongo import get_mongo_db
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

    @app.on_event("startup")
    def on_startup():
        db = get_mongo_db()
        users = db.get_collection("users")
        users.create_index("email", unique=True)
        if ENV.admin_email and ENV.admin_password:
            email = ENV.admin_email.lower()
            if not users.find_one({"_id": email}):
                users.insert_one({
                    "_id": email,
                    "email": email,
                    "full_name": "Administrator",
                    "role": "Admin",
                    "password_hash": hash_password(ENV.admin_password.get_secret_value()),
                    "is_active": True,
                })
    return app
