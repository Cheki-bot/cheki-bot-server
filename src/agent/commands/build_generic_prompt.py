from langchain_core.documents import Document

from src.agent.context_managers.prompts import CALENDAR_EVENT_PROMPT, GOV_PROGRAM_PROMPT
from src.agent.interfaces.build_topic_prompt import BuildTopicPrompt
from src.agent.schemas import Topic


class BuildGenericPrompt(BuildTopicPrompt):
    def __format_content(self, documents: list[Document]):
        content = []
        for document in documents:
            content.append(document.page_content)
        return "\n\n".join(content)

    async def run(self, documents: list[Document]) -> str:
        topic = Topic(documents[0].metadata.get("topic"))

        prompt = f"## Contenido sobre {topic}\n\n"

        match topic:
            case Topic.GOVERNMENT_PROPOSALS:
                content = self.__format_content(documents)
                content = GOV_PROGRAM_PROMPT.format(content=content)
                prompt += content
            case Topic.ELECTORAL_CALENDAR:
                content = self.__format_content(documents)
                content = CALENDAR_EVENT_PROMPT.format(content=content)
                prompt += content
            case Topic.QUESTIONS_AND_ANSWERS:
                content = ""
                for doc in documents:
                    content += "- Pregunta: {question}\nRespuesta: {answer}\n\n".format(
                        question=doc.metadata.get("question", ""),
                        answer=doc.metadata.get("answer", ""),
                    )
                prompt = "## Preguntas y respuestas\n\n"
                prompt += content
            case Topic.CAPABILITIES:
                prompt += """
### Capacidades que tienes como chatbot:
- Monstrar información sobre validaciones de verdad de noticias en redes sociales y otros medios
- Responder pregutas.
- Proporcionar inforamación sobre las eleciones de bolivia
- Proporcionar información sobre candidatos y sus propuestas de govierno"""
        return prompt

    async def __call__(self, documents: list[Document]):
        return await self.run(documents)
