from typing import Annotated

from fastapi import Depends
from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import VectorStore
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_nebius import ChatNebius, NebiusEmbeddings
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pymongo.database import Database as MongoDB

from src.agent.agent import AsyncAgent
from src.agent.commands import (
    AsyncClassifyTopic,
    AsyncRAGRetrieve,
    BuildCalendarContext,
    BuildCandidaciesContext,
    BuildCapabilitiesContext,
    BuildGovernmentPlansContext,
    BuildNewsVerificatiosContext,
    BuildQuestionsAndAnswersContext,
    BuildTopicContext,
    SearchElection,
)
from src.agent.schemas import Topic
from src.core.config import settings
from src.mongo import get_async_mongo_db
from src.mongo.consts import FILTERS


def get_chat_model():
    params = dict(
        model=settings.llm.model,
        api_key=settings.llm.api_key,
        temperature=settings.llm.temperature,
        max_completion_tokens=settings.llm.max_tokens,
    )
    match settings.llm.provider:
        case "openai":
            return ChatOpenAI(**params)
        case "nebius":
            return ChatNebius(**params)
        case _:
            raise NotImplementedError("Provider not supported")


def get_embedding_model():
    params = dict(
        model=settings.llm.emb_model,
        api_key=settings.llm.api_key,
    )
    match settings.llm.provider:
        case "openai":
            return OpenAIEmbeddings(**params)
        case "nebius":
            raise NebiusEmbeddings(**params)
        case _:
            raise NotImplementedError("Provider not supported")


def get_topic_selector() -> AsyncClassifyTopic:
    return AsyncClassifyTopic(
        model=ChatOpenAI(
            model="gpt-5-nano",
            reasoning={
                "effort": "minimal",
                "summary": None,
            },
            temperature=0.0,
            api_key=settings.llm.api_key,
        )
    )


def get_mongo_vdb(emb_model: "EmbeddingModelDep", db: "MongoDBDep") -> VectorStore:
    vector_db = MongoDBAtlasVectorSearch(
        collection=db.get_collection(settings.mongo.collection_name),
        embedding=emb_model,
        index_name=settings.mongo.index_name,
        relevance_score_fn="cosine",
    )
    vector_db.create_vector_search_index(settings.mongo.dimensions, FILTERS)
    return vector_db


def get_rag_engine(
    vector_db: Annotated[MongoDBAtlasVectorSearch, Depends(get_mongo_vdb)],
) -> AsyncRAGRetrieve:
    return AsyncRAGRetrieve(vector_db=vector_db)


def get_topic_prompt_builder(
    db: "MongoDBDep", vector_db: "VectorDBDep", search_election: "SearchElectionDep"
):
    build_topic_prompts = BuildTopicContext(
        {
            Topic.VERIFICATION_OF_NEWS: BuildNewsVerificatiosContext(vector_db),
            Topic.CANDIDACIES: BuildCandidaciesContext(db, search_election),
            Topic.GOVERNMENT_PROPOSALS: BuildGovernmentPlansContext(vector_db, search_election),
            Topic.ELECTORAL_CALENDAR: BuildCalendarContext(vector_db, search_election),
            Topic.QUESTIONS_AND_ANSWERS: BuildQuestionsAndAnswersContext(vector_db),
            Topic.CAPABILITIES: BuildCapabilitiesContext(),
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


def get_election_searcher(
    chat_model: "ChatModelDep",
    vector_db: "VectorDBDep",
) -> SearchElection:
    return SearchElection(chat_model, vector_db)


ChatModelDep = Annotated[BaseChatModel, Depends(get_chat_model)]
EmbeddingModelDep = Annotated[Embeddings, Depends(get_embedding_model)]
ClassifyTopicDep = Annotated[AsyncClassifyTopic, Depends(get_topic_selector)]
MongoDBDep = Annotated[MongoDB, Depends(get_async_mongo_db)]
VectorDBDep = Annotated[MongoDBAtlasVectorSearch, Depends(get_mongo_vdb)]
RAGRetrieveDep = Annotated[AsyncRAGRetrieve, Depends(get_rag_engine)]
BuildTopicPromptsDep = Annotated[BuildTopicContext, Depends(get_topic_prompt_builder)]
AgentDep = Annotated[AsyncAgent, Depends(get_agent)]
SearchElectionDep = Annotated[SearchElection, Depends(get_election_searcher)]
