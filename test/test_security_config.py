"""Tests for security-related settings parsing and validation."""

import pytest

from shared.config import Settings


def test_parse_api_keys_and_project_acl():
    settings = Settings(
        _env_file=None,
        api_keys="key-a,key-b",
        api_key_project_map='{"key-a": ["*", "project-1"], "key-b": ["project-2"]}',
    )

    assert settings.get_allowed_api_keys() == {"key-a", "key-b"}
    assert settings.get_api_key_project_acl() == {
        "key-a": {"*", "project-1"},
        "key-b": {"project-2"},
    }


def test_validate_runtime_rejects_redis_mismatch_for_docker_service_host():
    settings = Settings(
        _env_file=None,
        redis_url="redis://redis:6380/0",
        api_keys="key-a",
    )

    with pytest.raises(ValueError, match="6379"):
        settings.validate_runtime()


def test_validate_runtime_rejects_empty_api_keys_when_auth_enabled():
    settings = Settings(
        _env_file=None,
        auth_enabled=True,
        api_keys="   ",
    )

    with pytest.raises(ValueError, match="EASM_API_KEYS"):
        settings.validate_runtime()


def test_validate_runtime_rejects_invalid_project_acl_json():
    settings = Settings(
        _env_file=None,
        api_keys="key-a",
        api_key_project_map='{"key-a": "not-a-list"}',
    )

    with pytest.raises(ValueError, match="arrays"):
        settings.validate_runtime()
