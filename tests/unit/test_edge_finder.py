"""Tests for EdgeFinder strategy — filled in during Phase 4."""

import pytest


class TestEdgeFinder:
    """Edge finder strategy test suite."""

    @pytest.mark.unit
    def test_positive_edge_generates_buy_signal(self) -> None:
        """When market is underpriced, should generate BUY signal."""
        pytest.skip("Not yet implemented — Phase 4")

    @pytest.mark.unit
    def test_no_edge_returns_none(self) -> None:
        """When edge is below threshold, should return None."""
        pytest.skip("Not yet implemented — Phase 4")

    @pytest.mark.unit
    def test_edge_calculation_accuracy(self) -> None:
        """Edge calculation should match expected values."""
        pytest.skip("Not yet implemented — Phase 4")
