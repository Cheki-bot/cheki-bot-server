# Cheki-Bot Server

A sophisticated conversational AI system built with Python, FastAPI, and LangChain Core, designed to provide intelligent chatbot capabilities using various language models including Nebius and OpenAI.

## Features

- **Multi-LLM Support**: Integrates with Nebius and OpenAI language models
- **Vector Database Integration**: Uses ChromaDB for context management and retrieval-augmented generation (RAG)
- **Modular Architecture**: Agent-based design for easy extension and maintenance
- **Async/Await Support**: Non-blocking operations for better performance
- **FastAPI Backend**: High-performance web framework with automatic API documentation
- **Conversation Context Management**: Persistent conversation handling with context managers
- **End-to-End Testing**: Comprehensive test suite with unit and integration tests
- **Docker Support**: Containerized deployment with Docker Compose

## Project Structure

```sh
.
├── .env.example              # Environment variables template
├── .github/                  # GitHub workflows
│   ├── workflows/
│   │   ├── pytest.yml        # Test workflow
│   │   └── ruff-linter.yml   # Linting workflow
├── Dockerfile                # Docker configuration
├── README.md                 # This file
├── commands.py               # Utility commands
├── docker-compose.yml        # Docker Compose configuration
├── main.py                   # Entry point for the application
├── pyproject.toml            # Dependencies and project configuration
├── scripts/                  # Utility scripts
│   └── create_vectordb.py    # Database setup script
├── src/
│   ├── __init__.py           # Package initialization
│   ├── agents/               # Agent implementations for different LLMs
│   │   ├── __init__.py       # Package initialization
│   │   ├── nebius_agent.py   # Nebius LLM agent
│   │   ├── openai_agent.py   # OpenAI LLM agent
│   │   └── context_managers/ # Context management components
│   │       ├── __init__.py   # Package initialization
│   │       ├── chroma_cm.py  # ChromaDB-based context manager
│   │       └── prompts.py    # Prompt templates
│   ├── api/                  # API layer with routes and app setup
│   │   ├── __init__.py       # Package initialization
│   │   ├── app.py            # FastAPI application factory
│   │   ├── deps.py           # Dependency injection
│   │   ├── models.py         # Pydantic models for API requests/responses
│   │   └── routes/           # API endpoints
│   │       ├── __init__.py   # Package initialization
│   │       └── chatbot.py    # Chat endpoint implementation
│   ├── core/                 # Core system components
│   │   ├── __init__.py       # Package initialization
│   │   ├── agent.py          # Base Agent class
│   │   ├── consts.py         # Constants
│   │   └── entities/         # Core entity classes
│   │       ├── __init__.py   # Package initialization
│   │       ├── context_manager.py  # Base context manager interface
│   │       └── vector_store.py     # Base vector store interface
│   ├── settings.py           # Configuration management
│   ├── tests/                # Test suite
│   │   ├── __init__.py       # Package initialization
│   │   ├── test_agent.py     # Unit tests for agents
│   │   └── e2e/              # End-to-end tests
│   │       ├── __init__.py   # Package initialization
│   │       └── test_chatbot.py # End-to-end chatbot tests
│   └── tools/                # Utility tools
│       ├── __init__.py       # Package initialization
└── docs/                     # Documentation files
    └── terminal_commands.md  # Terminal commands documentation
```

## Prerequisites

- Python 3.12+
- uv package manager
- Docker (optional)

## Installation

1. Clone the repository:

    ```bash
    git clone <repository-url>
    cd cheki-bot-server
    ```

    *Clones the repository from the provided URL and enters the project directory.*

2. Synchronize environment and install dependencies:

    ```bash
    uv sync # This creates the virtual environment and installs the project dependencies
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

    *Synchronizes the environment and installs the necessary project dependencies.*
    **Note**: Ensure `uv` is installed and available in your PATH. If not installed yet, install it via: [https://github.com/astral-sh/uv](https://docs-astral-sh.translate.goog/uv/?_x_tr_sl=en&_x_tr_tl=es&_x_tr_hl=es&_x_tr_pto=tc)

3. Set up environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your actual API keys and configurations
    ```

    *Copies the example environment file and configures the actual API keys and settings.*

## Configuration

Create a `.env` file based on the provided `.env.example`:

- `ALLOW_ORIGINS`: CORS allowed origins (default: <http://localhost:5173>)
- `LLM_PROVIDER`: Language model provider (default: openai)
- `LLM_MODEL`: LLM model to use (default: gpt-3.5-turbo)
- `LLM_EMB_MODEL`: LLM embedding model (default: text-embedding-3-small)
- `LLM_API_KEY`: Your LLM API key (required)
- `LLM_TEMPERATURE`: Sampling temperature for LLM responses (default: 0.7)
- `LLM_MAX_TOKENS`: Maximum tokens in LLM responses (default: 1000)
- `LLM_CONTEXT_LENGTH`: Maximum context length for LLM (default: 32768)
- `CHROMA_PERSIST_DIRECTORY`: ChromaDB persistence directory (default: chroma_db)

## Running the Application

### Development Mode

```bash
python main.py
```

### Using Docker

```bash
docker-compose up
```

The API will be available at `http://localhost:8000`.

## API Documentation

The system includes automatic API documentation:

- OpenAPI specification: `http://localhost:8000/docs`
- ReDoc interface: `http://localhost:8000/redoc`

## Usage Examples

### Chat Endpoint

The chatbot provides two endpoints:

1. `POST /chatbot/telegram_webhook` - For handling Telegram webhook updates
2. `GET /chatbot/ws` - For real-time WebSocket chat interactions

#### 1. POST `/chatbot/telegram_webhook`

Send a POST request to handle Telegram webhook updates:

```bash
# POST endpoint for chat messages
curl -X POST "http://localhost:8000/api/chatbot/telegram_webhook" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, how are you?", "history": []}'
```

#### 2. GET `/api/chatbot/ws`

Open a WebSocket connection for real-time chat interactions:

```bash
# WebSocket endpoint for real-time chat
curl -X GET "ws://localhost:8000/api/chatbot/ws"
```

### Health Check

```bash
curl http://localhost:8000/health
```

## Core Components

### Agents

- `NebiusAgent`: Implements Nebius LLM integration
- `OpenAIAgent`: Implements OpenAI GPT model integration

### Context Managers

- `ChromaCM`: ChromaDB-based context manager for semantic search
- Handles conversation history and retrieval of relevant information

### Core Classes

- `Agent`: Base class for all agent implementations
- `BaseEntity`: Base entity for conversation data structures

## Testing

Run unit tests:

```bash
uv run pytest src/tests/test_agent.py
```

Run end-to-end tests:

```bash
uv run pytest src/tests/e2e/
```

Run all tests:

```bash
uv run pytest
```

## Development Workflow

1. Follow PEP 8 coding standards
2. Use type hints throughout the codebase
3. Write comprehensive docstrings
4. Add unit tests for new functionality
5. Run linters and formatters before committing
6. Ensure all tests pass before merging

## Acknowledgements

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Uses [LangChain Core](https://python.langchain.com/)
- Vector storage powered by [ChromaDB](https://docs.trychroma.com/)

## Contact

For support or questions, please open an issue in the repository.
