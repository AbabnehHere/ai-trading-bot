"""Tests for ConfigLoader."""

import os

import pytest

from src.utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Config loader test suite."""

    @pytest.mark.unit
    def test_loads_yaml_config(self) -> None:
        """Should successfully load a YAML config file."""
        # Use the actual settings.yaml
        loader = ConfigLoader("config/settings.yaml")
        config = loader.get_all()
        assert "bot" in config
        assert config["bot"]["name"] == "polymarket-bot"

    @pytest.mark.unit
    def test_dot_notation_access(self) -> None:
        """Should support dot-notation key access."""
        loader = ConfigLoader("config/settings.yaml")
        name = loader.get("bot.name")
        assert name == "polymarket-bot"

    @pytest.mark.unit
    def test_dot_notation_missing_key_returns_default(self) -> None:
        """Missing keys should return the default value."""
        loader = ConfigLoader("config/settings.yaml")
        result = loader.get("nonexistent.key", default="fallback")
        assert result == "fallback"

    @pytest.mark.unit
    def test_nested_config_access(self) -> None:
        """Should access deeply nested values."""
        loader = ConfigLoader("config/settings.yaml")
        edge_threshold = loader.get("strategy.edge_detection.min_edge_threshold")
        assert edge_threshold == 0.08

    @pytest.mark.unit
    def test_missing_file_raises_error(self) -> None:
        """Should raise FileNotFoundError for missing config."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader("config/nonexistent.yaml")

    @pytest.mark.unit
    def test_env_var_override(self) -> None:
        """Environment variables with POLYBOT_ prefix should override config."""
        os.environ["POLYBOT_BOT__NAME"] = "test-bot"
        try:
            loader = ConfigLoader("config/settings.yaml")
            assert loader.get("bot.name") == "test-bot"
        finally:
            del os.environ["POLYBOT_BOT__NAME"]
