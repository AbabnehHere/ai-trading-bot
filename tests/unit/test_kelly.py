"""Tests for Kelly Criterion calculation — filled in during Phase 4."""

import pytest


class TestKellyCriterion:
    """Kelly criterion test suite."""

    @pytest.mark.unit
    def test_kelly_positive_edge(self) -> None:
        """Positive edge should return positive bet size."""
        pytest.skip("Not yet implemented — Phase 4")

    @pytest.mark.unit
    def test_kelly_negative_edge_returns_zero(self) -> None:
        """Negative edge should return zero bet size."""
        pytest.skip("Not yet implemented — Phase 4")

    @pytest.mark.unit
    def test_fractional_kelly_reduces_size(self) -> None:
        """Fractional Kelly should be smaller than full Kelly."""
        pytest.skip("Not yet implemented — Phase 4")
