"""Assistant request boundary; content generation belongs to Member 3."""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.connection import get_session
from app.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.ai_adapter import AIAdapter, get_ai_adapter
from app.services.assistant_service import ask_assistant

router = APIRouter(prefix="/ai", tags=["AI assistant"])


@router.post("/assistant", response_model=AssistantResponse)
def assistant(payload: AssistantRequest,
              session: Annotated[Session, Depends(get_session)],
              adapter: Annotated[AIAdapter, Depends(get_ai_adapter)]):
    """Ask with optional explicitly selected analysis context. Does not save a conversation."""
    return ask_assistant(session, payload, adapter)
