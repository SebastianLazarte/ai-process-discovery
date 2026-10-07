import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

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


def create_app(settings: Settings | None = None, provider: LLMProvider | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine = build_engine(settings.database_url)
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
    )

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse({"detail": exc.message, "code": exc.code}, status_code=exc.status_code)

    @app.exception_handler(DomainValidationError)
    async def _domain_error(_: Request, exc: DomainValidationError) -> JSONResponse:
        return JSONResponse(
            {"detail": exc.message, "field": exc.field, "code": "domain_validation"},
            status_code=422,
        )

    app.include_router(system.router)
    app.include_router(processes.router)
    app.include_router(analyses.router)
    return app


app = create_app()
