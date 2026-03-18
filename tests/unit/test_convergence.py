"""Tests for Convergence strategy — filled in during Phase 4."""

import pytest


class TestConvergenceStrategy:
    """Convergence strategy test suite."""

    @pytest.mark.unit
    def test_near_resolution_market_generates_signal(self) -> None:
        """Markets near resolution with clear outcome should generate signal."""
        pytest.skip("Not yet implemented — Phase 4")

    @pytest.mark.unit
    def test_far_from_resolution_returns_none(self) -> None:
        """Markets far from resolution should not generate signal."""
        pytest.skip("Not yet implemented — Phase 4")
