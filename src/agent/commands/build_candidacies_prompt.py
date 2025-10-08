from bson import ObjectId
from langchain_core.documents import Document
from pydantic import TypeAdapter
from pymongo.database import Database

from src.agent.interfaces.build_topic_prompt import BuildTopicPrompt
from src.core.entities.election_entities import Status
from src.mongo.models import CandidacyModel, ElectionModel


class BuildCandidaciesPrompt(BuildTopicPrompt):
    def __init__(self, db: Database) -> None:
        self.__db = db

    @property
    def db(self) -> Database:
        return self.__db

    async def run(self, documents: list[Document]) -> str:
        status = {
            Status.ACTIVE.value: "Activa en este momento",
            Status.COMPLETED.value: "Finalizada",
            Status.UPCOMING.value: "Anunciada para el futuro",
        }

        ids = {ObjectId(doc.metadata.get("data_id")) for doc in documents if doc.metadata.get("data_id") is not None}

        cand_coll = self.db.get_collection("candidacies")
        elect_coll = self.db.get_collection("elections")

        cursor = elect_coll.find({"status": "active"})
        elections = TypeAdapter(list[ElectionModel]).validate_python(cursor)
        elections_dict: dict[str, ElectionModel] = {e.id: e for e in elections}
        election_ids = set(elections_dict.keys())

        cursor = cand_coll.find(
            {
                "election_id": {"$in": list(election_ids)},
                **({"_id": {"$in": list(ids)}} if ids else {}),
            }
        )
        for data in cursor:
            candidacy = CandidacyModel(**data)
            elections_dict[candidacy.election_id].candidacies.append(candidacy)

        prompt = ""

        for election in elections:
            prompt += f"""
## Datos electorales encontrados:

### {election.name}

{election.description}

### Estado de la elección

- {status[election.status]}

### Candidatos

"""

            candidates_prompt = ""
            for candidacy in election.candidacies:
                candidates_prompt += f"- Partido {candidacy.party.name} ({candidacy.party.sigla})\n"
                for politician in candidacy.candidates:
                    candidates_prompt += f"\t-{politician.full_name} como {politician.position}\n"
            prompt += f"{candidates_prompt}"

        return prompt.strip()

    async def __call__(self, documents: list[Document]) -> str:
        return await self.run(documents)
