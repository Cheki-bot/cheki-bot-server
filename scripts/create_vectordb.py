import json
import re

import tiktoken
from bson import ObjectId
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_mongodb import MongoDBAtlasVectorSearch
from langchain_openai import OpenAIEmbeddings
from pydantic import TypeAdapter

from src.agent.schemas import Topic
from src.core.tools import sanitize_text_input
from src.mongo import get_mongo_db
from src.mongo.models import CandidacyModel, ElectionModel, NewsVerificationModel
from src.settings import Settings

settings = Settings(_env_file=".env")

folder = "base_file"
file_path = f"{folder}/{settings.google.data_filename}"

embedding = OpenAIEmbeddings(
    model=settings.llm.emb_model,
    api_key=settings.llm.api_key,
)

encoding = tiktoken.encoding_for_model("text-embedding-3-small")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=100,
    chunk_overlap=20,
    length_function=lambda text: len(encoding.encode(text)),
    separators=["\n\n", "\n", ". ", " ", ""],
)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()  # espacios redundantes
    return text


def load_verifications():
    db = get_mongo_db()
    collection = db.get_collection("news_verifications")

    verifications = TypeAdapter(list[NewsVerificationModel]).validate_python(collection.find().to_list())

    base_metadata = {"collection_name": "news_verifications", "topic": Topic.VERIFICATION_OF_NEWS.value}
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


def load_government_programs():
    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".government_programs[]",
        text_content=False,
    )
    documents = loader.load()
    splitted_documents = []
    for document in documents:
        program = json.loads(document.page_content)  # type: ignore
        party = program["party"]
        sigla = program["sigla"]
        president = program["president"]
        vice_president = program["vice_president"]
        status = program.get("status")
        if status and status == "no participa":
            metadata = {"status": status, "topic": Topic.GOVERNMENT_PROPOSALS.value}
            page_content = f"El partido {party} ({sigla}) binomio {president} y {vice_president} decidieron no participar como candidatos en las elecciones"
            continue
        government_plan = program["government_plan"]
        for index, (key, value) in enumerate(government_plan.items()):
            title = str(key).replace("_", " ")
            summary = str(value.get("summary", ""))
            _ = str(value.get("content", ""))
            num_seq = index + 1
            metadata = {"num_seq": num_seq, "topic": Topic.GOVERNMENT_PROPOSALS.value}

            chunks = splitter.split_text(summary)
            for chunk in chunks:
                page_content = "\n".join(
                    [
                        f"Plan de gobierno del Presidente {president} "
                        + f"y vice-presidente {vice_president} "
                        + f"del partido {party} ({sigla})",
                        f"{title} parte {num_seq}",
                        chunk,
                    ]
                )
                splitted_document = Document(page_content=page_content.lower(), metadata=metadata)
                splitted_documents.append(splitted_document)

    return splitted_documents


def load_calendar_metadata():
    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".calendar_metadata",
        text_content=False,
    )
    documents = loader.load()
    splitted_documents = []
    for document in documents:
        page_content = json.loads(document.page_content)
        content = "Titulo {}\n\nFecha {}\nResolución {}\n\nFirmas \n\n{}".format(
            page_content["title"],
            page_content["date"],
            page_content["resolution"],
            "\n".join([f"{signature['name']} - {signature['position']}" for signature in page_content["signatories"]]),
        )
        content = clean_text(content).lower()
        splitted_documents.append(
            Document(
                page_content=content,
                metadata={"topic": Topic.ELECTORAL_CALENDAR.value},
            )
        )

    return splitted_documents


def load_calendar():
    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".calendar[]",
        text_content=False,
    )
    documents = loader.load()
    splitted_documents = []
    for document in documents:
        page_content = json.loads(document.page_content)
        content = """Escenario Nro. {no} - {scenario}
Actividad - {activity}
Duración - {days} día(s) antes o después del dia de las elecciones (17 de agosto 2025)
Periodo - {from_date} a {to_date}
Plazo de Anticipación - {plazo}
Referencia - {reference}
""".format(**page_content)
        content = (
            clean_text(content).lower()
            + "Fuente - [calendario de elecciones generales 2025](https://fuentedirecta.oep.org.bo/noticia/el-tse-aprueba-el-calendario-electoral-para-las-elecciones-generales-2025)"
        )
        splitted_documents.append(
            Document(
                page_content=content,
                metadata={"topic": Topic.ELECTORAL_CALENDAR.value},
            )
        )
    return splitted_documents


def load_candidates():
    db = get_mongo_db()
    can_coll = db.get_collection("candidacies")
    ele_call = db.get_collection("elections")
    cursor = can_coll.find({})
    candidates: list[CandidacyModel] = TypeAdapter(list[CandidacyModel]).validate_python(cursor)
    cursor = ele_call.find({})
    elections = TypeAdapter(list[ElectionModel]).validate_python(cursor)

    base_metadata = {"collection_name": "candidacies", "topic": Topic.CANDIDATES.value}

    all_documents = []
    for election in elections:
        document = Document(
            sanitize_text_input(f"candidatos en las {election.name}"),
            metadata=base_metadata,
        )

        all_documents.append(document)

    for candidacy in candidates:
        content = f"partido {candidacy.party.name} ({candidacy.party.sigla}) "
        for politician in candidacy.candidates:
            content += f"{politician.full_name} como {politician.position} "
        content = sanitize_text_input(content)
        all_documents.append(Document(content, metadata=base_metadata))

    return all_documents


def load_questions_and_answers():
    loader = JSONLoader(file_path=file_path, jq_schema=".questions_and_answers[]", text_content=False)
    documents = loader.load()

    def parse(document: Document):
        content: dict = json.loads(document.page_content)
        question = content["question"].strip()
        answer = content["answer"].strip()
        return Document(
            page_content=sanitize_text_input(question),
            metadata={
                "topic": Topic.QUESTIONS_AND_ANSWERS.value,
                "question": question,
                "answer": answer,
            },
        )

    return [parse(doc) for doc in documents]


def create_vectordb():
    print("cargando verificaciones de noticias ...")
    verifications_docs = load_verifications()
    print(f"Se cargador {len(verifications_docs)} verificaciones")

    print("cargando programas de gobierno ...")
    government_programs_docs = load_government_programs()
    print(f"Se cargador {len(government_programs_docs)} programas de gobierno")

    print("cargando calendario de elecciones ...")
    calendar_metadata = load_calendar_metadata()
    calendar_docs = load_calendar()
    print(f"Se cargador {len(calendar_docs) + len(calendar_metadata)} eventos del calendario")

    print("cargando candidatos ...")
    candidate_docs = load_candidates()
    print(f"Se cargador {len(candidate_docs)} candidatos")

    print("cargando preguntas y respuestas ...")
    questions_and_answers_docs = load_questions_and_answers()
    print(f"Se cargador {len(questions_and_answers_docs)} preguntas y respuestas")

    all_documents = [
        *verifications_docs,
        *government_programs_docs,
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

    for idx in vectordb.collection.list_search_indexes():
        if idx["name"] == settings.mongo.index_name:
            vectordb.collection.drop_search_index(settings.mongo.index_name)
            print(f"Index {settings.mongo.index_name} dropped")
            break
    else:
        print(f"Creating index {settings.mongo.index_name}")
        vectordb.create_vector_search_index(settings.mongo.dimensions, ["type", "collection_name", "topic", "data_id"])

    vectordb.collection.delete_many({})
    vectordb.add_documents(documents=all_documents)

    print("Base de datos vectorial creada y persistida")
    return vectordb
