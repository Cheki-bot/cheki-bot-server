from langchain_chroma import Chroma
from langchain_community.document_loaders import JSONLoader
from langchain_nebius import NebiusEmbeddings

from src.settings import Settings

settings = Settings(_env_file=".env")


def create_vectordb():
    print("Iniciando la creación de la base de datos vectorial...")

    file_path = "base_file/Prueba-100verificaciones-Json-SIN-HTML.json"
    print(f"Cargando documentos desde el archivo: {file_path}")

    loader = JSONLoader(
        file_path=file_path,
        jq_schema=".[] | {title, body, field_fecha_publicacion_web, field_mt_post_categories, field_mt_subheader_body, field_tags, field_tendencia_politica}",
        text_content=False,
    )

    print("Cargando documentos...")
    documents = loader.load()
    print(f"Se cargaron {len(documents)} documentos")

    emb_model = NebiusEmbeddings(
        model=settings.llm.emb_model,
        api_key=settings.llm.api_key,
    )
    print(f"Modelo de embeddings inicializado: {settings.llm.emb_model}")

    print("Creando la base de datos vectorial...")
    vectordb = Chroma.from_documents(
        documents,
        embedding=emb_model,
        persist_directory=settings.chroma.persist_directory,
    )

    print(
        f"Base de datos vectorial creada y persistida en: {settings.chroma.persist_directory}"
    )
    return vectordb
