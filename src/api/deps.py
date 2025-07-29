from .. import ENV
from ..agents.openai_agent import OpenAIAgent


def get_agent():
    match ENV.llm.provider:
        case "openai":
            return OpenAIAgent()
        case _:
            raise NotImplementedError("Provider not supported")
