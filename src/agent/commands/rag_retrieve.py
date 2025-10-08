from langchain_core.documents import Document
from langchain_mongodb.vectorstores import MongoDBAtlasVectorSearch

from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import Topic


class AsyncRAGRetrieve(AsyncCommand):
    def __init__(self, vector_db: MongoDBAtlasVectorSearch) -> None:
        self.__db = vector_db.collection.database
        self.__vec_db = vector_db

    @property
    def db(self):
        return self.__db

    @property
    def vec_db(self):
        return self.__vec_db

    async def run(self, topic_name: Topic, query: str, k: int = 5) -> list[Document]:
        filter_args = {}
        if topic_name is not Topic.GENERAL_INFO:
            filter_args = {"pre_filter": {"topic": topic_name.value}}
        retriever = self.vec_db.as_retriever(search_kwargs={"k": k, **filter_args})
        documents = await retriever.ainvoke(query)
        return documents

    async def __call__(self, topic_name: Topic, query: str, k: int = 5) -> list[Document]:
        return await super().__call__(topic_name, query, k)
