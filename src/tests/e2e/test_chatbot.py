from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from src.api.app import create_app
from src.api.deps import get_agent
from src.core.agent import Agent


class MockAgent(Agent):
    def __init__(self):
        pass

    async def stream(self, query: str, history):
        if query == "Error":
            raise Exception("Error processing query")
        chunks = ["Hello, ", "AI is ", "answering ", "here!"]
        for chunk in chunks:
            yield chunk


app = create_app()
app.dependency_overrides[get_agent] = lambda: MockAgent()


client = TestClient(app)


def test_websocket_endpoint_valid_input():
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
                response += token
            except WebSocketDisconnect as e:
                assert e.code == 1000
                break
        assert response == "Hello, AI is answering here!"


def test_websocket_endpoint_invalid_json():
    # Test invalid JSON input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_text("invalid json")
        try:
            response = websocket.receive_text()
            assert "ERROR" in response
        except WebSocketDisconnect as e:
            assert e.code == 1003


def test_websocket_endpoint_missing_content():
    # Test missing 'content' in input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        try:
            websocket.send_json(
                {
                    "history": [{"role": "user", "content": "Hi"}],
                }
            )
            response = websocket.receive_text()
            assert "ERROR" in response
            assert "content" in response
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_endpoint_missing_history():
    # Test missing 'history' in input
    with client.websocket_connect("/api/chatbot/ws") as websocket:
        websocket.send_json(
            {
                "content": "Hello, how are you?",
            }
        )
        try:
            response = websocket.receive_text()
            assert "ERROR" in response
            assert "history" in response
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_websocket_endpoint_invalid_role_in_history():
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
            assert "ERROR" in response
            assert "role" in response
        except WebSocketDisconnect as e:
            assert e.code == 1008
