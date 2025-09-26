from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src.agents.context_managers.mongo_cm import MongoContextManager

from .. import ENV
from ..core.agent import Agent


class OpenAIAgent(Agent):
    def __init__(self):
        super().__init__(
            chat_model=ChatOpenAI(
                model=ENV.llm.model,
                api_key=ENV.llm.api_key,
                temperature=ENV.llm.temperature,
                max_completion_tokens=ENV.llm.max_tokens,
            ),
            context_manager=MongoContextManager(
                emb_model=OpenAIEmbeddings(
                    model=ENV.llm.emb_model,
                    api_key=ENV.llm.api_key,
                )
            ),
        )
