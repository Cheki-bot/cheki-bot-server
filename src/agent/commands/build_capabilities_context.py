from src.agent.context_managers.context_builder import ContextBuilder
from src.agent.interfaces.build_context import BuildContext
from src.agent.schemas import TopicSelection


class BuildCapabilitiesContext(BuildContext):
    async def run(self, topic_selection: TopicSelection, context_builder: ContextBuilder):
        context_builder.add_capabilities(
            "Busqueda de noticias verificadas por chequea bolivia, puedes consultar sobre noticias relacionadas con la politica o elecciones en bolivia para conocer que es lo que se sabe"
        )
        context_builder.add_capabilities(
            "Proporcionar información sobre candidatos a cargos publicos, puedes consultar sobre candidatos a presidencia, vicepresidencia, gobernadores, alcaldes, entre otros."
            "Para mejores resultado procura proporcionar nombres y apellidos de los candidatos, partidos politicos, la elección especifica (tipo, region), si se trata de una segunda vuelta y de que año."
        )

        context_builder.add_capabilities(
            "Proporcionar información de planes de gobierno, puedes consultar sobre planes de gobierno de candidatos a presidencia, vicepresidencia, gobernadores, alcaldes, entre otros. "
            "Para mejores resultado procura proporcionar nombres y apellidos de los candidatos, partidos politicos, la elección especifica (tipo, region), si se trata de una segunda vuelta y de que año."
        )

        context_builder.add_capabilities(
            "Proporcionar información sobre el calendario electoral vigente y sus eventos programandos. "
            "Para mejores resultado procura proporcionar el año, tipo de elección, region, y si se trata de una segunda vuelta. fecha del evento"
        )

        context_builder.add_capabilities("Preguntas y respuestas predeterminadas en el sistema")

        return context_builder
