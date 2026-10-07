from collections.abc import Iterator
from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.orm import Session

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


SessionDep = Annotated[Session, Depends(get_session)]
ProviderDep = Annotated[LLMProvider, Depends(get_provider)]


def get_process_service(session: SessionDep) -> ProcessService:
    return ProcessService(session)


def get_analysis_service(session: SessionDep, provider: ProviderDep) -> AnalysisService:
    return AnalysisService(session, provider)


ProcessServiceDep = Annotated[ProcessService, Depends(get_process_service)]
AnalysisServiceDep = Annotated[AnalysisService, Depends(get_analysis_service)]
