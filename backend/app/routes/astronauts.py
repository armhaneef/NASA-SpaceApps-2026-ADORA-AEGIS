"""Astronaut profile CRUD endpoints."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.schemas.astronaut import AstronautCreate, AstronautRead, AstronautUpdate
from app.services import astronaut_service as service

router = APIRouter(prefix="/astronauts", tags=["astronauts"])
Database = Annotated[Session, Depends(get_session)]


@router.post("", response_model=AstronautRead, status_code=201)
def create_astronaut(payload: AstronautCreate, session: Database):
    return service.create_astronaut(session, payload)


@router.get("", response_model=list[AstronautRead])
def list_astronauts(session: Database, limit: int = Query(100, ge=1, le=1000),
                    offset: int = Query(0, ge=0)):
    return service.list_astronauts(session, limit, offset)


@router.get("/{astronaut_id}", response_model=AstronautRead)
def get_astronaut(astronaut_id: str, session: Database):
    return service.get_astronaut(session, astronaut_id)


@router.patch("/{astronaut_id}", response_model=AstronautRead)
def update_astronaut(astronaut_id: str, payload: AstronautUpdate, session: Database):
    return service.update_astronaut(session, astronaut_id, payload)


@router.delete("/{astronaut_id}", status_code=204)
def delete_astronaut(astronaut_id: str, session: Database) -> Response:
    service.delete_astronaut(session, astronaut_id)
    return Response(status_code=204)
