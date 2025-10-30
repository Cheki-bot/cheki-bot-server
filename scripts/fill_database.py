import json
import re
from datetime import datetime

from pydantic import TypeAdapter

from src.core.config import settings
from src.core.tools import bo_str_date_to_datetime
from src.mongo import get_mongo_db
from src.mongo.models import (
    CalendarEvent,
    CalendarSignature,
    Candidacy,
    CandidacyStatus,
    Election,
    ElectionStatus,
    ElectoralCalendar,
    NewsTag,
    NewsVerification,
    PoliticalParty,
    Politician,
    QuestionsAndAnswers,
)
from src.mongo.types import PyObjectId

folder = "base_file"
file_path = f"{folder}/{settings.google.data_filename}"


def fill_elections():
    elections = [
        Election(
            id="68e533b125beb0374356fcac",
            name="Elecciones generales de Bolivia de 2025",
            description="Los votantes bolivianos elegirán al presidente y vicepresidente de Bolivia, 130 miembros de la Cámara de Diputados de Bolivia y 36 integrantes de la Cámara de Senadores de Bolivia para el período 2025-2030.",
            election_date=datetime(2025, 8, 17),
            status=ElectionStatus.COMPLETED,
            result="📊 Resultados oficiales — Elecciones 2025 🇧🇴  \n🥇 PDC: 32.06%\n🥈 LIBRE: 26.7%\nNingún partido alcanzó mayoría absoluta.\n🗳️ Segunda vuelta: 19 de octubre de 2025.\n#Elecciones2025 #BoliviaDecide #SegundaVuelta",
            source="https://www.chequeatuvoto.chequeabolivia.bo/",
        ),
        Election(
            id="68e533b225beb0374356fcad",
            name="Elecciones generales de Bolivia de 2025 segunda vuelta",
            description="Segunda vuelta de las elecciones generales de Bolivia de 2025",
            election_date=datetime(2025, 10, 19),
            status=ElectionStatus.COMPLETED,
            result="📊 Resultados oficiales — Elecciones 2025 🇧🇴 Segunda vuelta  \n🥇 PDC: 54.96%\n🥈 LIBRE: 45.04%.\n🗳️ Segunda vuelta: 19 de octubre de 2025.\n#Elecciones2025 #BoliviaDecide #SegundaVuelta",
            source="https://www.chequeatuvoto.chequeabolivia.bo/",
        ),
    ]
    db = get_mongo_db()
    collection = db.get_collection("elections")

    ids = {_id["_id"] for _id in collection.find({}, {"_id": 1}).to_list()}

    records = TypeAdapter(list).dump_python(elections, by_alias=True)

    records = [record for record in records if record["_id"] not in ids]

    if not records:
        return 0
    results = collection.insert_many(records)
    db.client.close()
    return len(results.inserted_ids)


def fill_candidacies() -> int:
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        gov_programs = data.get("government_programs", [])

    first_election_id = "68e533b125beb0374356fcac"
    second_election_id = "68e533b225beb0374356fcad"

    candidacies: list[Candidacy] = []

    db = get_mongo_db()
    collection = db.get_collection("candidacies")
    for gp in gov_programs:
        with open(gp["government_program_file"], "r", encoding="utf-8") as f:
            text = f.read()

        candidacy = Candidacy(
            _id=gp.get("_id", None),
            party=PoliticalParty(name=gp["party"], sigla=gp["sigla"]),
            candidates=[
                Politician(full_name=gp["president"], position="Presidente"),
                Politician(full_name=gp["vice_president"], position="Vice-presidente"),
            ],
            status=CandidacyStatus.WITHDRAWN
            if gp.get("status") == "no participa"
            else CandidacyStatus.ACTIVE,
            government_plan=text,
            election_id=PyObjectId(first_election_id),
        )

        candidacies.append(candidacy)
        if gp.get("segunda_vuelta", False):
            candidacy = candidacy.model_copy(deep=True)
            candidacy.election_id = PyObjectId(second_election_id)
            candidacies.append(candidacy)

    records = TypeAdapter(list).dump_python(candidacies, by_alias=True, exclude_none=True)

    elements = {(e["party"]["sigla"], str(e["election_id"])) for e in collection.find().to_list()}

    records = [
        record
        for record in records
        if (record.get("party").get("sigla"), str(record.get("election_id"))) not in elements
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
        verification = NewsVerification(
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


def fill_questions_and_asnwers():
    db = get_mongo_db()
    collection = db["questions_and_answers"]
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        qas_raw = data.get("questions_and_answers", [])
    qas = TypeAdapter(list[QuestionsAndAnswers]).validate_python(qas_raw)
    records = TypeAdapter(list).dump_python(qas, exclude_none=True)

    ids = {_id["_id"] for _id in collection.find({}, {"_id": 1}).to_list()}

    records = [record for record in records if record.get("_id") not in ids]

    if not records:
        return 0

    results = collection.insert_many(records)
    for _id, qa_raw in zip(results.inserted_ids, qas_raw):
        qa_raw["_id"] = str(_id)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    db.client.close()
    return len(results.inserted_ids)


def fill_calendar():
    db = get_mongo_db()
    collection = db["calendars"]

    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        calendar_metadata = data.get("calendar_metadata", {})
        calender_events = data.get("calendar", [])

    ids = {str(_id["_id"]) for _id in collection.find({}, {"_id": 1}).to_list()}

    registered_ids = calendar_metadata.get("registered_ids")

    if registered_ids is not None and any([_id in ids for _id in registered_ids]):
        return 0, 0

    first_election_id = "68e533b125beb0374356fcac"
    second_election_id = "68e533b225beb0374356fcad"

    first_round_calendar = ElectoralCalendar(
        pdf_url="https://www.oep.org.bo/documentos/04-04-25-calendario-Electoral-EG-2025.pdf",
        title=calendar_metadata.get("title"),
        resolution=calendar_metadata.get("resolution"),
        date=bo_str_date_to_datetime(calendar_metadata.get("date")),
        introduction=calendar_metadata.get("introduction"),
        signatures=[
            CalendarSignature(full_name=s.get("name"), position=s.get("position"))
            for s in calendar_metadata.get("signatories", [])
        ],
        election_id=first_election_id,
    )

    second_round_calendar = first_round_calendar.model_copy(deep=True)
    second_round_calendar.election_id = second_election_id

    records = [first_round_calendar.model_dump(), second_round_calendar.model_dump()]

    if not records:
        return 0, 0

    results = collection.insert_many(records)
    events = []

    for calendar_id in results.inserted_ids:
        events.extend(
            [
                CalendarEvent(
                    scenery=event.get("scenario"),
                    no=event.get("no"),
                    activity=event.get("activity"),
                    days=event.get("days"),
                    from_date=bo_str_date_to_datetime(event.get("from_date")),
                    to_date=bo_str_date_to_datetime(event.get("to_date")),
                    duration=event.get("duration"),
                    reference=event.get("reference"),
                    place=event.get("plazo"),
                    calendar_id=calendar_id,
                )
                for event in calender_events
            ]
        )
    collection = db["calendar_events"]
    records = TypeAdapter(list).dump_python(events, exclude_none=True)
    events_results = collection.insert_many(records)

    calendar_metadata["registered_ids"] = [str(_id) for _id in results.inserted_ids]

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    db.client.close()
    return len(results.inserted_ids), len(events_results.inserted_ids)


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
    print("Filling questions and answers...")
    count = fill_questions_and_asnwers()
    print(f"Se crearon {count} preguntas y respuestas")
    print("Filling calendar...")
    count_calendars, count_events = fill_calendar()
    print(f"Se crearon {count_calendars} calendarios y {count_events} eventos")
