# One image for the API and the Streamlit UI; compose.yaml picks the command.
FROM python:3.12-slim AS base

COPY --from=ghcr.io/astral-sh/uv:0.11.9 /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Dependencies first, so code changes do not invalidate this layer.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --all-extras --no-install-project

COPY src ./src
COPY ui ./ui
RUN uv sync --locked --no-dev --all-extras

RUN useradd --create-home --uid 10001 app && mkdir -p /data && chown app /data
USER app

ENV DATABASE_URL=sqlite:////data/apd.sqlite \
    LLM_PROVIDER=fake

EXPOSE 8000 8501

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://localhost:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
