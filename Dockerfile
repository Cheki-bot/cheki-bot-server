FROM python:3.12-slim-bookworm AS base

FROM base AS builder
# Copiar uv desde la imagen oficial de Astral
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Configuración de uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Directorio de trabajo
WORKDIR /app

# Copiar solo los archivos necesarios para instalar dependencias
COPY uv.lock pyproject.toml /app/

# Instalar dependencias con uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project --no-dev

# Copiar el código de la aplicación
COPY . /app

# Instalar la aplicación
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-dev

# Etapa 3: Imagen final (sin dependencias de construcción)
FROM base
# Copiar la aplicación desde la etapa de construcción
COPY --from=builder /app /app

WORKDIR /app

# Configurar el PATH para usar uv
ENV PATH="/app/.venv/bin:$PATH"

# Ejectar comandos necesarios
RUN python commands.py --download
RUN python commands.py --create

# Exponer el puerto de la aplicación
EXPOSE 8000

# Comando para ejecutar la aplicación
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]