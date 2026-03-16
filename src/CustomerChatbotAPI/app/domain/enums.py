"""Domain enumerations."""

from enum import StrEnum


class Intent(StrEnum):
    """User intent classification results."""

    PRODUCT = "product"
    POLICY = "policy"
    GENERAL = "general"


class Modality(StrEnum):
    """Communication modality."""

    TEXT = "text"
    VOICE = "voice"
    MIXED = "mixed"


class VoiceMode(StrEnum):
    """Voice interaction modes."""

    FULL_VOICE = "full_voice"  # voice in + voice out
    VOICE_IN_ONLY = "voice_in_only"  # voice in + text out
    TEXT_ONLY = "text_only"  # text in + text out


class MessageRole(StrEnum):
    """Chat message roles."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
