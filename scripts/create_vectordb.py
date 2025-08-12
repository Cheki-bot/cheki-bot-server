import json
import os

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
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=5)


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
            splitted_document = Document(page_content=chunk, metadata=metadata)
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
        page_content = json.loads(document.page_content)
        chunks = splitter.split_text(page_content["content"])
        for chunk in chunks:
            metadata = {
                **page_content,
                "type": DocType.GOV_PROGRAMS.value,
            }
            del metadata["content"]
            content = "Plan o programa de gobierno \n{} - {} - {}\n{}".format(
                metadata["sigla"],
                metadata["president"],
                metadata["vice_president"],
                chunk,
            )
            splitted_document = Document(page_content=content, metadata=metadata)
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
        content = "{}\n\n{}\nResolución {}\n\nFirmas \n\n{}".format(
            page_content["title"],
            page_content["date"],
            page_content["resolution"],
            "\n".join(
                [
                    f"{signature['name']} - {signature['position']}"
                    for signature in page_content["signatories"]
                ]
            ),
        )
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
Fuente - [calendario de elecciones generales 2025](https://fuentedirecta.oep.org.bo/noticia/el-tse-aprueba-el-calendario-electoral-para-las-elecciones-generales-2025)
""".format(**page_content)
        splitted_documents.append(
            Document(
                page_content=content,
                metadata={"type": DocType.CALENDAR.value},
            )
        )
    print(f"Calendario cargado: {len(splitted_documents)} documentos")
    return splitted_documents


def create_vectordb():
    verifications_docs = load_verifications()
    government_programs_docs = load_government_programs()
    calendar_metadata = load_calendar_metadata()
    calendar_docs = load_calendar()

    all_documents = [
        *verifications_docs,
        *government_programs_docs,
        *calendar_metadata,
        *calendar_docs,
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

    print(
        f"Base de datos vectorial creada y persistida en: {settings.chroma.persist_directory}"
    )
    return vectordb
