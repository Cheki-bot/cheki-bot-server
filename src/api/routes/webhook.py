from fastapi import APIRouter

from src.api.dependencies import IndexingServiceDep
from src.api.dependencies.injectables import CurrentUserDep
from src.api.schemas import RecordData

webhook_router = APIRouter(prefix="/webhook", tags=["Webhook"])


@webhook_router.post("/")
async def webhook_handler(
    data: RecordData,
    service: IndexingServiceDep,
    _: CurrentUserDep,
) -> list[str]:
    """Handle incoming webhook data and index the record.

    This endpoint receives webhook data, validates it, and indexes the record
    using the indexing service. The service processes the data based on its
    collection type and stores it in the vector database for later retrieval
    and semantic search capabilities.

    Args:
        data: The record data to be indexed, including collection name and ID
        service: The indexing service dependency for handling the indexing
        _: The current user dependency (used for authentication/authorization)

    Returns:
        The result of the indexing operation, which includes the IDs of the
        documents that were added to the vector database
    """
    return await service.index_record(data=data)
