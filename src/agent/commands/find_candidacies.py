from bson import ObjectId
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.interfaces.command import AsyncCommand
from src.mongo.models.candidacies_models import Candidacy


class FindCandidacies(AsyncCommand):
    def __init__(self, db: Database) -> None:
        self.__db = db

    def run(self, election_id: ObjectId) -> list[Candidacy]:
        candidacies = self.__db["candidacies"].find({"election_id": election_id})
        return TypeAdapter(list[Candidacy]).validate_python(candidacies)
