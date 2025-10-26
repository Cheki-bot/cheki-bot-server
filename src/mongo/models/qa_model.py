from .mongo_model import MongoModel


class QuestionsAndAnswers(MongoModel):
    question: str
    answer: str
