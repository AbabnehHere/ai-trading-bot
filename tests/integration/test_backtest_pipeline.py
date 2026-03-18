"""Integration tests for backtest pipeline — filled in during Phase 6."""

import pytest


class TestBacktestPipeline:
    """Backtest pipeline integration test suite."""

    @pytest.mark.integration
    def test_backtest_runs_to_completion(self) -> None:
        """Full backtest should run without errors."""
        pytest.skip("Not yet implemented — Phase 6")

    @pytest.mark.integration
    def test_backtest_produces_valid_metrics(self) -> None:
        """Backtest results should contain expected metric keys."""
        pytest.skip("Not yet implemented — Phase 6")
