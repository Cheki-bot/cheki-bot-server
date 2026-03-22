import json
from typing import Sequence

from fastapi import WebSocketDisconnect
from fastapi.exceptions import HTTPException
from fastapi.testclient import TestClient
from langchain_core.messages import BaseMessage
from typing_extensions import Self

from src.agent.agent import AsyncAgent
from src.agent.schemas import AgentResponseChunk, Platform
from src.api.app import create_app
from src.api.dependencies.injectables import get_agent
from src.mongo import get_async_mongo_db


class MockAgent(AsyncAgent):
    def __init__(self):
        pass

    async def stream(self, messages):
        # Simulate different responses based on content
        if len(messages) > 0 and messages[0].content == "Error":
            raise Exception("Error processing query")
        elif len(messages) > 0 and messages[0].content == "Test with long content":
            # Simulate a response with long content
            chunks = ["Hello, ", "AI is ", "answering ", "here!"]
            for chunk in chunks:
                yield AgentResponseChunk(content=chunk, type="text")
            yield AgentResponseChunk(content="", type="text", done=True)
        else:
            # Normal response simulation
            chunks = ["Hello, ", "AI is ", "answering ", "here!"]
            for chunk in chunks:
                yield AgentResponseChunk(content=chunk, type="text")
            yield AgentResponseChunk(content="", type="text", done=True)

    async def invoke(
        self, messages: Sequence[BaseMessage], platform: Platform = Platform.TELEGRAM
    ) -> str:
        return "Mock response"


class MockCollection:
    collection = None
    count = 0

    def __new__(cls) -> Self:
        if cls.collection is None:
            cls.collection = super().__new__(cls)
        return cls.collection

    def create_index(self, *args, **kwargs):
        pass

    def index_information(self):
        return []

    def count_documents(self, *args, **kwargs):
        return self.count

    def insert_one(self, *args, **kwargs):
        self.count += 1


class MockDatabase:
    db = None

    def __new__(cls) -> Self:
        if cls.db is None:
            cls.db = super().__new__(cls)
        return cls.db

    def __init__(self) -> None:
        self.rate_limit_records = MockCollection()


app = create_app()
app.dependency_overrides[get_agent] = lambda: MockAgent()
app.dependency_overrides[get_async_mongo_db] = lambda: MockDatabase()


client = TestClient(app)


def test_websocket_rate_limit():
    """
    Test that rate limiting works for websocket_endpoint.
    Should block requests after 10 per minute.
    """
    MockDatabase().rate_limit_records.count = 0
    try:
        for i in range(11):
            with client.websocket_connect("/api/chatbot/ws") as websocket:
                websocket.send_json(
                    {
                        "content": "Hello, how are you?",
                        "history": [{"role": "user", "content": "Hi"}],
                    }
                )

                response = websocket.receive_text()
                data = json.loads(response)
        assert data.get("type") == "error"
        assert "Rate limit exceeded" in data.get("content", "")

    except Exception as e:
        if isinstance(e, HTTPException):
            assert e.status_code == 429
        elif isinstance(e, WebSocketDisconnect):
            assert e.code == 1008 and "Rate limit exceeded" in e.reason
        else:
            print(type(e))
            # Re-raise if it's not the expected exception type
            raise e


def test_chatbot_webhook_endpoint_rate_limiting():
    """
    Test that rate limiting works for webhook_endpoint.
    Should block requests after 10 per minute.
    """
    MockDatabase().rate_limit_records.count = 0
    for i in range(10):
        response = client.post(
            "/api/chatbot/webhook",
            json={
                "content": f"Hello, how are you? {i}",
                "history": [{"role": "user", "content": "Hi"}],
            },
        )
        assert response.status_code == 200

    # Make the 11th request (should be blocked by rate limiting)
    response = client.post(
        "/api/chatbot/webhook",
        json={
            "content": "This should be blocked",
            "history": [{"role": "user", "content": "Hi"}],
        },
    )
    assert response.status_code == 429
    assert "Rate limit exceeded" in response.json().get("detail", "")


def test_websocket_endpoint_valid_input():
    MockDatabase().rate_limit_records.count = 0
    # Test valid input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Hello, how are you?",
                "history": [{"role": "user", "content": "Hi"}],
            }
        )
        response = ""
        while True:
            try:
                token = websocket.receive_text()
                data = json.loads(token)
                # Only process text type responses
                if data.get("type") == "text":
                    response += data["content"]
            except WebSocketDisconnect as e:
                assert e.code == 1000
                break
        assert response == "Hello, AI is answering here!"


def test_websocket_endpoint_invalid_json():
    MockDatabase().rate_limit_records.count = 0
    # Test invalid JSON input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_text("invalid json")
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1003


def test_websocket_endpoint_missing_content():
    MockDatabase().rate_limit_records.count = 0
    # Test missing 'content' in input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        try:
            websocket.send_json(
                {
                    "history": [{"role": "user", "content": "Hi"}],
                }
            )
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_endpoint_missing_history():
    MockDatabase().rate_limit_records.count = 0
    # Test missing 'history' in input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Hello, how are you?",
            }
        )
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_endpoint_invalid_role_in_history():
    MockDatabase().rate_limit_records.count = 0
    # Test invalid 'role' in 'history'
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Hello, how are you?",
                "history": [{"role": "invalid", "content": "Hi"}],
            }
        )
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_stream_content_too_long():
    MockDatabase().rate_limit_records.count = 0
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        try:
            websocket.send_json(
                {
                    "content": "a" * 501,
                    "history": [{"role": "user", "content": "Hi"}],
                }
            )
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_stream_history_too_long():
    MockDatabase().rate_limit_records.count = 0
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Hello, how are you?",
                "history": [{"role": "user", "content": "Hi"}] * 51,
            }
        )
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_content_and_history_too_long():
    MockDatabase().rate_limit_records.count = 0
    # Test when both content and history are too long
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "a" * 50,
                "history": [{"role": "user", "content": "Hi"}] * 51,
            }
        )
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_endpoint_error_handling():
    MockDatabase().rate_limit_records.count = 0
    # Test error handling in agent stream
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Error",
                "history": [{"role": "user", "content": "Hi"}],
            }
        )
        try:
            response = websocket.receive_text()
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1011


def test_websocket_endpoint_valid_input_with_long_content():
    MockDatabase().rate_limit_records.count = 0
    # Test valid input with long content
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Test with long content",
                "history": [{"role": "user", "content": "Hi"}],
            }
        )
        response = ""
        while True:
            try:
                token = websocket.receive_text()
                data = json.loads(token)
                # Only process text type responses
                if data.get("type") == "text":
                    response += data["content"]
            except WebSocketDisconnect as e:
                assert e.code == 1000
                break
        assert response == "Hello, AI is answering here!"
