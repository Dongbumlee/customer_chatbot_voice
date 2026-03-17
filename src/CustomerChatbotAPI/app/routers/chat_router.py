"""Chat router — endpoints for text-based chat interaction."""

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import StreamingResponse

from app.domain.entities import ChatSession
from app.domain.models import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatSessionResponse,
)
from app.infrastructure.auth_middleware import get_current_user

router = APIRouter()


def _get_orchestrator(request: Request):
    return request.app.state.orchestrator


def _get_session_repo(request: Request):
    return request.app.state.session_repository


def _get_message_repo(request: Request):
    return request.app.state.message_repository


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    user: dict = Depends(get_current_user),
    orchestrator=Depends(_get_orchestrator),
) -> ChatMessageResponse:
    """Send a text message and receive an agent response.

    Routes through the ChatbotOrchestrator for intent classification
    and domain-specific agent handling.
    """
    agent_response = await orchestrator.process_message_async(
        session_id=request.session_id,
        user_message=request.content,
        modality=request.modality,
    )
    return ChatMessageResponse(
        message_id=str(uuid.uuid4()),
        session_id=request.session_id,
        content=agent_response.content,
        agent=agent_response.agent,
        metadata=agent_response.metadata,
        timestamp=datetime.now(timezone.utc),
    )


@router.post("/message/stream")
async def send_message_stream(
    request: ChatMessageRequest,
    user: dict = Depends(get_current_user),
    orchestrator=Depends(_get_orchestrator),
) -> StreamingResponse:
    """Stream an agent response as Server-Sent Events (SSE).

    Events:
        - data: {"type":"meta","agent":"chat","intent":"general"}
        - data: {"type":"chunk","content":"Hello"}
        - data: {"type":"chunk","content":" there!"}
        - data: {"type":"product_cards","cards":[...]}
        - data: {"type":"done"}
    """
    async def event_generator():
        async for event in orchestrator.process_message_stream_async(
            session_id=request.session_id,
            user_message=request.content,
            modality=request.modality,
        ):
            yield f"data: {json.dumps(event)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/session", response_model=ChatSessionResponse)
async def create_session(
    user: dict = Depends(get_current_user),
    session_repo=Depends(_get_session_repo),
) -> ChatSessionResponse:
    """Create a new chat session for the authenticated user."""
    now = datetime.now(timezone.utc)
    session = ChatSession(
        id=str(uuid.uuid4()),
        user_id=user["oid"],
        title="New Chat",
        modality="text",
        created_at=now,
        last_active_at=now,
    )
    await session_repo.add_async(session)
    return ChatSessionResponse(
        session_id=session.id,
        title=session.title,
        modality=session.modality,
        created_at=session.created_at,
        last_active_at=session.last_active_at,
        is_active=session.is_active,
    )


@router.get("/session/{session_id}/history", response_model=list[ChatMessageResponse])
async def get_session_history(
    session_id: str,
    user: dict = Depends(get_current_user),
    session_repo=Depends(_get_session_repo),
    message_repo=Depends(_get_message_repo),
) -> list[ChatMessageResponse]:
    """Retrieve chat history for a specific session.

    Only returns history for sessions owned by the authenticated user.
    """
    session = await session_repo.get_async(session_id)
    if not session or session.user_id != user["oid"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    messages = await message_repo.find_async({"session_id": session_id})
    return [
        ChatMessageResponse(
            message_id=msg.id,
            session_id=msg.session_id,
            content=msg.content,
            agent=msg.agent,
            metadata=msg.metadata,
            timestamp=msg.timestamp,
        )
        for msg in (messages or [])
    ]


@router.delete("/session/{session_id}", status_code=204)
async def end_session(
    session_id: str,
    user: dict = Depends(get_current_user),
    session_repo=Depends(_get_session_repo),
) -> None:
    """End/archive a chat session."""
    session = await session_repo.get_async(session_id)
    if not session or session.user_id != user["oid"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )
    session.is_active = False
    await session_repo.update_async(session)
