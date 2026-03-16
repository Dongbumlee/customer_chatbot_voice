"""Unit tests for auth middleware."""

from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


class TestValidateToken:
    """Tests for validate_token."""

    @pytest.fixture(autouse=True)
    def _reset_cache(self) -> None:
        """Reset JWKS cache between tests."""
        import app.infrastructure.auth_middleware as mod

        mod._jwks_cache.clear()
        mod._jwks_cache_timestamp = 0.0

    @pytest.fixture
    def mock_settings(self) -> MagicMock:
        settings = MagicMock()
        settings.azure_tenant_id = "test-tenant-id"
        settings.azure_client_id = "test-client-id"
        return settings

    async def test_rejects_empty_token(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials="")

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with pytest.raises(HTTPException) as exc_info:
                await validate_token(credentials)

        assert exc_info.value.status_code == 401
        assert "Missing" in exc_info.value.detail

    async def test_rejects_token_without_kid(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "app.infrastructure.auth_middleware.jwt.get_unverified_header",
                return_value={},
            ):
                credentials = HTTPAuthorizationCredentials(
                    scheme="Bearer", credentials="some.jwt.token"
                )
                with pytest.raises(HTTPException) as exc_info:
                    await validate_token(credentials)

        assert exc_info.value.status_code == 401
        assert "key ID" in exc_info.value.detail

    async def test_rejects_expired_token(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "app.infrastructure.auth_middleware.jwt.get_unverified_header",
                return_value={"kid": "test-kid"},
            ):
                with patch(
                    "app.infrastructure.auth_middleware._get_signing_keys",
                    new_callable=AsyncMock,
                    return_value={"keys": [{"kid": "test-kid"}]},
                ):
                    with patch(
                        "app.infrastructure.auth_middleware.jwt.algorithms.RSAAlgorithm.from_jwk",
                        return_value="fake-key",
                    ):
                        with patch(
                            "app.infrastructure.auth_middleware.jwt.decode",
                            side_effect=jwt.ExpiredSignatureError("expired"),
                        ):
                            credentials = HTTPAuthorizationCredentials(
                                scheme="Bearer", credentials="expired.jwt.token"
                            )
                            with pytest.raises(HTTPException) as exc_info:
                                await validate_token(credentials)

        assert exc_info.value.status_code == 401
        assert "expired" in exc_info.value.detail

    async def test_rejects_invalid_token(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "app.infrastructure.auth_middleware.jwt.get_unverified_header",
                return_value={"kid": "test-kid"},
            ):
                with patch(
                    "app.infrastructure.auth_middleware._get_signing_keys",
                    new_callable=AsyncMock,
                    return_value={"keys": [{"kid": "test-kid"}]},
                ):
                    with patch(
                        "app.infrastructure.auth_middleware.jwt.algorithms.RSAAlgorithm.from_jwk",
                        return_value="fake-key",
                    ):
                        with patch(
                            "app.infrastructure.auth_middleware.jwt.decode",
                            side_effect=jwt.InvalidTokenError("bad"),
                        ):
                            credentials = HTTPAuthorizationCredentials(
                                scheme="Bearer", credentials="bad.jwt.token"
                            )
                            with pytest.raises(HTTPException) as exc_info:
                                await validate_token(credentials)

        assert exc_info.value.status_code == 401
        assert "Invalid" in exc_info.value.detail

    async def test_valid_token_returns_claims(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        expected_claims = {
            "oid": "user-oid",
            "preferred_username": "user@example.com",
            "name": "Test User",
            "sub": "user-sub",
            "exp": 9999999999,
            "iss": f"https://login.microsoftonline.com/{mock_settings.azure_tenant_id}/v2.0",
            "aud": mock_settings.azure_client_id,
        }

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "app.infrastructure.auth_middleware.jwt.get_unverified_header",
                return_value={"kid": "test-kid"},
            ):
                with patch(
                    "app.infrastructure.auth_middleware._get_signing_keys",
                    new_callable=AsyncMock,
                    return_value={"keys": [{"kid": "test-kid"}]},
                ):
                    with patch(
                        "app.infrastructure.auth_middleware.jwt.algorithms.RSAAlgorithm.from_jwk",
                        return_value="fake-key",
                    ):
                        with patch(
                            "app.infrastructure.auth_middleware.jwt.decode",
                            return_value=expected_claims,
                        ):
                            credentials = HTTPAuthorizationCredentials(
                                scheme="Bearer", credentials="valid.jwt.token"
                            )
                            result = await validate_token(credentials)

        assert result["oid"] == "user-oid"
        assert result["preferred_username"] == "user@example.com"

    async def test_retries_jwks_on_key_miss(self, mock_settings: MagicMock) -> None:
        from app.infrastructure.auth_middleware import validate_token

        first_keys = {"keys": [{"kid": "old-kid"}]}
        second_keys = {"keys": [{"kid": "new-kid"}]}

        call_count = 0

        async def mock_get_signing_keys(tenant_id: str):
            nonlocal call_count
            call_count += 1
            return first_keys if call_count == 1 else second_keys

        expected_claims = {
            "oid": "u1",
            "sub": "s1",
            "exp": 9999999999,
            "iss": "i",
            "aud": "a",
        }

        with patch(
            "app.infrastructure.auth_middleware.get_settings",
            return_value=mock_settings,
        ):
            with patch(
                "app.infrastructure.auth_middleware.jwt.get_unverified_header",
                return_value={"kid": "new-kid"},
            ):
                with patch(
                    "app.infrastructure.auth_middleware._get_signing_keys",
                    side_effect=mock_get_signing_keys,
                ):
                    with patch(
                        "app.infrastructure.auth_middleware.jwt.algorithms.RSAAlgorithm.from_jwk",
                        return_value="key",
                    ):
                        with patch(
                            "app.infrastructure.auth_middleware.jwt.decode",
                            return_value=expected_claims,
                        ):
                            credentials = HTTPAuthorizationCredentials(
                                scheme="Bearer", credentials="token"
                            )
                            result = await validate_token(credentials)

        assert call_count == 2
        assert result["oid"] == "u1"


class TestGetCurrentUser:
    """Tests for get_current_user."""

    async def test_extracts_user_info_from_claims(self) -> None:
        from app.infrastructure.auth_middleware import get_current_user

        claims = {
            "oid": "user-oid-123",
            "preferred_username": "test@example.com",
            "name": "Test User",
            "sub": "sub-123",
        }

        result = await get_current_user(request=MagicMock(), claims=claims)

        assert result["oid"] == "user-oid-123"
        assert result["preferred_username"] == "test@example.com"
        assert result["name"] == "Test User"

    async def test_handles_missing_optional_claims(self) -> None:
        from app.infrastructure.auth_middleware import get_current_user

        claims = {"sub": "sub-123"}

        result = await get_current_user(request=MagicMock(), claims=claims)

        assert result["oid"] == ""
        assert result["preferred_username"] == ""
