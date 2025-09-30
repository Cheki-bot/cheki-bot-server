from typing import Annotated

from fastapi import Depends
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_nebius import ChatNebius, NebiusEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from src import ENV
from src.agent.agent import Agent
from src.agent.context_manager import ContextManager
from src.agent.context_managers.mongo_cm import MongoContextManager
from src.agent.topic_detector import TopicSelector


def get_chat_model():
    params = dict(
        model=ENV.llm.model,
        api_key=ENV.llm.api_key,
        temperature=ENV.llm.temperature,
        max_completion_tokens=ENV.llm.max_tokens,
    )
    match ENV.llm.provider:
        case "openai":
            return ChatOpenAI(**params)
        case "nebius":
            return ChatNebius(**params)
        case _:
            raise NotImplementedError("Provider not supported")


def get_embedding_model():
    params = dict(
        model=ENV.llm.emb_model,
        api_key=ENV.llm.api_key,
    )
    match ENV.llm.provider:
        case "openai":
            return OpenAIEmbeddings(**params)
        case "nebius":
            raise NebiusEmbeddings(**params)
        case _:
            raise NotImplementedError("Provider not supported")


def get_context_manager(emb_model: "EmbeddingModelDep"):
    return MongoContextManager(emb_model)


def get_agent(chat_model: "ChatModelDep", context_manager: "ContextManagerDep") -> Agent:
    return Agent(chat_model, context_manager)


def get_topic_selector(chat_model: "ChatModelDep"):
    return TopicSelector(chat_model)


ChatModelDep = Annotated[BaseChatModel, Depends(get_chat_model)]
EmbeddingModelDep = Annotated[Embeddings, Depends(get_embedding_model)]
ContextManagerDep = Annotated[ContextManager, Depends(get_context_manager)]
TopicSelectorDep = Annotated[TopicSelector, Depends(get_topic_selector)]
AgentDep = Annotated[Agent, Depends(get_agent)]
