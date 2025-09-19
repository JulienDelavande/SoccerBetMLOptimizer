
FROM python:3.10-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY pipelines/ ./pipelines
COPY optibet_lib/ ./optibet_lib
RUN uv sync --package pipelines

WORKDIR /app/pipelines
EXPOSE 80

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]
