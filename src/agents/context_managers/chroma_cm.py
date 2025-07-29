import tiktoken
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    SystemMessage,
    trim_messages,
)

from src import ENV

from ...core.entities.context_manager import ContextManager
from .prompts import CHAT_SYSTEM_PROMPT


class ChromaContextManager(ContextManager):
    def __init__(self, emb_model: Embeddings) -> None:
        self.vectorDB = Chroma(
            persist_directory=ENV.chroma.persist_directory,
            embedding_function=emb_model,
        )

    async def retrieve_context(self, query, history):
        system_message = await self.build_system_message(query)
        query_message = HumanMessage(content=query)
        messages = [system_message] + history.messages + [query_message]
        return await self.trim_context(messages)

    async def build_system_message(self, query: str):
        retriver = self.vectorDB.as_retriever(search_kwargs={"k": 3})
        docs = await retriver.ainvoke(query)
        context_text = "\n\n".join([doc.page_content for doc in docs])
        chat_system_prompt = CHAT_SYSTEM_PROMPT.format(context=context_text)
        return SystemMessage(content=chat_system_prompt)

    async def trim_context(self, context):
        encoding = tiktoken.encoding_for_model("gpt-4-nano")

        def count_tokens_openai(message_list: list[BaseMessage]):
            return sum(
                len(encoding.encode(str(msg.content)))
                for msg in message_list
                if hasattr(msg, "content")
            )

        return trim_messages(
            context,
            token_counter=count_tokens_openai,
            max_tokens=ENV.llm.max_tokens,
            strategy="last",
            start_on="human",
            end_on=("human", "tool"),
            include_system=True,
        )
