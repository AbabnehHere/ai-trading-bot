# TODO: Implement in Phase 3
"""YAML config loading with environment variable overrides.

Loads configuration from YAML files and allows environment variables
to override specific settings.
"""

from typing import Any


class ConfigLoader:
    """Loads and merges configuration from YAML files and environment."""

    def __init__(self, config_path: str = "config/settings.yaml") -> None:
        """Initialize the config loader.

        Args:
            config_path: Path to the primary settings YAML file.
        """
        raise NotImplementedError("Phase 3")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., "risk.max_position_pct").
            default: Default value if key is not found.

        Returns:
            Configuration value.
        """
        raise NotImplementedError("Phase 3")

    def get_all(self) -> dict[str, Any]:
        """Get the entire configuration as a dict.

        Returns:
            Complete configuration dictionary.
        """
        raise NotImplementedError("Phase 3")
