"""Voice service — Azure Speech SDK integration for real-time STT/TTS."""

import logging
from dataclasses import dataclass

import azure.cognitiveservices.speech as speechsdk

logger = logging.getLogger(__name__)


@dataclass
class VoiceSession:
    """Represents an active voice streaming session."""

    session_id: str
    is_active: bool = False


class VoiceService:
    """Manages Azure Speech SDK integration.

    Handles speech-to-text and text-to-speech using the Azure
    Cognitive Services Speech SDK, with clean extension points
    for the Voice Live API WebSocket protocol.
    """

    def __init__(
        self,
        speech_key: str,
        speech_region: str,
    ) -> None:
        self._speech_key = speech_key
        self._speech_region = speech_region
        self._sessions: dict[str, VoiceSession] = {}

    async def start_session_async(self, session_id: str) -> VoiceSession:
        """Start a new voice streaming session.

        Args:
            session_id: The chat session ID to associate with voice.

        Returns:
            Active voice session handle.
        """
        voice_session = VoiceSession(session_id=session_id, is_active=True)
        self._sessions[session_id] = voice_session
        logger.info("Voice session started: %s", session_id)
        return voice_session

    async def process_audio_stream_async(self, audio_chunk: bytes) -> str:
        """Process an audio chunk and return transcribed text.

        Args:
            audio_chunk: Raw audio bytes from the client microphone.

        Returns:
            Transcribed text from speech-to-text.
        """
        speech_config = speechsdk.SpeechConfig(
            subscription=self._speech_key,
            region=self._speech_region,
        )
        speech_config.speech_recognition_language = "en-US"

        stream = speechsdk.audio.PushAudioInputStream()
        audio_config = speechsdk.audio.AudioConfig(stream=stream)
        recognizer = speechsdk.SpeechRecognizer(
            speech_config=speech_config,
            audio_config=audio_config,
        )

        stream.write(audio_chunk)
        stream.close()

        result = recognizer.recognize_once()

        if result.reason == speechsdk.ResultReason.RecognizedSpeech:
            return result.text
        if result.reason == speechsdk.ResultReason.NoMatch:
            return ""

        logger.warning("Speech recognition cancelled: %s", result.reason)
        return ""

    async def synthesize_response_async(self, text: str) -> bytes:
        """Synthesize text into speech audio.

        Args:
            text: Agent response text to convert to speech.

        Returns:
            Audio bytes (MP3) for playback.
        """
        speech_config = speechsdk.SpeechConfig(
            subscription=self._speech_key,
            region=self._speech_region,
        )
        speech_config.set_speech_synthesis_output_format(
            speechsdk.SpeechSynthesisOutputFormat.Audio16Khz32KBitRateMonoMp3,
        )

        synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config,
            audio_config=None,
        )

        result = synthesizer.speak_text(text)

        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            return result.audio_data

        logger.warning("Speech synthesis failed: %s", result.reason)
        return b""

    async def end_session_async(self, session_id: str) -> None:
        """End an active voice session and release resources.

        Args:
            session_id: The voice session to terminate.
        """
        session = self._sessions.pop(session_id, None)
        if session:
            session.is_active = False
            logger.info("Voice session ended: %s", session_id)
