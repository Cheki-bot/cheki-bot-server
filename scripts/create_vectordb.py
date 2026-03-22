import tiktoken
from bson import ObjectId
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import MarkdownHeaderTextSplitter
from pydantic import TypeAdapter

from src.agent.schemas import Topic
from src.core.config import settings
from src.core.tools import sanitize_text_input
from src.mongo import get_mongo_db
from src.mongo.consts import FILTERS
from src.mongo.models import (
    CalendarEvent,
    Candidacy,
    Election,
    ElectoralCalendar,
    NewsVerification,
    QuestionsAndAnswers,
)

folder = "base_file"
file_path = f"{folder}/{settings.google.data_filename}"

embedding = OpenAIEmbeddings(
    model=settings.llm.emb_model,
    api_key=settings.llm.api_key,
)

encoding = tiktoken.encoding_for_model("text-embedding-3-small")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=800,
    chunk_overlap=100,
    length_function=lambda text: len(encoding.encode(text)),
    separators=["\n\n", "\n", ". ", " ", ""],
)


def load_verifications():
    db = get_mongo_db()
    collection = db.get_collection(NewsVerification.__collection_name__)

    verifications = TypeAdapter(list[NewsVerification]).validate_python(collection.find().to_list())

    base_metadata = {
        "collection_name": NewsVerification.__collection_name__,
        "topic": Topic.VERIFICATION_OF_NEWS.value,
    }
    documents = []
    for verification in verifications:
        metadata = {"data_id": ObjectId(str(verification.id)), **base_metadata}
        title = sanitize_text_input(verification.title)
        body = sanitize_text_input(verification.body)
        summary = sanitize_text_input(verification.summary)
        news_documents = [
            Document(page_content=title, metadata=metadata),
            Document(page_content=body, metadata=metadata),
            Document(page_content=summary, metadata=metadata),
        ]
        documents.extend(news_documents)
    db.client.close()
    return splitter.split_documents(documents)


def load_elections():
    db = get_mongo_db()
    collection = db["elections"]

    elections = TypeAdapter(list[Election]).validate_python(collection.find())
    base_metadata = {"collection_name": "elections"}
    documents = []
    for election in elections:
        name = sanitize_text_input(election.name)
        description = sanitize_text_input(election.description)
        result = sanitize_text_input(election.description)
        content = f"{name}\n\n{description}\n\n{result}\n"
        metadata = {"data_id": election.id, **base_metadata}
        documents.append(Document(page_content=content, metadata=metadata))
    db.client.close()
    return documents


def load_calendar_metadata():
    db = get_mongo_db()
    collection = db[ElectoralCalendar.__collection_name__]

    documents = []

    base_metadata = {
        "topic": Topic.ELECTORAL_CALENDAR.value,
        "collection_name": ElectoralCalendar.__collection_name__,
    }

    for calendar in TypeAdapter(list[ElectoralCalendar]).validate_python(collection.find()):
        title = sanitize_text_input(calendar.title)
        date = calendar.date.strftime("%a, %m/%d/%Y - %H:%M")
        resolution = sanitize_text_input(calendar.resolution)
        introduction = sanitize_text_input(calendar.introduction)
        content = f"{title} - {date} - {resolution}\n\n{introduction}\n"
        metadata = {"data_id": calendar.id, **base_metadata}
        documents.append(Document(page_content=content, metadata=metadata))

    return documents


def load_calendar_events():
    db = get_mongo_db()
    collection = db[CalendarEvent.__collection_name__]
    events = TypeAdapter(list[CalendarEvent]).validate_python(collection.find())

    documents = []
    base_metadata = {
        "topic": Topic.ELECTORAL_CALENDAR.value,
        "collection_name": CalendarEvent.__collection_name__,
    }
    for event in events:
        activity = sanitize_text_input(event.activity)
        metadata = {"data_id": event.id, "calendar_id": event.calendar_id, **base_metadata}
        documents.append(Document(page_content=activity, metadata=metadata))
    return documents


def load_candidates():
    db = get_mongo_db()
    can_coll = db.get_collection("candidacies")
    ele_call = db.get_collection("elections")

    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
        ("####", "Header 4"),
    ]

    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)

    elections = TypeAdapter(list[Election]).validate_python(ele_call.find({}))

    all_documents = []
    for election in elections:
        content = sanitize_text_input(
            (f"candidatos en las {election.name} {election.active_round} {election.status}")
        )
        metadata = {
            "data_id": election.id,
            "topic": Topic.CANDIDACIES.value,
            "collection_name": Election.__collection_name__,
        }
        document = Document(content, metadata=metadata)
        all_documents.append(document)

        candidates = TypeAdapter(list[Candidacy]).validate_python(
            can_coll.find({"election_id": election.id})
        )

        for candidacy in candidates:
            metadata = {
                "data_id": candidacy.id,
                "topic": Topic.CANDIDACIES.value,
                "collection_name": Candidacy.__collection_name__,
                "election_id": election.id,
            }

            content = f"partido {candidacy.party.name} {candidacy.party.sigla}"
            content = sanitize_text_input(content)

            all_documents.append(Document(content, metadata=metadata))

            for politician in candidacy.candidates:
                content = f"{politician.full_name} como {politician.position}"
                all_documents.append(Document(content, metadata=metadata))

            gov_program_docs = markdown_splitter.split_text(candidacy.government_plan)

            metadata = {
                **metadata,
                "data_id": candidacy.id,
                "topic": Topic.GOVERNMENT_PROPOSALS.value,
            }

            for doc in gov_program_docs:
                if len(encoding.encode(doc.page_content)) > 1000:
                    sub_docs = splitter.split_documents([doc])
                else:
                    sub_docs = [doc]

                for sub_doc in sub_docs:
                    content = "\n".join([v for v in sub_doc.metadata.values()])
                    content = f"{content}\n\n{sub_doc.page_content}"
                    all_documents.append(Document(page_content=content, metadata=metadata))

    return all_documents


def load_questions_and_answers():
    db = get_mongo_db()
    collection = db[QuestionsAndAnswers.__collection_name__]
    cursor = collection.find({})
    questions_and_answers = TypeAdapter(list[QuestionsAndAnswers]).validate_python(cursor)

    documents = []
    base_metadata = {
        "topic": Topic.QUESTIONS_AND_ANSWERS.value,
        "collection_name": QuestionsAndAnswers.__collection_name__,
    }
    for qa in questions_and_answers:
        question = sanitize_text_input(qa.question)
        documents.append(
            Document(
                page_content=question,
                metadata={"data_id": qa.id, **base_metadata},
            )
        )

    return documents


def create_vectordb():
    print("cargando verificaciones de noticias ...")
    verifications_docs = load_verifications()
    print(f"Se cargador {len(verifications_docs)} verificaciones")

    print("cargando elecciones ...")
    elections_docs = load_elections()
    print(f"Se cargador {len(elections_docs)} elecciones")

    print("cargando calendario de elecciones ...")
    calendar_metadata = load_calendar_metadata()
    calendar_docs = load_calendar_events()
    print(f"Se cargador {len(calendar_docs) + len(calendar_metadata)} eventos del calendario")

    print("cargando candidatos ...")
    candidate_docs = load_candidates()
    print(f"Se cargador {len(candidate_docs)} candidatos")

    print("cargando preguntas y respuestas ...")
    questions_and_answers_docs = load_questions_and_answers()
    print(f"Se cargador {len(questions_and_answers_docs)} preguntas y respuestas")

    all_documents = [
        *verifications_docs,
        *elections_docs,
        *calendar_metadata,
        *calendar_docs,
        *candidate_docs,
        *questions_and_answers_docs,
    ]
    print(f"Se cargador un total de {len(all_documents)} documentos en el vector store")

    vectordb = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=settings.mongo.uri,
        db_name=settings.mongo.db_name,
        collection_name=settings.mongo.collection_name,
        embedding=embedding,
        index_name=settings.mongo.index_name,
        relevance_score_fn="cosine",
        namespace=f"{settings.mongo.db_name}.{settings.mongo.collection_name}",
    )
    search_index = None

    for idx in vectordb.collection.list_search_indexes():
        if idx["name"] == settings.mongo.index_name:
            search_index = idx
            break

    if search_index:
        existing_filters = {
            f["path"] for f in search_index["latestDefinition"]["fields"] if f["type"] == "filter"
        }

        if not existing_filters == set(FILTERS):
            vectordb.collection.drop_search_index(settings.mongo.index_name)
            print("Index dropped due to filter mismatch")

    vectordb.create_vector_search_index(settings.mongo.dimensions, FILTERS)

    print("deleteting old data...")
    vectordb.collection.delete_many({})

    vectordb.add_documents(documents=all_documents)

    print("Base de datos vectorial creada y persistida")
    return vectordb
