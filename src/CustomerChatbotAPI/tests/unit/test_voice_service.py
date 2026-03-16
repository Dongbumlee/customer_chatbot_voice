"""Unit tests for VoiceService."""

from unittest.mock import MagicMock, patch

import pytest
from app.services.voice_service import VoiceService, VoiceSession


class TestStartSession:
    """Tests for VoiceService.start_session_async."""

    @pytest.fixture
    def voice_service(self) -> VoiceService:
        return VoiceService(speech_key="test-key", speech_region="eastus2")

    async def test_creates_active_session(self, voice_service: VoiceService) -> None:
        result = await voice_service.start_session_async("session-001")

        assert isinstance(result, VoiceSession)
        assert result.session_id == "session-001"
        assert result.is_active is True

    async def test_stores_session_in_registry(
        self, voice_service: VoiceService
    ) -> None:
        await voice_service.start_session_async("session-001")

        assert "session-001" in voice_service._sessions


class TestEndSession:
    """Tests for VoiceService.end_session_async."""

    @pytest.fixture
    def voice_service(self) -> VoiceService:
        return VoiceService(speech_key="test-key", speech_region="eastus2")

    async def test_removes_session_from_registry(
        self, voice_service: VoiceService
    ) -> None:
        await voice_service.start_session_async("session-001")
        await voice_service.end_session_async("session-001")

        assert "session-001" not in voice_service._sessions

    async def test_noop_for_unknown_session(self, voice_service: VoiceService) -> None:
        await voice_service.end_session_async("unknown")


class TestProcessAudioStream:
    """Tests for VoiceService.process_audio_stream_async."""

    @pytest.fixture
    def voice_service(self) -> VoiceService:
        return VoiceService(speech_key="test-key", speech_region="eastus2")

    @patch("app.services.voice_service.speechsdk")
    async def test_returns_transcribed_text(
        self, mock_sdk: MagicMock, voice_service: VoiceService
    ) -> None:
        mock_result = MagicMock()
        mock_result.reason = mock_sdk.ResultReason.RecognizedSpeech
        mock_result.text = "Hello world"
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_once.return_value = mock_result
        mock_sdk.SpeechRecognizer.return_value = mock_recognizer
        mock_stream = MagicMock()
        mock_sdk.audio.PushAudioInputStream.return_value = mock_stream

        result = await voice_service.process_audio_stream_async(b"fake-audio")

        assert result == "Hello world"
        mock_stream.write.assert_called_once_with(b"fake-audio")
        mock_stream.close.assert_called_once()

    @patch("app.services.voice_service.speechsdk")
    async def test_returns_empty_on_no_match(
        self, mock_sdk: MagicMock, voice_service: VoiceService
    ) -> None:
        mock_result = MagicMock()
        mock_result.reason = mock_sdk.ResultReason.NoMatch
        mock_recognizer = MagicMock()
        mock_recognizer.recognize_once.return_value = mock_result
        mock_sdk.SpeechRecognizer.return_value = mock_recognizer
        mock_sdk.audio.PushAudioInputStream.return_value = MagicMock()

        result = await voice_service.process_audio_stream_async(b"silence")

        assert result == ""


class TestSynthesizeResponse:
    """Tests for VoiceService.synthesize_response_async."""

    @pytest.fixture
    def voice_service(self) -> VoiceService:
        return VoiceService(speech_key="test-key", speech_region="eastus2")

    @patch("app.services.voice_service.speechsdk")
    async def test_returns_audio_bytes(
        self, mock_sdk: MagicMock, voice_service: VoiceService
    ) -> None:
        mock_result = MagicMock()
        mock_result.reason = mock_sdk.ResultReason.SynthesizingAudioCompleted
        mock_result.audio_data = b"mp3-audio-bytes"
        mock_synthesizer = MagicMock()
        mock_synthesizer.speak_text.return_value = mock_result
        mock_sdk.SpeechSynthesizer.return_value = mock_synthesizer

        result = await voice_service.synthesize_response_async("Hello")

        assert result == b"mp3-audio-bytes"

    @patch("app.services.voice_service.speechsdk")
    async def test_returns_empty_on_failure(
        self, mock_sdk: MagicMock, voice_service: VoiceService
    ) -> None:
        mock_result = MagicMock()
        mock_result.reason = mock_sdk.ResultReason.Canceled
        mock_synthesizer = MagicMock()
        mock_synthesizer.speak_text.return_value = mock_result
        mock_sdk.SpeechSynthesizer.return_value = mock_synthesizer

        result = await voice_service.synthesize_response_async("Hello")

        assert result == b""
