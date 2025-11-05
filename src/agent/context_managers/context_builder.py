from src.mongo.models.calendar_models import CalendarEvent, ElectoralCalendar
from src.mongo.models.candidacies_models import Candidacy, CandidacyStatus, Election
from src.mongo.models.qa_model import QuestionsAndAnswers
from src.mongo.models.verifications_models import NewsVerification


class ContextBuilder:
    """A class for building context information from election and candidacy data.

    This class helps construct formatted context strings containing election information,
    candidate information, and not found messages for use in AI agents.
    """

    def __init__(self) -> None:
        """Initialize the ContextBuilder with an empty context dictionary."""
        self.__context_dict: dict[str, list[str]] = {}

    def reset(self) -> None:
        """Reset the internal context dictionary to its initial empty state."""
        self.__context_dict = {}

    def add_not_found_messages(self, msg: str) -> None:
        """Add a message indicating that information was not found.

        Args:
            msg (str): The message to add indicating a not found item.
        """
        if "not_found" not in self.__context_dict:
            self.__context_dict["not_found"] = []
        self.__context_dict["not_found"].append(msg)

    def add_capabilities(self, text: str):
        if "capabilities" not in self.__context_dict:
            self.__context_dict["capabilities"] = []
        self.__context_dict["capabilities"].append(f"- {text}")

    def add_questions_and_answers(self, qas: list[QuestionsAndAnswers]):
        if "qas" not in self.__context_dict:
            self.__context_dict["qas"] = []

        for qa in qas:
            self.__context_dict["qas"].append(
                f"**Pregunta:** {qa.question}\n**Respuesta:** {qa.answer}"
            )

    def set_election(self, election: Election):
        """Set election information in the context.

        Args:
            election (Election): The election object containing election details.
        """
        self.__context_dict["election"] = []
        item = f"### {election.name} ({election.active_round})\n\n"
        item += f"ID: {election.id}\n\n"
        item += f"Fecha de elección: {election.election_date}\n\n"
        item += f"{election.description}\n\n"
        item += f"Fuente: {election.source}"
        if election.winner:
            item += f"\n\nGanador: {election.winner.party.name} ({election.winner.party.sigla})"
        if election.result:
            item += f"\n\nResultados de las elecciones: \n{election.result}"
        self.__context_dict["election"].append(item)

    def add_candidacies(self, candidacies: list[Candidacy], include_gov_plan: bool = False) -> None:
        """Add candidacy information to the context.

        Args:
            candidacies (list[Candidacy]): A list of candidacy objects to add to the context.
        """
        if "candidacies" not in self.__context_dict:
            self.__context_dict["candidacies"] = []

        for candidacy in candidacies:
            item = f"- {candidacy.party.name} ({candidacy.party.sigla}) ID de la elección: {candidacy.election_id}"
            if CandidacyStatus(candidacy.status) is not CandidacyStatus.ACTIVE:
                item += f" ({candidacy.status})"
            for candidate in candidacy.candidates:
                item += f"\n\t- {candidate.full_name} - {candidate.position}"
                item += "" if candidate.is_active else " (inativo)"
            if include_gov_plan and CandidacyStatus(candidacy.status) is CandidacyStatus.ACTIVE:
                item += (
                    f"\n\tPlan de gobierno de ({candidacy.party.name} - {candidacy.party.sigla}):\n"
                )
                item += (
                    f"```txt\n{candidacy.government_plan.strip()}\n\tFuente: {candidacy.source}```"
                )

            self.__context_dict["candidacies"].append(item)
        if not self.__context_dict["candidacies"]:
            del self.__context_dict["candidacies"]

    def add_news_verifications(self, news_verifications: list[NewsVerification]):
        if "news_verifications" not in self.__context_dict:
            self.__context_dict["news_verifications"] = []
        for new in news_verifications:
            item = f"### {new.title}\n\n"
            item += f"**Fecha** {new.publication_date.strftime('%a, %m/%d/%Y - %H:%M')} "
            item += f"**Posted in** [{new.classified_as}]({new.section_url})\n\n"
            item += f"_{new.summary}_\n\n"
            item += f"{new.body}\n\n"
            item += f"**Fuente principal** {new.url}\n\n"
            tags = " ".join([f"[{tag.name}]({tag.url})" for tag in new.tags])
            item += f"**Tags** {tags}"
            self.__context_dict["news_verifications"].append(item)

        if not self.__context_dict["news_verifications"]:
            del self.__context_dict["news_verifications"]

    def add_calendars(self, calendars: list[ElectoralCalendar]):
        if "calendars" not in self.__context_dict:
            self.__context_dict["calendars"] = []
        for calendar in calendars:
            item = f"### {calendar.title} - De la elección: {calendar.election_id}\n\n"
            item += f"**Fecha** {calendar.date.strftime('%a, %m/%d/%Y - %H:%M')}\n"
            item += f"**resolution** {calendar.resolution}\n"
            item += f"**Enlace** {calendar.pdf_url}\n"
            item += f"{calendar.introduction}\n"
            item += "**Firmas**\n"
            for signature in calendar.signatures:
                item += f"- {signature.full_name} - {signature.position}"
            self.__context_dict["calendars"].append(item)

    def add_events(self, events: list[CalendarEvent]):
        if "events" not in self.__context_dict:
            self.__context_dict["events"] = []
        for event in events:
            scenery = event.scenery if event.scenery != "main" else "Principal\n"
            item = f"### {event.activity} - Del calendario: {event.calendar_id}\n\n"
            item += f"**No.** {event.no}\n"
            item += f"**Escenario** {scenery}\n"
            item += f"**Días** (antes o despues de las elecciones) {event.days}\n"
            item += f"**Desde** {event.from_date.strftime('%a, %m/%d/%Y - %H:%M')}\n"
            item += f"**Hasta** {event.to_date.strftime('%a, %m/%d/%Y - %H:%M')}\n"
            item += f"**Duración** {event.duration} días\n"
            item += f"**Referencia** {event.reference}\n\n"
            item += f"**Plazo** {event.place}"
            self.__context_dict["events"].append(item)

    def build_context(self) -> str:
        """Build and return the complete context string.

        Returns:
            str: The formatted context string containing all election, candidacy, and
                 not found information.
        """
        if not self.__context_dict:
            return ""

        context = "# Contenido recuperado\n\n"
        if "election" in self.__context_dict:
            context += "## Eleccion\n\n"
            context += "\n\n".join(self.__context_dict["election"])
            context += "\n\n"

        if "candidacies" in self.__context_dict:
            context += "## Candidaturas\n\n"
            context += "\n\n".join(self.__context_dict["candidacies"])
            context += "\n\n"

        if "news_verifications" in self.__context_dict:
            context += "## Verificaciones de Noticias\n\n"
            context += "\n\n".join(self.__context_dict["news_verifications"])
            context += "\n\n"

        if "qas" in self.__context_dict:
            context += "## Preguntas y respuestas\n\n"
            context += "\n\n".join(self.__context_dict["qas"])
            context += "\n\n"

        if "capabilities" in self.__context_dict:
            context += "## Tus capacidades como asistente\n\n"
            context += "\n".join(self.__context_dict["capabilities"])
            context += "\n\n"

        if "not_found" in self.__context_dict:
            context += "## No encontrado\n\n"
            context += "\n\n".join(self.__context_dict["not_found"])
            context += "\n\n"

        self.reset()
        return context
