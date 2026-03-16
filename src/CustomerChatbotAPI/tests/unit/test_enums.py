"""Unit tests for domain enumerations."""

from app.domain.enums import Intent, MessageRole, Modality, VoiceMode


class TestIntent:
    """Tests for Intent enum values."""

    def test_product_intent(self) -> None:
        assert Intent.PRODUCT == "product"
        assert Intent.PRODUCT.value == "product"

    def test_policy_intent(self) -> None:
        assert Intent.POLICY == "policy"

    def test_general_intent(self) -> None:
        assert Intent.GENERAL == "general"

    def test_intent_is_str(self) -> None:
        assert isinstance(Intent.PRODUCT, str)


class TestModality:
    """Tests for Modality enum values."""

    def test_text_modality(self) -> None:
        assert Modality.TEXT == "text"

    def test_voice_modality(self) -> None:
        assert Modality.VOICE == "voice"

    def test_mixed_modality(self) -> None:
        assert Modality.MIXED == "mixed"


class TestVoiceMode:
    """Tests for VoiceMode enum values."""

    def test_full_voice(self) -> None:
        assert VoiceMode.FULL_VOICE == "full_voice"

    def test_voice_in_only(self) -> None:
        assert VoiceMode.VOICE_IN_ONLY == "voice_in_only"

    def test_text_only(self) -> None:
        assert VoiceMode.TEXT_ONLY == "text_only"


class TestMessageRole:
    """Tests for MessageRole enum values."""

    def test_user_role(self) -> None:
        assert MessageRole.USER == "user"

    def test_assistant_role(self) -> None:
        assert MessageRole.ASSISTANT == "assistant"

    def test_system_role(self) -> None:
        assert MessageRole.SYSTEM == "system"
