import os

from .settings import Settings

_env_file = ".env"

match os.getenv("ENV"):
    case "prod":
        _env_file = "prod.env"
    case "dev":
        _env_file = "dev.env"
    case _:
        _env_file = ".env"


ENV = Settings(_env_file=_env_file)
