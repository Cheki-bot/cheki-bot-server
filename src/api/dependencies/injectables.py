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
from src.agent.commands import (
    AsyncClassifyTopic,
    AsyncRAGRetrieve,
    BuildCandidaciesPrompt,
    BuildGenericPrompt,
    BuildNewsVerificatiosPrompt,
    BuildTopicPrompts,
)
from src.agent.schemas import Topic
from src.mongo import get_async_mongo_db


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


def get_topic_selector() -> AsyncClassifyTopic:
    return AsyncClassifyTopic(
        model=ChatOpenAI(
            model="gpt-4.1-nano",
            temperature=0.1,
            api_key=ENV.llm.api_key,
        )
    )


def get_mongo_vdb(emb_model: "EmbeddingModelDep", db: "MongoDBDep") -> VectorStore:
    vector_db = MongoDBAtlasVectorSearch(
        collection=db.get_collection(ENV.mongo.collection_name),
        embedding=emb_model,
        index_name=ENV.mongo.index_name,
        relevance_score_fn="cosine",
    )
    vector_db.create_vector_search_index(
        ENV.mongo.dimensions, ["type", "collection_name", "topic", "data_id"]
    )
    return vector_db


def get_rag_engine(
    vector_db: Annotated[MongoDBAtlasVectorSearch, Depends(get_mongo_vdb)],
) -> AsyncRAGRetrieve:
    return AsyncRAGRetrieve(vector_db=vector_db)


def get_topic_prompt_builder(db: "MongoDBDep"):
    build_topic_prompts = BuildTopicPrompts(
        {
            Topic.VERIFICATION_OF_NEWS: BuildNewsVerificatiosPrompt(db),
            Topic.CANDIDATES: BuildCandidaciesPrompt(db),
            Topic.GOVERNMENT_PROPOSALS: BuildGenericPrompt(),
            Topic.ELECTORAL_CALENDAR: BuildGenericPrompt(),
            Topic.QUESTIONS_AND_ANSWERS: BuildGenericPrompt(),
            Topic.CAPABILITIES: BuildGenericPrompt(),
        }
    )
    return build_topic_prompts


def get_agent(
    chat_model: "ChatModelDep",
    classify_topic: "ClassifyTopicDep",
    rag_retrieve: "RAGRetrieveDep",
    build_topic_prompts: "BuildTopicPromptsDep",
) -> AsyncAgent:
    return AsyncAgent(
        chat_model,
        classify_topic,
        rag_retrieve,
        build_topic_prompts,
    )


ChatModelDep = Annotated[BaseChatModel, Depends(get_chat_model)]
EmbeddingModelDep = Annotated[Embeddings, Depends(get_embedding_model)]
ClassifyTopicDep = Annotated[AsyncClassifyTopic, Depends(get_topic_selector)]
MongoDBDep = Annotated[MongoDB, Depends(get_async_mongo_db)]
RAGRetrieveDep = Annotated[AsyncRAGRetrieve, Depends(get_rag_engine)]
BuildTopicPromptsDep = Annotated[BuildTopicPrompts, Depends(get_topic_prompt_builder)]
AgentDep = Annotated[AsyncAgent, Depends(get_agent)]
