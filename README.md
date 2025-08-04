# Cheki-Bot Server

A sophisticated conversational AI system built with Python, FastAPI, and LangChain Core, designed to provide intelligent chatbot capabilities using various language models including Nebius and OpenAI.

## Features

- **Multi-LLM Support**: Integrates with Nebius and OpenAI language models
- **Vector Database Integration**: Uses ChromaDB for context management and retrieval-augmented generation (RAG)
- **Modular Architecture**: Agent-based design for easy extension and maintenance
- **Async/Await Support**: Non-blocking operations for better performance
- **FastAPI Backend**: High-performance web framework with automatic API documentation
- **Conversation Context Management**: Persistent conversation handling with context managers

## Project Structure

```sh
.
├── .env.example              # Environment variables template
├── Dockerfile                # Docker configuration
├── README.md                 # This file
├── main.py                   # Entry point for the application
├── pyproject.toml            # Dependencies and project configuration
├── scripts/                  # Utility scripts
│   └── setup_db.py           # Database setup script
├── src/
│   ├── api/                  # API layer with routes and app setup
│   │   ├── app.py            # FastAPI application factory
│   │   ├── routes/           # API endpoints
│   │   └── models.py         # Pydantic models for API requests/responses
│   ├── agents/               # Agent implementations for different LLMs
│   │   ├── nebius_agent.py   # Nebius LLM agent
│   │   ├── openai_agent.py   # OpenAI LLM agent
│   │   └── context_managers/ # Context management components
│   ├── core/                 # Core system components
│   │   ├── agent.py          # Base Agent class
│   │   └── entities/         # Core entity classes
│   └── tests/                # Test suite
└── docs/                     # Documentation files
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

2. Syncronize environment and install dependencies:

    ```bash
    uv sync
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Set up environment variables:

    ```bash
    cp .env.example .env
    # Edit .env with your actual API keys and configurations
    ```

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

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello, how are you?"}'
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
uv run uvicorn main:app --reaload
```

Run end-to-end tests:

```bash
uv run pytest
```

## Development Workflow

1. Follow PEP 8 coding standards
2. Use type hints throughout the codebase
3. Write comprehensive docstrings
4. Add unit tests for new functionality
5. Run linters and formatters before committing

## Contributing

1. Create a feature branch
2. Commit your changes
3. Push to the branch
4. Create a pull request

## Acknowledgements

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Uses [LangChain Core](https://python.langchain.com/)
- Vector storage powered by [ChromaDB](https://docs.trychroma.com/)

## Contact

For support or questions, please open an issue in the repository.
