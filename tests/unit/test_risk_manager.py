"""Tests for RiskManager — filled in during Phase 5."""

import pytest


class TestRiskManager:
    """Risk manager test suite."""

    @pytest.mark.unit
    def test_rejects_trade_exceeding_max_position_size(self) -> None:
        """Trade larger than max_position_pct should be rejected."""
        pytest.skip("Not yet implemented — Phase 5")

    @pytest.mark.unit
    def test_rejects_trade_when_daily_loss_limit_hit(self) -> None:
        """No new trades after daily loss limit is breached."""
        pytest.skip("Not yet implemented — Phase 5")

    @pytest.mark.unit
    def test_circuit_breaker_halts_all_trading(self) -> None:
        """Drawdown circuit breaker should halt everything."""
        pytest.skip("Not yet implemented — Phase 5")
