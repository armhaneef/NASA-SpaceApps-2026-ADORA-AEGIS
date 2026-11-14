"""Explicit analysis execution and side-effect-free retrieval."""

from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.schemas.analysis import AnalysisRead, AnalysisRequest
from app.services import analysis_service as service
from app.services.ml_adapter import MLAdapter, get_ml_adapter

router = APIRouter(prefix="/health/{astronaut_id}/analyses", tags=["ML analyses"])
Database = Annotated[Session, Depends(get_session)]


@router.post("", response_model=AnalysisRead, status_code=201)
def create_analysis(astronaut_id: str, payload: AnalysisRequest, session: Database,
                    adapter: Annotated[MLAdapter, Depends(get_ml_adapter)]):
    return service.create_analysis(session, astronaut_id, payload, adapter)


@router.get("", response_model=list[AnalysisRead])
def list_analyses(astronaut_id: str, session: Database,
                  limit: int = Query(100, ge=1, le=1000), offset: int = Query(0, ge=0)):
    return service.list_analyses(session, astronaut_id, limit, offset)


@router.get("/latest", response_model=AnalysisRead)
def latest_analysis(astronaut_id: str, session: Database):
    from app.services.errors import NotFoundError

    records = service.list_analyses(session, astronaut_id, 1, 0)
    if not records:
        raise NotFoundError("No stored analysis for this astronaut")
    return records[0]


@router.get("/{analysis_id}", response_model=AnalysisRead)
def get_analysis(astronaut_id: str, analysis_id: Annotated[int, Path(ge=1)], session: Database):
    return service.get_analysis(session, astronaut_id, analysis_id)
