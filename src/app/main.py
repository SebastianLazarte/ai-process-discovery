import logging
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, RedirectResponse

from app import __version__
from app.api.routes import analyses, processes, system, web
from app.core.config import Settings, get_settings
from app.core.db import build_engine, init_db, session_factory
from app.core.errors import AppError
from app.core.logging import configure_logging
from app.domain.errors import DomainValidationError
from app.llm.provider import LLMProvider
from app.llm.providers import build_provider

logger = logging.getLogger(__name__)

# ADR 0009: the API lives under /api. Until 2.0.0 (RS-80) every route also answers at the
# root, for the vanilla client. The schema documents each path once, relative to /api.
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

    for router in (system.router, processes.router, analyses.router):
        app.include_router(router, prefix=API_PREFIX, include_in_schema=False)
        app.include_router(router)

    for old, new in LEGACY_DOCS.items():
        app.add_api_route(old, _redirect_to(new), methods=["GET"], include_in_schema=False)

    web.mount_web_client(app, settings.web_dir)
    return app


def _redirect_to(target: str) -> Callable[[], RedirectResponse]:
    def redirect() -> RedirectResponse:
        return RedirectResponse(target, status_code=308)

    return redirect


app = create_app()
