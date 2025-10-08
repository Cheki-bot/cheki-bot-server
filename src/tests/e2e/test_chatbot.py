import json

from fastapi import WebSocketDisconnect
from fastapi.testclient import TestClient

from src.agent.agent import AsyncAgent
from src.agent.schemas import AgentResponseChunk
from src.api.app import create_app
from src.api.dependencies.injectables import get_agent


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
                data = json.loads(token)
                # Only process text type responses
                if data.get("type") == "text":
                    response += data["content"]
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
            data = json.loads(response)
            assert data.get("type") == "error"
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
            data = json.loads(response)
            assert data.get("type") == "error"
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
            data = json.loads(response)
            assert data.get("type") == "error"
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
            data = json.loads(response)
            assert data.get("type") == "error"
        except WebSocketDisconnect as e:
            assert e.code == 1008


def test_stream_content_too_long():
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
