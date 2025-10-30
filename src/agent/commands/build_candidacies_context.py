from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.commands.search_election import SearchElection
from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces import BuildContext
from src.agent.schemas import TopicSelection
from src.mongo.models.candidacies_models import Candidacy


class BuildCandidaciesContext(BuildContext):
    def __init__(self, db: Database, search_election: SearchElection) -> None:
        self.__db = db
        self.__search_election = search_election

    @property
    def db(self) -> Database:
        return self.__db

    @property
    def search_election(self) -> SearchElection:
        return self.__search_election

    async def run(
        self,
        topic_selection: TopicSelection,
        context_builder: ContextBuilder,
    ) -> ContextBuilder:
        election = await self.search_election(topic_selection)
        if not election:
            msg = (
                "No se encontró la elección solicitada, "
                "por favor especifique las elecciones "
                "de las cuales necesita saber los candidatos."
            )
            context_builder.add_not_found_messages(msg)

            return context_builder

        candidacies = TypeAdapter(list[Candidacy]).validate_python(
            self.db["candidacies"].find({"election_id": election.id})
        )
        context_builder.set_election(election)
        context_builder.add_candidacies(candidacies)

        return context_builder

    async def __call__(
        self,
        topic_selection: TopicSelection,
        context_builder: ContextBuilder,
    ) -> ContextBuilder:
        return await self.run(topic_selection, context_builder)
