"""Unit tests for VoiceService."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.voice_service import VoiceLiveSession, VoiceService


@pytest.fixture
def voice_service() -> VoiceService:
    return VoiceService(endpoint="https://test.cognitiveservices.azure.com", model="gpt-4o")


class TestVoiceLiveSession:
    """Tests for VoiceLiveSession dataclass."""

    def test_create_session(self) -> None:
        session = VoiceLiveSession(session_id="s-001")
        assert session.session_id == "s-001"
        assert session.is_active is False
        assert session.ws is None


class TestEndSession:
    """Tests for VoiceService.end_session_async."""

    async def test_removes_session(self, voice_service: VoiceService) -> None:
        mock_ws = AsyncMock()
        session = VoiceLiveSession(session_id="s-001", ws=mock_ws, is_active=True)
        voice_service._sessions["s-001"] = session

        await voice_service.end_session_async("s-001")

        assert "s-001" not in voice_service._sessions
        mock_ws.close.assert_awaited_once()

    async def test_noop_for_unknown_session(self, voice_service: VoiceService) -> None:
        await voice_service.end_session_async("unknown")


class TestGetWsUrl:
    """Tests for VoiceService WebSocket URL construction."""

    def test_builds_correct_url(self, voice_service: VoiceService) -> None:
        url = voice_service._get_ws_url()

        assert url.startswith("wss://test.cognitiveservices.azure.com")
        assert "/voice-live/realtime" in url
        assert "model=gpt-4o" in url
        assert "api-version=2025-10-01" in url


class TestSendAudio:
    """Tests for VoiceService.send_audio_async."""

    async def test_sends_base64_encoded_audio(self, voice_service: VoiceService) -> None:
        mock_ws = AsyncMock()
        session = VoiceLiveSession(session_id="s-001", ws=mock_ws, is_active=True)
        voice_service._sessions["s-001"] = session

        await voice_service.send_audio_async("s-001", b"\x00\x01\x02\x03")

        mock_ws.send.assert_awaited_once()
        import json
        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["type"] == "input_audio_buffer.append"
        assert "audio" in sent_data

    async def test_noop_for_unknown_session(self, voice_service: VoiceService) -> None:
        await voice_service.send_audio_async("unknown", b"\x00\x01")
