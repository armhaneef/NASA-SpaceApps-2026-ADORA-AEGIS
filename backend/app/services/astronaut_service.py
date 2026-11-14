"""Astronaut persistence operations."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.models import Astronaut
from app.schemas.astronaut import AstronautCreate, AstronautUpdate
from app.services.errors import ConflictError, NotFoundError


def get_astronaut(session: Session, astronaut_id: str) -> Astronaut:
    astronaut = session.get(Astronaut, astronaut_id)
    if astronaut is None:
        raise NotFoundError("Astronaut not found")
    return astronaut


def list_astronauts(session: Session, limit: int, offset: int):
    return session.scalars(select(Astronaut).order_by(Astronaut.astronaut_id)
                           .limit(limit).offset(offset)).all()


def create_astronaut(session: Session, payload: AstronautCreate) -> Astronaut:
    astronaut = Astronaut(**payload.model_dump())
    session.add(astronaut)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Astronaut ID already exists") from exc
    session.refresh(astronaut)
    return astronaut


def update_astronaut(session: Session, astronaut_id: str, payload: AstronautUpdate):
    astronaut = get_astronaut(session, astronaut_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(astronaut, key, value)
    session.commit()
    session.refresh(astronaut)
    return astronaut


def delete_astronaut(session: Session, astronaut_id: str) -> None:
    astronaut = get_astronaut(session, astronaut_id)
    session.delete(astronaut)
    try:
        session.commit()
    except IntegrityError as exc:
        session.rollback()
        raise ConflictError("Astronaut has stored readings or analyses; deletion is restricted") from exc
