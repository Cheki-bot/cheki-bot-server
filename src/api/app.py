from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def create_app() -> FastAPI:
    app = FastAPI()

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():  # noqa: unused-argument
        return {"message": "Hello World"}

    @app.get("/checkhealth")
    async def check_health():  # noqa: unused-argument
        return {"status": "ok"}

    return app
