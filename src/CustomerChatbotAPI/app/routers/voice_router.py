"""Voice router — WebSocket endpoint for real-time voice streaming."""

import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.auth_middleware import validate_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint for bidirectional voice audio streaming.

    Accepts audio chunks from the client, streams to Azure Speech SDK
    for real-time STT, processes via ChatbotOrchestrator, and returns
    TTS audio response.

    Protocol:
        1. Client connects and sends auth token in first message.
        2. Client streams audio chunks as binary frames.
        3. Server sends back transcription events and TTS audio.
        4. Either side can close the connection.
    """
    await websocket.accept()

    voice_service = websocket.app.state.voice_service
    orchestrator = websocket.app.state.orchestrator
    session_id: str | None = None
    max_audio_chunk_size = 65536  # 64 KB

    try:
        import asyncio

        try:
            auth_data = await asyncio.wait_for(
                websocket.receive_json(),
                timeout=10.0,
            )
        except asyncio.TimeoutError:
            await websocket.send_json(
                {"type": "error", "detail": "Authentication timeout"},
            )
            await websocket.close(code=4001)
            return

        auth_data
        if auth_data.get("type") != "auth" or not auth_data.get("token"):
            await websocket.send_json(
                {"type": "error", "detail": "Authentication required"},
            )
            await websocket.close(code=4001)
            return

        try:
            credentials = HTTPAuthorizationCredentials(
                scheme="Bearer",
                credentials=auth_data["token"],
            )
            claims = await validate_token(credentials)
        except Exception:
            await websocket.send_json(
                {"type": "error", "detail": "Invalid token"},
            )
            await websocket.close(code=4001)
            return

        session_id = auth_data.get(
            "session_id",
            f"voice-{claims.get('oid', 'anon')}",
        )
        await voice_service.start_session_async(session_id)
        await websocket.send_json(
            {"type": "session_started", "session_id": session_id},
        )

        while True:
            data = await websocket.receive_bytes()

            if len(data) > max_audio_chunk_size:
                await websocket.send_json(
                    {"type": "error", "detail": "Audio chunk exceeds 64KB limit"},
                )
                continue

            transcription = await voice_service.process_audio_stream_async(data)
            if not transcription:
                continue

            await websocket.send_json(
                {"type": "transcription", "text": transcription},
            )

            agent_response = await orchestrator.process_message_async(
                session_id=session_id,
                user_message=transcription,
                modality="voice",
            )

            await websocket.send_json({
                "type": "response",
                "content": agent_response.content,
                "agent": agent_response.agent,
                "intent": agent_response.intent,
            })

            audio_bytes = await voice_service.synthesize_response_async(
                agent_response.content,
            )
            if audio_bytes:
                await websocket.send_bytes(audio_bytes)

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected: %s", session_id)
    except Exception:
        logger.exception("Voice stream error for session: %s", session_id)
    finally:
        if session_id:
            await voice_service.end_session_async(session_id)
