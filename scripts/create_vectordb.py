import json
import os
import re

import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.consts import DocType
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
    chunk_size=150,
    chunk_overlap=20,
    length_function=lambda text: len(encoding.encode(text)),
    separators=["\n\n", "\n", ". ", " ", ""],
)


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()  # espacios redundantes
    return text


def load_verifications():
    print("Cargando verificaciones...")
    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".verifications[]",
        text_content=False,
    )
    documents = loader.load()
    splitted_documents = []
    for document in documents:
        page_content = json.loads(document.page_content)
        chunks = splitter.split_text(page_content["body"])
        for chunk in chunks:
            metadata = {
                **page_content,
                "tags": " ".join(page_content["tags"]),
                "type": DocType.VERIFICATIONS.value,
            }
            del metadata["body"]
            splitted_document = Document(page_content=clean_text(chunk), metadata=metadata)
            splitted_documents.append(splitted_document)
    print(f"Verificaciones cargadas: {len(splitted_documents)} documentos")
    return splitted_documents


def load_government_programs():
    print("Cargando programas gubernamentales...")
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
        government_plan = program["government_plan"]
        for index, (key, value) in enumerate(government_plan.items()):
            title = str(key).replace("_", " ")
            summary = str(value.get("summary", ""))
            _ = str(value.get("content", ""))
            num_seq = index + 1
            metadata = {"num_seq": num_seq, "type": DocType.GOV_PROGRAMS.value}
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

    print(f"Programas gubernamentales cargados: {len(splitted_documents)} documentos")
    return splitted_documents


def load_calendar_metadata():
    print("Cargando metadatos del calendario...")
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
                metadata={"type": DocType.CALENDAR_META.value},
            )
        )
    print(f"Metadatos del calendario cargados: {len(splitted_documents)} documentos")
    return splitted_documents


def load_calendar():
    print("Cargando calendario...")
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
                metadata={"type": DocType.CALENDAR.value},
            )
        )
    print(f"Calendario cargado: {len(splitted_documents)} documentos")
    return splitted_documents


def load_candidates():
    with open(file_path, "r") as f:
        database = json.load(f)
    candidates: list = database["candidates"]
    header = "CANDIDATURAS\n"
    header += "Lista de candidatos a la elecciones presidenciales de bolivia (2025-2030)"
    candidates_list = ""
    candidates_list_with_summary = ""
    splitted_documents: list[Document] = []
    for candidate in candidates:
        candidates_list += f"- {candidate['candidate']}\n"
        candidates_list_with_summary += f"{candidates_list}{candidate['summary']}\n"

    chunks = splitter.split_text(candidates_list)
    for index, chuck in enumerate(chunks):
        num_seq = index + 1
        page_content = f"{header} Parte {num_seq}\n{chuck} "
        splitted_document = Document(
            page_content=page_content.lower(),
            metadata={
                "num_seq": num_seq,
                "type": DocType.CANDIDATES.value,
            },
        )
        splitted_documents.append(splitted_document)
    chunks = splitter.split_text(candidates_list_with_summary)
    for index, chuck in enumerate(chunks):
        num_seq = index + 1
        page_content = f"{header} y resumen de propuestas Parte {num_seq}\n{chuck} "
        splitted_document = Document(
            page_content=page_content.lower(),
            metadata={
                "num_seq": num_seq,
                "type": DocType.CANDIDATES.value,
            },
        )
        splitted_documents.append(splitted_document)
    return splitted_documents


def load_questions_and_answers():
    loader = JSONLoader(file_path=file_path, jq_schema=".questions_and_answers[]", text_content=False)
    documents = loader.load()

    def parse(document: Document):
        content: dict = json.loads(document.page_content)
        question = content["question"].strip().lower()
        answer = content["answer"]
        return Document(page_content=question, metadata={"type": DocType.Q_A.value, "answer": answer})

    return [parse(doc) for doc in documents]


def create_vectordb():
    verifications_docs = load_verifications()
    government_programs_docs = load_government_programs()
    calendar_metadata = load_calendar_metadata()
    calendar_docs = load_calendar()
    candidate_docs = load_candidates()
    questions_and_answers_docs = load_questions_and_answers()

    all_documents = [
        *verifications_docs,
        *government_programs_docs,
        *calendar_metadata,
        *calendar_docs,
        *candidate_docs,
        *questions_and_answers_docs,
    ]

    if os.path.exists(settings.chroma.persist_directory):
        vectordb = Chroma(
            persist_directory=settings.chroma.persist_directory,
            embedding_function=embedding,
        )
        vectordb.delete_collection()
    vectordb = Chroma.from_documents(
        documents=all_documents,
        embedding=embedding,
        persist_directory=settings.chroma.persist_directory,
    )

    print(f"Base de datos vectorial creada y persistida en: {settings.chroma.persist_directory}")
    return vectordb
