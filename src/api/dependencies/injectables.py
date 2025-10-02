from typing import Annotated

from fastapi import Depends
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_nebius import ChatNebius, NebiusEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pymongo.database import Database as MongoDB

from src import ENV
from src.agent.agent import AsyncAgent
from src.agent.commands import AsyncClassifyTopic, AsyncRAGRetrieve, AsyncSelectPrompt
from src.agent.context_manager import ContextManager
from src.agent.context_managers.mongo_cm import MongoContextManager
from src.db.mongo import get_mongo_db


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


def get_context_manager(emb_model: "EmbeddingModelDep") -> MongoContextManager:
    return MongoContextManager(emb_model)


def get_topic_selector(chat_model: "ChatModelDep") -> AsyncClassifyTopic:
    return AsyncClassifyTopic(chat_model)


def get_mongo_vdb(emb_model: "EmbeddingModelDep", db: "MongoDBDep") -> VectorStore:
    vector_db = MongoDBAtlasVectorSearch(
        collection=db.get_collection(ENV.mongo.collection_name),
        embedding=emb_model,
        index_name=ENV.mongo.index_name,
        relevance_score_fn="cosine",
    )
    vector_db.create_vector_search_index(ENV.mongo.dimensions, ["topic"])
    return vector_db


def get_rag_engine(vector_db: Annotated[MongoDBAtlasVectorSearch, Depends(get_mongo_vdb)]) -> AsyncRAGRetrieve:
    return AsyncRAGRetrieve(vector_db=vector_db)


def get_agent(
    chat_model: "ChatModelDep",
    classify_topic: "ClassifyTopicDep",
    rag_retrieve: "RAGRetrieveDep",
    select_prompt: "SelectPromptDep",
) -> AsyncAgent:
    return AsyncAgent(chat_model, classify_topic, rag_retrieve, select_prompt)


ChatModelDep = Annotated[BaseChatModel, Depends(get_chat_model)]
EmbeddingModelDep = Annotated[Embeddings, Depends(get_embedding_model)]
ClassifyTopicDep = Annotated[AsyncClassifyTopic, Depends(get_topic_selector)]
MongoDBDep = Annotated[MongoDB, Depends(get_mongo_db)]
ContextManagerDep = Annotated[ContextManager, Depends(get_context_manager)]
RAGRetrieveDep = Annotated[AsyncRAGRetrieve, Depends(get_rag_engine)]
SelectPromptDep = Annotated[AsyncSelectPrompt, Depends()]
AgentDep = Annotated[AsyncAgent, Depends(get_agent)]
