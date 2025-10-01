from typing import Optional

from langchain_core.documents import Document
from langchain_core.vectorstores import VectorStore

from src.agent.interfaces.command import AsyncCommand
from src.agent.schemas import TopicSelection


class AsyncRAGRetrieve(AsyncCommand):
    def __init__(self, vector_db: VectorStore, db_engine: Optional[str] = None) -> None:
        self.__vec_db = vector_db
        self.__filter_field = "pre_filter" if db_engine is not None and db_engine == "mongo" else "filter"

    async def run(self, topic_selection: TopicSelection) -> list[Document]:
        # Obtener documentos para el tema principal
        main_documents = await self.__retrieve(topic_selection.topic.name, topic_selection.optimized_query, k=5)

        # Obtener documentos para temas adicionales
        additional_documents = []
        for additional_topic in topic_selection.additional_topics:
            docs = await self.__retrieve(additional_topic.name, additional_topic, k=2)
            additional_documents.extend(docs)

        return main_documents + additional_documents

    async def __retrieve(self, topic_name: str, query: str, k: int) -> list[Document]:
        """Obtiene documentos para un tema específico."""
        filter_ = {self.__filter_field: {"topic": topic_name}}
        retriever = self.__vec_db.as_retriever(search_kwargs={"k": k, **filter_})
        return await retriever.ainvoke(query)

    async def __call__(self, *args, **kwargs) -> list[Document]:
        return await super().__call__(*args, **kwargs)
