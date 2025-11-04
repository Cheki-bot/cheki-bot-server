from bson import ObjectId
from langchain_mongodb import MongoDBAtlasVectorSearch
from pydantic import TypeAdapter

from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces.build_context import BuildContext
from src.agent.schemas import TopicSelection
from src.mongo.models.qa_model import QuestionsAndAnswers


class BuildQuestionsAndAnswersContext(BuildContext):
    def __init__(self, vector_db: MongoDBAtlasVectorSearch) -> None:
        self.__vec_db = vector_db

    @property
    def vec_db(self) -> MongoDBAtlasVectorSearch:
        return self.__vec_db

    @property
    def db(self):
        return self.vec_db.collection.database

    async def run(self, topic_selection: TopicSelection, context_builder: ContextBuilder):
        collection = self.db.get_collection(QuestionsAndAnswers.__collection_name__)
        search_kwargs = {
            "k": 10,
            "pre_filter": {
                "topic": topic_selection.topic.value,
                "collection_name": QuestionsAndAnswers.__collection_name__,
            },
        }
        retriever = self.vec_db.as_retriever(search_kwargs=search_kwargs)
        docs = await retriever.ainvoke(topic_selection.optimized_query)
        ids = {
            ObjectId(doc.metadata.get("data_id"))
            for doc in docs
            if doc.metadata.get("data_id") is not None
        }
        filters: dict = {"_id": {"$in": list(ids)}}
        qas = TypeAdapter(list[QuestionsAndAnswers]).validate_python(collection.find(filters))

        context_builder.add_questions_and_answers(qas)

        return context_builder
