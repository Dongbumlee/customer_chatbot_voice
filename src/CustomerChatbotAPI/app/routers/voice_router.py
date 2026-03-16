"""Voice router — WebSocket relay to Azure Voice Live API."""

import asyncio
import base64
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.auth_middleware import validate_token

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/stream")
async def voice_stream(websocket: WebSocket) -> None:
    """WebSocket endpoint that relays audio between the client and Azure Voice Live API.

    Protocol:
        1. Client sends auth JSON: {"type": "auth", "token": "...", "session_id": "..."}
        2. Server opens Voice Live API WebSocket and returns {"type": "session_started"}
        3. Client sends binary audio frames (PCM 24kHz)
        4. Server relays Voice Live API events back: transcriptions, audio, text
        5. Either side can close the connection.
    """
    await websocket.accept()

    voice_service = websocket.app.state.voice_service
    session_id: str | None = None

    if not voice_service:
        await websocket.send_json({"type": "error", "detail": "Voice features are not available"})
        await websocket.close(code=4003)
        return

    try:
        # Step 1: Authenticate
        try:
            auth_data = await asyncio.wait_for(websocket.receive_json(), timeout=10.0)
        except asyncio.TimeoutError:
            await websocket.send_json({"type": "error", "detail": "Authentication timeout"})
            await websocket.close(code=4001)
            return

        if auth_data.get("type") != "auth" or not auth_data.get("token"):
            await websocket.send_json({"type": "error", "detail": "Authentication required"})
            await websocket.close(code=4001)
            return

        try:
            credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=auth_data["token"])
            claims = await validate_token(credentials)
        except Exception:
            await websocket.send_json({"type": "error", "detail": "Invalid token"})
            await websocket.close(code=4001)
            return

        session_id = auth_data.get("session_id", f"voice-{claims.get('oid', 'anon')}")

        # Step 2: Connect to Voice Live API
        voice_session = await voice_service.connect_session_async(session_id)
        await websocket.send_json({"type": "session_started", "session_id": session_id})

        # Step 3: Two concurrent tasks — relay audio in both directions
        async def forward_client_audio():
            """Forward audio from client WebSocket to Voice Live API."""
            try:
                while True:
                    data = await websocket.receive_bytes()
                    if len(data) > 65536:
                        continue
                    await voice_service.send_audio_async(session_id, data)
            except WebSocketDisconnect:
                pass

        async def forward_voice_live_events():
            """Forward events from Voice Live API to client WebSocket."""
            async for event in voice_service.receive_events_async(session_id):
                event_type = event.get("type", "")

                if event_type == "response.audio.delta":
                    # Voice Live sends base64-encoded audio — forward as binary
                    audio_b64 = event.get("delta", "")
                    if audio_b64:
                        audio_bytes = base64.b64decode(audio_b64)
                        await websocket.send_bytes(audio_bytes)

                elif event_type == "response.audio_transcript.delta":
                    # Partial assistant transcript
                    await websocket.send_json({
                        "type": "assistant_transcript",
                        "text": event.get("delta", ""),
                    })

                elif event_type == "conversation.item.input_audio_transcription.completed":
                    # User's speech transcribed
                    await websocket.send_json({
                        "type": "transcription",
                        "text": event.get("transcript", ""),
                    })

                elif event_type == "response.audio_transcript.done":
                    # Full assistant response complete
                    await websocket.send_json({
                        "type": "response_done",
                        "text": event.get("transcript", ""),
                    })

                elif event_type == "error":
                    await websocket.send_json({
                        "type": "error",
                        "detail": event.get("error", {}).get("message", "Voice Live API error"),
                    })

        # Run both relay tasks concurrently
        await asyncio.gather(
            forward_client_audio(),
            forward_voice_live_events(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        logger.info("Voice WebSocket disconnected: %s", session_id)
    except Exception:
        logger.exception("Voice stream error for session: %s", session_id)
    finally:
        if session_id:
            await voice_service.end_session_async(session_id)
