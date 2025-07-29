from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorStoreManager(ABC):
    @abstractmethod
    def retrieve_context(self, query: str) -> str:
        pass

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]) -> None:
        pass

    @abstractmethod
    def delete_documents(self, document_ids: List[str]) -> None:
        pass
