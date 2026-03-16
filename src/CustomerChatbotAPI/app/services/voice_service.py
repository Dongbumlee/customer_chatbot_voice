"""Voice service — Azure Voice Live API integration for real-time speech-to-speech."""

import json
import logging
from dataclasses import dataclass, field

import websockets
from azure.identity import DefaultAzureCredential

logger = logging.getLogger(__name__)


@dataclass
class VoiceLiveSession:
    """Represents an active Voice Live API WebSocket session."""

    session_id: str
    ws: object = field(default=None, repr=False)
    is_active: bool = False


class VoiceService:
    """Manages Azure Voice Live API integration.

    Connects to the Voice Live API WebSocket, which provides fully managed
    speech-to-text + AI reasoning + text-to-speech in a single connection.
    See: https://learn.microsoft.com/azure/ai-services/speech-service/voice-live
    """

    def __init__(
        self,
        endpoint: str,
        model: str = "gpt-4o",
        voice_name: str = "en-US-Ava:DragonHDLatestNeural",
    ) -> None:
        # endpoint: e.g. "https://oai-xxx.openai.azure.com/"
        self._endpoint = endpoint.rstrip("/")
        self._model = model
        self._voice_name = voice_name
        self._sessions: dict[str, VoiceLiveSession] = {}
        self._credential = DefaultAzureCredential()

    def _get_ws_url(self) -> str:
        """Build the Voice Live API WebSocket URL."""
        # Convert https:// to wss://
        ws_endpoint = self._endpoint.replace("https://", "wss://").replace("http://", "ws://")
        return (
            f"{ws_endpoint}"
            f"/voice-live/realtime?api-version=2025-10-01&model={self._model}"
        )

    async def _get_auth_token(self) -> str:
        """Get a Bearer token for the Voice Live API."""
        token = self._credential.get_token(
            "https://cognitiveservices.azure.com/.default"
        )
        return token.token

    async def connect_session_async(self, session_id: str) -> VoiceLiveSession:
        """Open a WebSocket connection to Voice Live API.

        Returns:
            Active VoiceLiveSession with open WebSocket.
        """
        token = await self._get_auth_token()
        ws_url = self._get_ws_url()
        logger.info("Connecting to Voice Live API: %s", ws_url)

        ws = await websockets.connect(
            ws_url,
            additional_headers={"Authorization": f"Bearer {token}"},
        )
        logger.info("Voice Live WebSocket connected for session: %s", session_id)

        # Configure the session
        session_config = {
            "type": "session.update",
            "session": {
                "instructions": (
                    "You are a friendly customer service assistant for a retail chatbot. "
                    "Help users with product discovery, recommendations, and policy questions. "
                    "Keep responses concise and conversational since the user is speaking."
                ),
                "modalities": ["text", "audio"],
                "turn_detection": {
                    "type": "azure_semantic_vad",
                    "silence_duration_ms": 500,
                },
                "input_audio_noise_reduction": {"type": "azure_deep_noise_suppression"},
                "input_audio_echo_cancellation": {"type": "server_echo_cancellation"},
                "voice": {
                    "name": self._voice_name,
                    "type": "azure-standard",
                },
            },
        }
        await ws.send(json.dumps(session_config))

        voice_session = VoiceLiveSession(
            session_id=session_id, ws=ws, is_active=True,
        )
        self._sessions[session_id] = voice_session
        logger.info("Voice Live session connected: %s", session_id)
        return voice_session

    async def send_audio_async(self, session_id: str, audio_data: bytes) -> None:
        """Send audio data to the Voice Live API.

        Audio is sent as base64-encoded PCM in an input_audio_buffer.append event.
        """
        import base64

        session = self._sessions.get(session_id)
        if not session or not session.ws:
            return

        audio_b64 = base64.b64encode(audio_data).decode("ascii")
        event = {
            "type": "input_audio_buffer.append",
            "audio": audio_b64,
        }
        await session.ws.send(json.dumps(event))

    async def receive_events_async(self, session_id: str):
        """Async generator that yields events from the Voice Live API.

        Yields dicts with event type and relevant data (text, audio, etc.).
        """
        session = self._sessions.get(session_id)
        if not session or not session.ws:
            return

        try:
            async for message in session.ws:
                event = json.loads(message)
                yield event
        except websockets.exceptions.ConnectionClosed:
            logger.info("Voice Live WebSocket closed: %s", session_id)
        finally:
            session.is_active = False

    async def end_session_async(self, session_id: str) -> None:
        """Close the Voice Live API WebSocket session."""
        session = self._sessions.pop(session_id, None)
        if session and session.ws:
            try:
                await session.ws.close()
            except Exception:
                pass
            session.is_active = False
            logger.info("Voice Live session ended: %s", session_id)
