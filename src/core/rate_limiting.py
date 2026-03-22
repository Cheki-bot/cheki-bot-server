from datetime import UTC, datetime, timedelta
from typing import Optional, Tuple

from pymongo.database import Database


class RateLimiter:
    def __init__(self, db: Database, max_requests: int = 10, window_minutes: int = 1):
        """
        Inicializa el limitador de tasa.

        Args:
            db: Conexión a la base de datos MongoDB
            max_requests: Número máximo de solicitudes permitidas
            window_minutes: Ventana de tiempo en minutos
        """
        self.db = db
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.collection = self.db.rate_limit_records

        # Inicializar índices si no existen
        self._ensure_indexes()

    def _ensure_indexes(self):
        """
        Crea los índices necesarios para el rate limiting si no existen.
        """
        # Obtener los índices existentes
        existing_indexes = {index for index in self.collection.index_information()}

        # Crear índice para búsqueda rápida por identifier, endpoint y timestamp
        if "rate_limit_lookup_idx" not in existing_indexes:
            self.collection.create_index(
                [("identifier", 1), ("endpoint", 1), ("timestamp", 1)],
                name="rate_limit_lookup_idx",
                background=True,
            )

        # Crear índice TTL para eliminar automáticamente registros antiguos
        if "rate_limit_ttl_idx" not in existing_indexes:
            self.collection.create_index(
                "timestamp", expireAfterSeconds=120, name="rate_limit_ttl_idx", background=True
            )

    def is_allowed(self, identifier: str, endpoint: str) -> Tuple[bool, Optional[str]]:
        """
        Verifica si una solicitud está permitida.

        Args:
            identifier: Identificador único del cliente (IP, user ID, etc.)
            endpoint: Endpoint que se está accediendo

        Returns:
            Tuple con (permitido: bool, mensaje_error: str opcional)
        """
        now = datetime.now(UTC)
        window_start = now - timedelta(minutes=self.window_minutes)

        # Contar solicitudes recientes
        request_count = self.collection.count_documents(
            {"identifier": identifier, "endpoint": endpoint, "timestamp": {"$gte": window_start}}
        )

        if request_count >= self.max_requests:
            return (
                False,
                f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_minutes} minute(s).",
            )

        # Registrar la nueva solicitud
        self.collection.insert_one(
            {"identifier": identifier, "endpoint": endpoint, "timestamp": now}
        )

        return True, None
