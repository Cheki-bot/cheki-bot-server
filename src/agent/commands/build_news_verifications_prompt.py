from bson import ObjectId
from langchain_core.documents import Document
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.context_managers.prompts import VERIFICATION_TEMPLATE
from src.agent.interfaces.build_topic_prompt import BuildTopicPrompt
from src.mongo.models import NewsVerificationModel


class BuildNewsVerificatiosPrompt(BuildTopicPrompt):
    def __init__(self, db: Database) -> None:
        self.__db = db

    @property
    def db(self) -> Database:
        return self.__db

    async def run(self, documents: list[Document]) -> str:
        collection = self.db.get_collection("news_verifications")

        ids = {ObjectId(doc.metadata.get("data_id")) for doc in documents if doc.metadata.get("data_id") is not None}

        articles = TypeAdapter(list[NewsVerificationModel]).validate_python(
            collection.find({"_id": {"$in": list(ids)}})
        )

        texts = []

        for index, article in enumerate(articles):
            text = VERIFICATION_TEMPLATE.format(
                title=article.title,
                classified_as=article.classified_as,
                section_url=article.section_url,
                publication_date=article.publication_date.strftime("%d/%m/%Y a las %H:%M"),
                summary=article.summary,
                url=article.url,
                body=article.body,
                tags=" ".join([f"[{tag.name}]({tag.url})" for tag in article.tags]),
            )
            texts.append(text)

        prompt = f"## Verificaciones encontradas\n{'\n'.join(texts)}"

        return prompt

    async def __call__(self, documents: list[Document]):
        return await self.run(documents)
