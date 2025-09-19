
FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY data-ingestion/ ./data-ingestion
COPY optibet_lib/ ./optibet_lib
RUN uv sync --package data-ingestion

WORKDIR /app/data-ingestion
EXPOSE 80

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
