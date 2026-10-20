FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.lock .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements.lock
COPY app ./app
COPY bot ./bot
COPY migrations ./migrations
RUN useradd --uid 10001 --create-home catalog
USER catalog
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]

FROM runtime AS test
USER root
COPY requirements-dev.txt .
RUN --mount=type=cache,target=/root/.cache/pip pip install -r requirements-dev.txt
COPY tests ./tests
COPY pyproject.toml .
USER catalog
CMD ["python", "-m", "tests"]
