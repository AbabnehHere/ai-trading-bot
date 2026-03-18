"""Shared pytest fixtures for the Polymarket bot test suite."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def sample_market_data() -> dict:
    """Load sample market data from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_market_data.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def sample_orderbook() -> dict:
    """Load sample orderbook from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_orderbook.json"
    with open(fixture_path) as f:
        return json.load(f)


@pytest.fixture
def sample_news_events() -> list:
    """Load sample news events from fixtures."""
    fixture_path = Path(__file__).parent / "fixtures" / "sample_news_events.json"
    with open(fixture_path) as f:
        return json.load(f)
