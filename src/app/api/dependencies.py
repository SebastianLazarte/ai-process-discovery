from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.llm.provider import LLMProvider
from app.services.analysis_service import AnalysisService
from app.services.process_service import ProcessService


def get_session(request: Request) -> Iterator[Session]:
    session: Session = request.app.state.session_factory()
    try:
        yield session
    finally:
        session.close()


def get_provider(request: Request) -> LLMProvider:
    provider: LLMProvider = request.app.state.llm_provider
    return provider


def get_app_settings(request: Request) -> Settings:
    settings: Settings = request.app.state.settings
    return settings


SessionDep = Annotated[Session, Depends(get_session)]
ProviderDep = Annotated[LLMProvider, Depends(get_provider)]
SettingsDep = Annotated[Settings, Depends(get_app_settings)]


def get_process_service(session: SessionDep) -> ProcessService:
    return ProcessService(session)


def get_analysis_service(
    session: SessionDep, provider: ProviderDep, settings: SettingsDep
) -> AnalysisService:
    return AnalysisService(session, provider, llm_daily_limit=settings.llm_daily_limit)


ProcessServiceDep = Annotated[ProcessService, Depends(get_process_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
