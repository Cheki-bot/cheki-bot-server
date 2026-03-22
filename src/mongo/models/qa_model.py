from .mongo_model import MongoModel


class QuestionsAndAnswers(MongoModel):
    __collection_name__ = "questions_and_answers"
    question: str
    answer: str
