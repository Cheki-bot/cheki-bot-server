from bson import ObjectId
from langchain_mongodb import MongoDBAtlasVectorSearch
from pymongo.database import Database

from src.agent.commands.search_election import SearchElection
from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces.build_context import BuildContext
from src.agent.schemas import Topic, TopicSelection
from src.mongo.models.candidacies_models import Candidacy, Election


class BuildGovernmentPlansContext(BuildContext):
    def __init__(
        self, vector_db: MongoDBAtlasVectorSearch, search_election: SearchElection
    ) -> None:
        self.__vdb = vector_db
        self.__search_election = search_election

    @property
    def db(self) -> Database:
        return self.__vdb.collection.database

    @property
    def vdb(self) -> MongoDBAtlasVectorSearch:
        return self.__vdb

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
            election = Election.model_validate(
                self.db[Election.__collection_name__].find_one({}, {}, sort=[("_id", -1)])
            )

        candidate = topic_selection.params.get("candidate")

        if not election:
            msg = "No se encontraron elecciones relacionadas a su solicitud"
            context_builder.add_not_found_messages(msg)
            return context_builder

        if not candidate:
            msg = (
                "Por favor especifique el candidato "
                "del cual necesita saber los planes gubernamentales."
            )
            context_builder.add_not_found_messages(msg)

        search_kwargs = {
            "k": 1,
            "score_threshold": 0.5,
            "pre_filter": {
                "topic": Topic.CANDIDACIES.value,
                "election_id": election.id,
            },
        }
        retriever = self.vdb.as_retriever(
            search_kwargs=search_kwargs,
            search_type="similarity_score_threshold",
        )
        docs = await retriever.ainvoke(str(candidate))
        if not docs or len(docs) < 1:
            msg = (
                "No se encontró los candidatos solicitados para saber sus planes de gobierno. "
                "Por favor especifique el candidato y/o la elección específica."
            )
            context_builder.add_not_found_messages(msg)
            return context_builder

        collection = self.db[Candidacy.__collection_name__]
        candidacy = Candidacy.model_validate(
            collection.find_one({"_id": ObjectId(docs[0].metadata["data_id"])})
        )

        search_kwargs = {
            "k": 10,
            "pre_filter": {
                "topic": Topic.GOVERNMENT_PROPOSALS.value,
                "data_id": candidacy.id,
            },
        }
        retriever = self.vdb.as_retriever(search_kwargs=search_kwargs)
        docs = await retriever.ainvoke(topic_selection.optimized_query)
        content = "\n\n".join([doc.page_content for doc in docs])
        candidacy.government_plan = content

        context_builder.add_candidacies([candidacy], include_gov_plan=True)

        return context_builder
