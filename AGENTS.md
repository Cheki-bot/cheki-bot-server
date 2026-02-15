# Agent Instructions for Checki-Bot Backend

## Development Environment Setup

**Install dependencies:**
```bash
uv sync
```

**Activate virtual environment:**
```bash
source .venv/bin/activate  # Linux/Mac
# On Windows: venv\Scripts\activate
```

**Run the development server:**
```bash
python main.py
```

## Build, Lint, and Test Commands

### Testing

**Run all tests:**
```bash
uv run pytest
```

**Run specific test file:**
```bash
uv run pytest src/tests/test_agent.py -v
```

**Run specific test function:**
```bash
uv run pytest src/tests/test_agent.py::test_stream_success -v
```

**Run only async tests:**
```bash
uv run pytest -m asyncio
```

**Run end-to-end tests:**
```bash
uv run pytest src/tests/e2e/
```

**Run tests with coverage:**
```bash
uv run pytest --cov=src --cov-report=html
```

### Code Quality

**Lint with ruff:**
```bash
uv run ruff check .
```

**Format code with ruff:**
```bash
uv run ruff format .
```

**Check for linting issues:**
```bash
uv run ruff check --fix .
```

**Check mypy type hints:**
```bash
uv run mypy src/
```

**Type checking with mypy:**
```bash
uv run mypy src/ --strict
```

**Verify all formatting:**
```bash
uv run ruff check --output-format=concise
```

### Docker

**Run with Docker:**
```bash
docker-compose up
```

**Run specific services:**
```bash
docker-compose up -d chroma_db
```

**Stop services:**
```bash
docker-compose down
```

## Code Style Guidelines

### Imports

**Import order (PEP 8):**

1. Standard library imports
2. Third-party imports
3. Local application imports

Example:
```python
import asyncio
from typing import Optional

from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from src.agent.agent import AsyncAgent
from src.agent.schemas import TopicSelection
```

**Import placement:**
- Put imports at the top of the file
- Group imports by their source (stdlib, third-party, local)
- After `package imports`, put blank line before local imports

**Specific imports:**
```python
# Standard library
import os
import sys
from typing import List, Optional

# Third-party
from fastapi import FastAPI, Depends, HTTPException
from langchain_core.messages import HumanMessage

# Local
from src.agent.agent import AsyncAgent
from src.agent.schemas import TopicSelection
```

### Formatting

**Line length:**
- Maximum 100 characters (configured in pyproject.toml)

**Whitespace:**
- Two spaces for indentation
- Single blank line between top-level functions and classes
- Single blank line between logical sections within a function
- No trailing whitespace

**Parentheses:**
- Use parentheses for multi-line statements
- Keep function calls and expressions readable

```python
# Good
def example_function(
    param1: str,
    param2: int,
    param3: Optional[List[str]] = None,
) -> bool:
    return param1 == param2

# Good
result = (
    some_value
    + other_value
    + third_value
)

# Bad
def example_function(param1: str, param2: int) -> bool:
    return param1 == param2
```

### Type Hints

**Always use type hints:**
```python
def process_data(data: str, timeout: int = 30) -> dict[str, str]:
    """Process input data with timeout."""
    return {"processed": data}
```

**Use typing module:**
```python
from typing import List, Dict, Optional, Union, Callable
from collections.abc import AsyncIterable

def handle_list(items: List[str]) -> Optional[str]:
    """Process a list of strings."""
    pass

async def fetch_data() -> AsyncIterable[str]:
    """Yield data asynchronously."""
    pass
```

**Complex type annotations:**
```python
from typing import TypeVar, Generic

T = TypeVar("T")

class Storage(Generic[T]):
    def __init__(self, data: T) -> None:
        self.data = data
```

**Pydantic models:**
```python
from pydantic import BaseModel, Field, validator

class User(BaseModel):
    name: str
    email: str
    age: int = Field(ge=18, le=120)

    @validator("email")
    def validate_email(cls, v: str) -> str:
        return v.lower()
```

### Naming Conventions

**Classes:**
- Use PascalCase
- Singular nouns
- Clear and descriptive

```python
class AsyncAgent:
    """Abstract base class for agents."""
    pass

class ChromaContextManager:
    """Context manager for ChromaDB."""
    pass
```

**Functions and methods:**
- Use snake_case
- Verbs as prefix (get, set, process, validate)
- Concise but descriptive

```python
async def build_topic_context(topic_selections: List) -> str:
    """Build context for topic."""
    pass

async def validate_input(data: dict) -> bool:
    """Validate input data."""
    pass

def get_config() -> dict:
    """Get configuration."""
    pass
```

**Variables:**
- Use snake_case
- Lowercase with underscores
- Meaningful and descriptive

```python
chat_model: BaseChatModel
context_manager: ContextManager
api_key: SecretStr
max_tokens: int
retry_count: int = 3
```

**Constants:**
- Use UPPER_CASE
- Single words or clear acronyms

```python
DEFAULT_TIMEOUT = 30
MAX_RETRIES = 3
API_VERSION = "v1"
DATABASE_URI = "mongodb://localhost:27017"
```

**Private members:**
- Single underscore prefix (`_variable`)
- Protected members (`_ProtectedVariable`)
- Double underscore prefix (`__PrivateVariable`)

```python
class Example:
    _internal_state = None
    _protected_method():
        pass

    __private_var = "secret"
```

**Async/Await patterns:**
```python
async def fetch_data() -> str:
    """Fetch data asynchronously."""
    data = await some_async_function()
    return data

# Usage
result = await fetch_data()
```

### Error Handling

**Try-except blocks:**
```python
try:
    result = await process_request(request)
except specific_error as e:
    logger.error(f"Error: {e}")
    raise
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    raise
```

**Raising exceptions:**
```python
if not data:
    raise ValueError("Data cannot be empty")

if condition:
    raise PermissionError("Access denied")
```

**Exception propagation:**
```python
async def process_item(item: str) -> None:
    """Process an item."""
    try:
        result = await validate_item(item)
        await save_item(result)
    except Exception:
        raise
```

**Specific exception handling:**
```python
from fastapi import HTTPException, status

try:
    user = await get_user(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
except DatabaseError as e:
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Database error"
    )
```

### Documentation

**Docstrings:**
- Use triple quotes `"""` for docstrings
- Include brief description, parameters, returns, and examples
- Keep them concise

```python
class Agent:
    """Base class for all agents in the system.

    This class provides the foundational structure for agents that interact with
    language models and manage context.

    Attributes:
        chat_model: The language model for generating responses.
        context_manager: Manager for context retrieval.

    Example:
        >>> agent = Agent(chat_model=model, context_manager=manager)
        >>> response = await agent.invoke("Hello")
    """
    pass

async def process_data(data: str) -> dict:
    """Process input data.

    Args:
        data: Input string to process.

    Returns:
        Processed dictionary with results.

    Raises:
        ValueError: If input is empty.
    """
    pass
```

**Type hints in docstrings:**
```python
async def get_user(user_id: int) -> Optional[User]:
    """Retrieve user by ID.

    Args:
        user_id: The unique identifier for the user.

    Returns:
        User object if found, None otherwise.

    Example:
        >>> user = await get_user(123)
        >>> print(user.name)
    """
    pass
```

### Async Code Patterns

**Async functions:**
```python
async def fetch_data(url: str) -> str:
    """Fetch data from URL asynchronously."""
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

**Async context managers:**
```python
async with pool.acquire() as connection:
    result = await connection.execute("SELECT * FROM users")
```

**Async iteration:**
```python
async for item in async_iterator():
    process(item)

async def async_iterator():
    """Yield items asynchronously."""
    yield item
    yield another_item
```

**Parallel execution:**
```python
results = await asyncio.gather(
    fetch_data(url1),
    fetch_data(url2),
    fetch_data(url3),
)
```

### Code Organization

**File structure:**
```python
# Imports section
from typing import List, Optional
import asyncio

# Constants
MAX_RETRIES = 3

# Type definitions
class MyClass:
    """Class definition."""
    pass

# Function definitions
async def my_function() -> None:
    """Function definition."""
    pass

# Main execution
if __name__ == "__main__":
    asyncio.run(main())
```

**Module organization:**
```python
# src/api/app.py
from fastapi import FastAPI

# Import function
def create_app() -> FastAPI:
    """Create FastAPI app."""
    app = FastAPI()
    return app

# Export main function
__all__ = ["create_app"]
```

## Testing Guidelines

**Test structure:**
```python
import pytest
from unittest.mock import AsyncMock

from src.agent.agent import AsyncAgent

@pytest.fixture
def mock_model():
    """Create mock model."""
    return AsyncMock()

@pytest.mark.asyncio
async def test_example(mock_model):
    """Test example function."""
    result = await function(mock_model)
    assert result is not None
```

**Mock usage:**
```python
from unittest.mock import AsyncMock, MagicMock, patch

mock_object = AsyncMock()
mock_object.return_value = "test"
result = mock_object()

# Patch external dependencies
with patch("module.function", return_value="mocked"):
    result = await process_data()
```

**Assertion patterns:**
```python
assert result == expected
assert isinstance(result, ExpectedType)
assert result is not None
assert any(condition for item in items)
```

## Security Best Practices

**Sensitive data:**
```python
from pydantic import SecretStr

class Settings(BaseModel):
    api_key: SecretStr
    password: SecretStr
```

**Environment variables:**
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")
    api_key: str
```

**Input validation:**
```python
from pydantic import BaseModel, Field, validator

class UserInput(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: str

    @validator("email")
    def validate_email(cls, v: str) -> str:
        return v.lower()
```

**Rate limiting:**
```python
from fastapi import Request, Response, HTTPException

class RateLimiter:
    """Rate limiter for API endpoints."""

    def __init__(self, max_requests: int = 100):
        self.max_requests = max_requests
```

## Common Patterns

**FastAPI dependency injection:**
```python
from fastapi import Depends

async def get_current_user(request: Request):
    """Get current user from request."""
    return request.state.user

@router.get("/protected")
async def protected_route(
    user: User = Depends(get_current_user),
):
    """Protected route."""
    return {"user": user}
```

**Logger usage:**
```python
import logging

logger = logging.getLogger(__name__)

logger.info("Processing request")
logger.warning("Unusual activity detected")
logger.error("Failed to process request")
```

**Configuration management:**
```python
from src.core.config import settings

# Access configuration
db_url = settings.db.uri
timeout = settings.timeout
```

## Environment Configuration

**Environment variables:**
```bash
# .env file
ALLOW_ORIGINS="http://localhost:5173"
LLM_PROVIDER="openai"
LLM_MODEL="gpt-3.5-turbo"
LLM_API_KEY="sk-..."
CHROMA_PERSIST_DIRECTORY="chroma_db"
```

**Python environment:**
```bash
# Use Python version specified in .python-version
python --version  # Should match 3.12+

# Create virtual environment with uv
uv sync
```

**Project-specific rules:**
- Follow the existing code style
- Use type hints for all functions
- Add docstrings for public APIs
- Write tests for new functionality
- Run linters before committing
- Ensure all tests pass