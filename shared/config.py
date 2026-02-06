import json
from urllib.parse import urlparse

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "dev"
    database_url: str = "postgresql+psycopg://easm:easm@db:5432/easm"
    redis_url: str = "redis://redis:6379/0"
    auth_enabled: bool = True
    api_keys: str = "dev-change-me"
    api_key_project_map: str = ""
    scan_verify_tls: bool = True

    class Config:
        env_file = ".env"
        env_prefix = "EASM_"

    def get_allowed_api_keys(self) -> set[str]:
        """Parse comma-separated API keys from settings."""
        return {key.strip() for key in self.api_keys.split(",") if key.strip()}

    def get_api_key_project_acl(self) -> dict[str, set[str]]:
        """
        Parse API key project ACL from JSON.

        Format:
            {"api-key-1": ["<project-uuid>", "*"], "api-key-2": ["<project-uuid>"]}
        """
        raw = self.api_key_project_map.strip()
        if not raw:
            return {}

        try:
            loaded = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError("EASM_API_KEY_PROJECT_MAP must be valid JSON") from exc

        if not isinstance(loaded, dict):
            raise ValueError("EASM_API_KEY_PROJECT_MAP must be a JSON object")

        acl: dict[str, set[str]] = {}
        for key, project_ids in loaded.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError("EASM_API_KEY_PROJECT_MAP contains an invalid API key")
            if not isinstance(project_ids, list):
                raise ValueError("EASM_API_KEY_PROJECT_MAP values must be arrays")

            acl[key.strip()] = {
                str(project_id).strip()
                for project_id in project_ids
                if str(project_id).strip()
            }
        return acl

    def validate_runtime(self) -> None:
        """Fail fast on invalid security/runtime settings."""
        if self.auth_enabled and not self.get_allowed_api_keys():
            raise ValueError("EASM_API_KEYS must not be empty when auth is enabled")
        self.get_api_key_project_acl()

        parsed = urlparse(self.redis_url)
        redis_host = parsed.hostname or ""
        redis_port = parsed.port if parsed.port is not None else 6379

        # In docker-compose service network, redis must be reached on container port 6379.
        if redis_host == "redis" and redis_port != 6379:
            raise ValueError(
                "Invalid EASM_REDIS_URL: host 'redis' must use container port 6379"
            )


settings = Settings()
