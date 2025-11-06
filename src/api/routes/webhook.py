from fastapi import APIRouter

from src.api.dependencies import IndexingServiceDep
from src.api.schemas import RecordData

webhook_router = APIRouter(prefix="/webhook", tags=["Webhook"])


@webhook_router.post("/")
async def webhook_handler(data: RecordData, service: IndexingServiceDep):
    return await service.index_record(data=data)
