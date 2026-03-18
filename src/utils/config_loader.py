"""YAML config loading with environment variable overrides.

Loads configuration from YAML files and allows environment variables
to override specific settings.
"""

import os
from pathlib import Path
from typing import Any

import yaml


class ConfigLoader:
    """Loads and merges configuration from YAML files and environment."""

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize the config loader.

        Args:
            config_path: Path to the primary settings YAML file.
        """
        self._config: dict[str, Any] = {}
        self._load(config_path)

    def _load(self, config_path: str) -> None:
        """Load config from YAML file and apply environment overrides."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(path) as f:
            self._config = yaml.safe_load(f) or {}

        # Load environment-specific overrides
        env = os.getenv("ENV", "development")
        env_config_path = path.parent / f"settings.{env[:3]}.yaml"
        if env_config_path.exists():
            with open(env_config_path) as f:
                overrides = yaml.safe_load(f) or {}
                self._deep_merge(self._config, overrides)

        # Apply environment variable overrides (POLYBOT_ prefix)
        self._apply_env_overrides()

    def _deep_merge(self, base: dict[str, Any], override: dict[str, Any]) -> None:
        """Deep merge override dict into base dict."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _apply_env_overrides(self) -> None:
        """Apply POLYBOT_ prefixed env vars as config overrides.

        e.g., POLYBOT_TRADING__MIN_EDGE_THRESHOLD=0.10 sets
        config["trading"]["min_edge_threshold"] = 0.10
        """
        prefix = "POLYBOT_"
        for key, value in os.environ.items():
            if not key.startswith(prefix):
                continue
            config_key = key[len(prefix) :].lower()
            parts = config_key.split("__")
            target = self._config
            for part in parts[:-1]:
                if part not in target:
                    target[part] = {}
                target = target[part]
            # Try to parse as number or bool
            target[parts[-1]] = self._parse_value(value)

    def _parse_value(self, value: str) -> Any:
        """Try to parse a string value as its appropriate type."""
        if value.lower() in ("true", "yes"):
            return True
        if value.lower() in ("false", "no"):
            return False
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "risk.max_position_pct").
            default: Default value if key is not found.

        Returns:
            Configuration value.
        """
        parts = key.split(".")
        current = self._config
        for part in parts:
            if not isinstance(current, dict) or part not in current:
                return default
            current = current[part]
        return current

    def get_all(self) -> dict[str, Any]:
        """Get the entire configuration as a dict.

        Returns:
            Complete configuration dictionary.
        """
        return self._config.copy()
