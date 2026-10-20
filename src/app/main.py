import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI, Request
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse, RedirectResponse

from app import __version__
from app.api.routes import analyses, processes, system
from app.core.config import Settings, get_settings
from app.core.db import build_engine, init_db, session_factory
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.domain.errors import DomainValidationError
from app.llm.provider import LLMProvider
from app.llm.providers import build_provider

logger = logging.getLogger(__name__)

# ADR 0009, ADR 0016: the API lives under /api and the root belongs to the Next.js client.
# The schema documents each path relative to /api. Old docs URLs redirect there (RS-80).
API_PREFIX = "/api"
LEGACY_DOCS = {"/docs": "/api/docs", "/redoc": "/api/redoc", "/openapi.json": "/api/openapi.json"}


def create_app(settings: Settings | None = None, provider: LLMProvider | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings.database_url)
        if settings.create_schema_on_startup:
            init_db(engine)
        app.state.engine = engine
        app.state.session_factory = session_factory(engine)
        app.state.llm_provider = provider or build_provider(settings)
        logger.info(
            "app_started",
            extra={"llm_provider": app.state.llm_provider.name, "db": engine.dialect.name},
        )
        yield
        engine.dispose()

    app = FastAPI(
        title="AI Process Discovery & Automation Planner",
        version=__version__,
        description=(
            "Quantifies a business process, scores automation suitability with explicit "
            "rules, enriches it with an LLM behind a validated contract, and produces an "
            "automation blueprint. Deterministic first: the LLM never produces a number."
        ),
        lifespan=lifespan,
        servers=[{"url": API_PREFIX}],
        docs_url=f"{API_PREFIX}/docs",
        redoc_url=f"{API_PREFIX}/redoc",
        openapi_url=f"{API_PREFIX}/openapi.json",
    )
    app.state.settings = settings

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.message, "code": exc.code}, status_code=exc.status_code)

    @app.exception_handler(DomainValidationError)
    async def _domain_error(_: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(
            {"detail": exc.message, "field": exc.field, "code": "domain_validation"},
            status_code=422,
        )

    api = APIRouter()
    for router in (system.router, processes.router, analyses.router):
        api.include_router(router)
    app.include_router(api, prefix=API_PREFIX, include_in_schema=False)
    app.openapi = _schema_relative_to_api(app, api)  # type: ignore[method-assign]

    for old, new in LEGACY_DOCS.items():
        app.add_api_route(old, _redirect_to(new), methods=["GET"], include_in_schema=False)

    return app


def _schema_relative_to_api(app: FastAPI, api: APIRouter) -> Callable[[], dict[str, Any]]:
    """Document each path once, relative to the `servers` entry /api."""

    def openapi() -> dict[str, Any]:
        if app.openapi_schema is None:
            app.openapi_schema = get_openapi(
                title=app.title,
                version=app.version,
                description=app.description,
                routes=api.routes,
                servers=app.servers,
            )
        return app.openapi_schema

    return openapi


def _redirect_to(target: str) -> Callable[[], RedirectResponse]:
    def redirect() -> RedirectResponse:
        return RedirectResponse(target, status_code=301)

    return redirect


app = create_app()
