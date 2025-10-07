import json
import re
from datetime import datetime

from bson import ObjectId
from pydantic import TypeAdapter

from src.core.entities import NewsTag, PoliticalParty, Politician, Status
from src.mongo import get_mongo_db
from src.mongo.models import CandidacyModel, ElectionModel, NewsVerificationModel
from src.settings import Settings

settings = Settings(_env_file=".env")

folder = "base_file"
file_path = f"{folder}/{settings.google.data_filename}"


def fill_elections():
    elections = [
        ElectionModel(
            id="68e533b125beb0374356fcac",
            name="Elecciones generales de Bolivia de 2025",
            description="Los votantes bolivianos elegirán al presidente y vicepresidente de Bolivia, 130 miembros de la Cámara de Diputados de Bolivia y 36 integrantes de la Cámara de Senadores de Bolivia para el período 2025-2030.",
            election_date=datetime(2025, 8, 17),
            status=Status.COMPLETED,
            result="Las elecciones concluyeron en segunda vuelta",
        ),
        ElectionModel(
            id="68e533b225beb0374356fcad",
            name="Elecciones generales de Bolivia de 2025 segunda vuelta",
            description="Segunda vuelta de las elecciones generales de Bolivia de 2025",
            election_date=datetime(2025, 10, 17),
            status=Status.ACTIVE,
        ),
    ]
    db = get_mongo_db()
    collection = db.get_collection("elections")
    ids = {str(_id["_id"]) for _id in collection.find({}, {"_id": 1}).to_list()}
    records = TypeAdapter(list).dump_python(elections, by_alias=True)

    records = [
        {
            **record,
            "_id": ObjectId(record["_id"]),
        }
        for record in records
        if record["_id"] not in ids
    ]
    if not records:
        return 0
    results = collection.insert_many(records)
    db.client.close()
    return len(results.inserted_ids)


def fill_verifications():
    db = get_mongo_db()
    collection = db["news_verifications"]
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        news = data.get("verifications", [])

    def get_tag(tag_str: str):
        matchs = re.search(r"\[(.*)\]\((.*)\)", tag_str)
        if matchs:
            return NewsTag(name=matchs.group(1), url=matchs.group(2))

    news_ids = {str(_id["_id"]) for _id in collection.find({}, {"_id": 1}).to_list()}

    news = [new for new in news if not (new.get("_id") and new.get("_id") in news_ids)]

    verifications = []
    for new in news:
        verification = NewsVerificationModel(
            title=new["title"],
            classified_as=new["post_category"],
            section_url=new["section_url"],
            summary=new["summary"],
            url=new["url"],
            publication_date=datetime.strptime(new["publication_date"], "%a, %m/%d/%Y - %H:%M"),
            tags=[get_tag(tag) for tag in new["tags"] if get_tag(tag)],
            body=new["body"],
        )
        verifications.append(verification)
    records = TypeAdapter(list).dump_python(verifications, by_alias=True, exclude_none=True)
    if not verifications:
        db.client.close()
        return 0
    results = db.get_collection("news_verifications").insert_many(records)
    for _id, new in zip(results.inserted_ids, news):
        new["_id"] = str(_id)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    db.client.close()
    return len(results.inserted_ids)


def fill_candidacies():
    presi = "Presidente"
    vice = "Vicepresidente"
    first_election_id = "68e533b125beb0374356fcac"
    second_election_id = "68e533b225beb0374356fcad"
    candidacies: list[CandidacyModel] = [
        CandidacyModel(
            id="68e5521e63ccae8a64b0f106",
            party=PoliticalParty(name="MOVIMIENTO DE REGENERACIÓN NACIONAL", sigla="MORENA"),
            candidates=[
                Politician(full_name="Eva Copa", position="Presidente"),
                Politician(full_name="Jorge Richter", position="Vice Presidente"),
            ],
            status="Inhabilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5521e63ccae8a64b0f107",
            party=PoliticalParty(name="AUTONOMÍAS PARA BOLIVIA - SÚMATE", sigla="APB-SUMATE"),
            candidates=[
                Politician(full_name="Manfred Reyes Villa", position=presi),
                Politician(full_name="", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5521f63ccae8a64b0f108",
            party=PoliticalParty(name="ALIANZA LIBERTAD Y DEMOCRACIA", sigla="LIBRE"),
            candidates=[
                Politician(full_name='Jorge "Tuto" Quiroga', position=presi),
                Politician(full_name="Juan Pablo Velasco", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5521f63ccae8a64b0f109",
            party=PoliticalParty(name="ALIANZA LIBERTAD Y DEMOCRACIA", sigla="LIBRE"),
            candidates=[
                Politician(full_name='Jorge "Tuto" Quiroga', position=presi),
                Politician(full_name="Juan Pablo Velasco", position=vice),
            ],
            status="Habilitado",
            election_id=second_election_id,
        ),
        CandidacyModel(
            id="68e5522063ccae8a64b0f10a",
            party=PoliticalParty(name="ALIANZA POPULAR", sigla="AP"),
            candidates=[
                Politician(full_name="Andrónico Rodriguez", position=presi),
                Politician(full_name="Mariana Prado", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522063ccae8a64b0f10b",
            party=PoliticalParty(name="ACCIÓN DEMOCRÁTICA NACIONALISTA", sigla="ADN"),
            candidates=[
                Politician(full_name="Pavel Aracena", position=presi),
                Politician(full_name="Victor Hugo Nuñez", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522163ccae8a64b0f10c",
            party=PoliticalParty(name="MOVIMIENTO AL SOCIALISMO", sigla="MAS - IPSP"),
            candidates=[
                Politician(full_name="Eduardo del Castillo", position=presi),
                Politician(full_name="Milan Berna", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522163ccae8a64b0f10d",
            party=PoliticalParty(name="ALIANZA UNIDAD", sigla="UN - CREEMOS"),
            candidates=[
                Politician(full_name="Samuel Doria Medina", position=presi),
                Politician(full_name="José Luis Lupo", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522263ccae8a64b0f10e",
            party=PoliticalParty(name="PARTIDO DEMÓCRATA CRISTIANO", sigla="PDC"),
            candidates=[
                Politician(full_name="Rodrigo Paz", position=presi),
                Politician(full_name="Edman Lara", position=vice),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522363ccae8a64b0f10f",
            party=PoliticalParty(name="PARTIDO DEMÓCRATA CRISTIANO", sigla="PDC"),
            candidates=[
                Politician(full_name="Rodrigo Paz", position=presi),
                Politician(full_name="Edman Lara", position=vice),
            ],
            status="Habilitado",
            election_id=second_election_id,
        ),
        CandidacyModel(
            id="68e5522863ccae8a64b0f110",
            party=PoliticalParty(name="FRENTE PARA LA VICTORIA", sigla="FP"),
            candidates=[
                Politician(full_name="Jhonny Fernandez", position=presi),
            ],
            status="Habilitado",
            election_id=first_election_id,
        ),
        CandidacyModel(
            id="68e5522a63ccae8a64b0f111",
            party=PoliticalParty(name="NUEVA GENERACIÓN POLÍTICA", sigla="NGP"),
            candidates=[
                Politician(full_name="Fidel Tapia", position=presi),
                Politician(full_name="Edgar Uriona", position=vice),
            ],
            status="Inhabilitado",
            election_id=first_election_id,
        ),
    ]
    db = get_mongo_db()
    collection = db.get_collection("candidacies")
    ids = {str(_id["_id"]) for _id in collection.find({}, {"_id": 1}).to_list()}
    records = TypeAdapter(list).dump_python(candidacies, by_alias=True, exclude_none=True)

    records = [
        {
            **record,
            "_id": ObjectId(record["_id"]),
        }
        for record in records
        if record["_id"] not in ids
    ]
    if not records:
        return 0
    results = collection.insert_many(records)
    db.client.close()
    return len(results.inserted_ids)


def fill_database():
    print("Filling database...")
    count = fill_elections()
    print(f"Se crearon {count} elecciones")
    print("Filling verifications...")
    count = fill_verifications()
    print(f"Se crearon {count} verificaciones")
    print("Filling candidacies...")
    count = fill_candidacies()
    print(f"Se crearon {count} candidaturas")
