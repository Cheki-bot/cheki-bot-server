from datetime import UTC, datetime, timedelta, timezone
from typing import Sequence

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
)
from langchain_mongodb import MongoDBAtlasVectorSearch

from src import ENV
from src.agent.context_managers.chroma_cm import ChromaContextManager
from src.agent.schemas import DocType

from .prompts import (
    CALENDAR_EVENT_PROMPT,
    CALENDAR_METADATA_PROMPT,
    CANDIDATES_PROMPT,
    CHAT_SYSTEM_PROMPT,
    GOV_PROGRAM_PROMPT,
    NOT_FOUND_PROMPT,
    Q_A_PROMPT,
    VERIFICATION_PROMPT,
    VERIFICATION_TEMPLATE,
    VERIFICATION_TEMPLATE_DEFAULT,
)


class MongoContextManager(ChromaContextManager):
    def __init__(self, emb_model: Embeddings) -> None:
        self.vectorDB = MongoDBAtlasVectorSearch.from_connection_string(
            connection_string=ENV.mongo.uri,
            db_name=ENV.mongo.db_name,
            collection_name=ENV.mongo.collection_name,
            embedding=emb_model,
            index_name=ENV.mongo.index_name,
            relevance_score_fn="cosine",
            namespace=f"{ENV.mongo.db_name}.{ENV.mongo.collection_name}",
        )
        self.vectorDB.create_vector_search_index(ENV.mongo.dimensions, ["type"])
        self.node: list = []

    def __format_verification(self, documents: list[Document]):
        content = []
        for document in documents:
            data = VERIFICATION_TEMPLATE_DEFAULT.copy()
            data.update({**document.metadata, "body": document.page_content})
            content.append(VERIFICATION_TEMPLATE.format(**data))
        return VERIFICATION_PROMPT.format(content="\n".join(content))

    def __format_content(self, documents: list[Document]):
        content = []
        for document in documents:
            content.append(document.page_content)
        return "\n\n".join(content)

    async def build_system_messages(
        self, queries: Sequence[BaseMessage]
    ) -> Sequence[SystemMessage]:
        """Build a system message with contextual information from the vector database.

        Args:
            query: The user's query string to search for relevant documents.

        Returns:
            A SystemMessage containing the formatted context from the database.
        """

        relevant_docs: list[tuple[Document, float]] = []
        complete_context = ""
        focus = 1.0
        for query in queries[::-1]:
            query_str = str(query.content).lower()
            scores = await self.vectorDB.asimilarity_search_with_relevance_scores(
                query_str,
                k=3,
                score_threshold=0.1,
            )
            relevant_docs = [(doc, score * focus) for doc, score in scores]
            complete_context += f"{query_str} "
            focus *= 0.5
        relevant_docs += await self.vectorDB.asimilarity_search_with_relevance_scores(
            complete_context,
            k=3,
            score_threshold=0.1,
        )

        content_type = {}  # type: ignore
        for doc, score in relevant_docs:
            _type = doc.metadata.get("type")
            if _type not in content_type:
                content_type[_type] = []
            content_type[_type].append(score)

        # Calculate median instead of average
        for _type in content_type:
            content_type[_type] = sorted(content_type[_type])[len(content_type[_type]) // 2]

        best_match = ""
        if content_type:
            best_match = str(max(content_type, key=lambda key: content_type.get(key, 0)))

        current_date = datetime.now(UTC)
        date_str = current_date.astimezone(
            timezone(offset=timedelta(hours=-4), name="America/La_Paz")
        ).strftime("%d de %B del %Y")

        system_prompts = [SystemMessage(content=CHAT_SYSTEM_PROMPT.format(date=date_str))]

        match best_match:
            case DocType.VERIFICATIONS.value:
                retriver = self.vectorDB.as_retriever(
                    search_kwargs={"k": 10, "pre_filter": {"type": best_match}}
                )
                documents = await retriver.ainvoke(complete_context)
                content = self.__format_verification(documents)
                system_prompts.append(SystemMessage(content))

            case DocType.GOV_PROGRAMS.value:
                retriver = self.vectorDB.as_retriever(
                    search_kwargs={"k": 20, "pre_filter": {"type": best_match}}
                )
                documents = await retriver.ainvoke(complete_context)
                content = self.__format_content(documents)
                content = GOV_PROGRAM_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CALENDAR_META.value:
                retriver = self.vectorDB.as_retriever(
                    search_kwargs={"k": 20, "pre_filter": {"type": best_match}}
                )
                documents = await retriver.ainvoke(complete_context)
                content = self.__format_content(documents)
                content = CALENDAR_METADATA_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CALENDAR.value:
                retriver = self.vectorDB.as_retriever(
                    search_kwargs={"k": 20, "pre_filter": {"type": best_match}}
                )
                documents = await retriver.ainvoke(complete_context)
                content = self.__format_content(documents)
                content = CALENDAR_EVENT_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.CANDIDATES.value:
                retriver = self.vectorDB.as_retriever(
                    search_kwargs={"k": 20, "pre_filter": {"type": best_match}}
                )
                documents = await retriver.ainvoke(complete_context)
                content = ""
                for doc in documents:
                    content += doc.page_content + "\n"
                    content += doc.metadata["candidates"] + "\n"
                    content += "Resumen de propuestas\n" + doc.metadata["summaries"]
                content = CANDIDATES_PROMPT.format(content=content)
                system_prompts.append(SystemMessage(content))

            case DocType.Q_A.value:
                retriver = self.vectorDB.as_retriever(
                    search_type="similarity_score_threshold",
                    search_kwargs={
                        "score_threshold": 0.1,
                        "k": 1,
                        "pre_filter": {"type": best_match},
                    },
                )
                query = queries[-1]
                query_str = str(query.content) if len(queries) > 0 else ""  # type: ignore
                query_str = query_str.strip().lower()
                documents = await retriver.ainvoke(query_str)
                content = ""
                for doc in documents:
                    content = (
                        f"Question: {doc.page_content}\nAnswer: {doc.metadata.get('answer', '')}\n"
                    )

                content = Q_A_PROMPT.format(question="query", content=content.strip())
                system_prompts.append(SystemMessage(content))

            case _:
                system_prompts.append(SystemMessage(NOT_FOUND_PROMPT))

        return system_prompts
