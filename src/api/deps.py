from .. import ENV
from ..agents.nebius_agent import NebiusAgent
from ..agents.openai_agent import OpenAIAgent


def get_agent():
    match ENV.llm.provider:
        case "openai":
            return OpenAIAgent()
        case "nebius":
            return NebiusAgent()
        case _:
            raise NotImplementedError("Provider not supported")
