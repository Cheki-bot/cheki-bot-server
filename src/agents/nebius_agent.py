from langchain_nebius import ChatNebius, NebiusEmbeddings

from src import ENV
from src.core.agent import Agent

from .context_managers.chroma_cm import ChromaContextManager


class NebiusAgent(Agent):
    def __init__(self):
        super().__init__(
            chat_model=ChatNebius(
                model=ENV.llm.model,
                api_key=ENV.llm.api_key,
                temperature=ENV.llm.temperature,
                max_tokens=ENV.llm.max_tokens,
            ),
            context_manager=ChromaContextManager(
                emb_model=NebiusEmbeddings(
                    model=ENV.llm.emb_model,
                    api_key=ENV.llm.api_key,
                )
            ),
        )
