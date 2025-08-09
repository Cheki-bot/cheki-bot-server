import json
import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import JSONLoader
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

from src.settings import Settings

settings = Settings(_env_file=".env")


def create_vectordb():
    print("Iniciando la creación de la base de datos vectorial...")

    file_path = "base_file/processed_data_5.json"
    print(f"Cargando documentos desde el archivo: {file_path}")

    loader = JSONLoader(
        file_path,
        ".[] | {title, body, publication_date, tags, keywords}",
        text_content=False,
    )

    print("Cargando documentos...")
    documents = loader.load()
    print(f"Se cargaron {len(documents)} documentos")

    emb_model = OpenAIEmbeddings(
        model=settings.llm.emb_model,
        api_key=settings.llm.api_key,
    )
    print(f"Modelo de embeddings inicializado: {settings.llm.emb_model}")

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=5)

    print("Dividiendo documentos en fragmentos...")
    splitted_documents = []
    for document in documents:
        page_content = json.loads(document.page_content)
        chunks = splitter.split_text(page_content["body"])
        for chunk in chunks:
            metadata = {
                "title": page_content["title"],
                "publication_date": page_content["publication_date"],
                "tags": " ".join(page_content["tags"]),
                "keywords": " ".join(page_content["keywords"]),
            }
            splitted_document = Document(page_content=chunk, metadata=metadata)
            splitted_documents.append(splitted_document)

    print("Creando la base de datos vectorial...")
    if os.path.exists(settings.chroma.persist_directory):
        vectordb = Chroma(
            persist_directory=settings.chroma.persist_directory,
            embedding_function=emb_model,
        )
        vectordb.delete_collection()
    vectordb = Chroma.from_documents(
        documents=splitted_documents,
        embedding=emb_model,
        persist_directory=settings.chroma.persist_directory,
    )

    print(
        f"Base de datos vectorial creada y persistida en: {settings.chroma.persist_directory}"
    )
    return vectordb
