"""Integration tests for Polymarket API connection — filled in during Phase 3."""

import pytest


class TestApiConnection:
    """API connection integration test suite."""

    @pytest.mark.integration
    def test_can_connect_to_polymarket_api(self) -> None:
        """Should successfully connect to the Polymarket API."""
        pytest.skip("Not yet implemented — Phase 3")

    @pytest.mark.integration
    def test_can_fetch_active_markets(self) -> None:
        """Should fetch a non-empty list of active markets."""
        pytest.skip("Not yet implemented — Phase 3")
