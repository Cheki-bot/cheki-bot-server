import sys

sys.path.append(".")

from src.settings import Settings

settings = Settings(_env_file=".env")


print(settings.model_dump_json(indent=4))
