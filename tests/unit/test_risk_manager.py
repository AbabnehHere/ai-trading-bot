"""Tests for RiskManager — verifies all risk checks work correctly."""

import pytest

from src.core.position_manager import PositionManager
from src.core.risk_manager import RiskManager
from src.data.market_data import MarketDataClient


def _make_risk_manager(
    balance: float = 1000.0,
    max_position_pct: float = 0.03,
    max_drawdown_pct: float = 0.10,
    max_daily_loss_pct: float = 0.03,
    max_concurrent: int = 10,
    min_trade_size: float = 5.0,
    max_trade_size: float = 100.0,
    max_trades_per_day: int = 20,
    cooldown_minutes: int = 0,
) -> tuple[RiskManager, PositionManager]:
    """Create a risk manager + position manager for testing."""
    market_data = MarketDataClient()
    positions = PositionManager(market_data, balance, paper=True, use_taker_fees=False)
    config = {
        "max_position_pct": max_position_pct,
        "max_drawdown_pct": max_drawdown_pct,
        "max_daily_loss_pct": max_daily_loss_pct,
        "max_concurrent_positions": max_concurrent,
        "min_trade_size": min_trade_size,
        "max_trade_size": max_trade_size,
        "max_trades_per_day": max_trades_per_day,
        "cooldown_after_loss_minutes": cooldown_minutes,
        "min_bankroll_usd": 50.0,
    }
    risk = RiskManager(positions, config)
    return risk, positions


class TestRiskManager:
    """Risk manager test suite."""

    @pytest.mark.unit
    def test_rejects_trade_exceeding_max_position_size(self) -> None:
        """Trade larger than max_position_pct should be rejected."""
        risk, _ = _make_risk_manager(balance=1000.0, max_position_pct=0.03)
        # 3% of $1000 = $30 max. Try placing $50 worth (100 shares at $0.50)
        result = risk.check_trade("mkt1", "BUY", size=100, price=0.50)
        assert not result.approved
        assert "exceeds max" in result.reason.lower() or "Position" in result.reason

    @pytest.mark.unit
    def test_approves_trade_within_position_limit(self) -> None:
        """Trade within max_position_pct should be approved."""
        risk, _ = _make_risk_manager(balance=1000.0, max_position_pct=0.03)
        # 3% of $1000 = $30 max. Place $25 worth (50 shares at $0.50)
        result = risk.check_trade("mkt1", "BUY", size=50, price=0.50)
        assert result.approved

    @pytest.mark.unit
    def test_rejects_trade_when_daily_loss_limit_hit(self) -> None:
        """No new trades after daily loss limit is breached."""
        risk, _ = _make_risk_manager(balance=1000.0, max_daily_loss_pct=0.03)
        # Record $31 in losses (3.1% of $1000 > 3% limit)
        risk.record_loss(31.0)
        result = risk.check_trade("mkt1", "BUY", size=10, price=0.50)
        assert not result.approved
        assert "daily loss" in result.reason.lower()

    @pytest.mark.unit
    def test_circuit_breaker_halts_all_trading(self) -> None:
        """Drawdown circuit breaker should halt everything."""
        risk, positions = _make_risk_manager(balance=1000.0, max_drawdown_pct=0.10)
        # Simulate drawdown by reducing cash
        positions._cash = 850.0  # 15% down from $1000 peak
        result = risk.check_trade("mkt1", "BUY", size=10, price=0.50)
        assert not result.approved
        assert "circuit breaker" in result.reason.lower() or "drawdown" in result.reason.lower()

    @pytest.mark.unit
    def test_rejects_trade_below_minimum_size(self) -> None:
        """Trade below min_trade_size should be rejected."""
        risk, _ = _make_risk_manager(min_trade_size=5.0)
        # $2.50 worth (5 shares at $0.50) < $5 minimum
        result = risk.check_trade("mkt1", "BUY", size=5, price=0.50)
        assert not result.approved
        assert "below minimum" in result.reason.lower()

    @pytest.mark.unit
    def test_rejects_trade_above_maximum_size(self) -> None:
        """Trade above max_trade_size should be rejected."""
        risk, _ = _make_risk_manager(balance=10000.0, max_position_pct=0.5, max_trade_size=100.0)
        # $150 worth > $100 maximum
        result = risk.check_trade("mkt1", "BUY", size=300, price=0.50)
        assert not result.approved
        assert "exceeds maximum" in result.reason.lower()

    @pytest.mark.unit
    def test_rejects_when_max_positions_reached(self) -> None:
        """Should reject when max concurrent positions reached."""
        risk, positions = _make_risk_manager(
            balance=10000.0, max_concurrent=2, max_position_pct=0.5
        )
        # Fill 2 positions
        positions.record_fill("mkt1", "tok1", "BUY", 10, 0.50)
        positions.record_fill("mkt2", "tok2", "BUY", 10, 0.50)

        result = risk.check_trade("mkt3", "BUY", size=10, price=0.50)
        assert not result.approved
        assert "concurrent" in result.reason.lower()

    @pytest.mark.unit
    def test_rejects_when_bankroll_too_low(self) -> None:
        """Should reject when bankroll is below minimum."""
        risk, _ = _make_risk_manager(balance=40.0)  # Below $50 minimum
        result = risk.check_trade("mkt1", "BUY", size=10, price=0.50)
        assert not result.approved
        assert "below minimum" in result.reason.lower()

    @pytest.mark.unit
    def test_rejects_when_daily_trade_count_exceeded(self) -> None:
        """Should reject when max daily trades reached."""
        risk, _ = _make_risk_manager(max_trades_per_day=2)
        risk.record_trade()
        risk.record_trade()
        result = risk.check_trade("mkt1", "BUY", size=10, price=0.50)
        assert not result.approved
        assert "daily trades" in result.reason.lower()

    @pytest.mark.unit
    def test_stop_loss_triggers_correctly(self) -> None:
        """Stop-loss at -30% should trigger at -30% or worse."""
        risk, _ = _make_risk_manager()
        assert risk.check_stop_loss(-0.30) is True
        assert risk.check_stop_loss(-0.50) is True
        assert risk.check_stop_loss(-0.10) is False
        assert risk.check_stop_loss(0.10) is False

    @pytest.mark.unit
    def test_take_profit_triggers_correctly(self) -> None:
        """Take-profit at +50% should trigger at +50% or better."""
        risk, _ = _make_risk_manager()
        assert risk.check_take_profit(0.50) is True
        assert risk.check_take_profit(0.80) is True
        assert risk.check_take_profit(0.30) is False
        assert risk.check_take_profit(-0.10) is False

    @pytest.mark.unit
    def test_kelly_position_sizing(self) -> None:
        """Position sizing should use fractional Kelly and respect caps."""
        risk, _ = _make_risk_manager(balance=1000.0, max_position_pct=0.03)
        # 65% probability, market price 0.50 (2x odds)
        size = risk.calculate_position_size(probability=0.65, market_price=0.50)
        # Should be positive but capped at 3% of $1000 = $30
        assert size > 0
        assert size <= 30.0

    @pytest.mark.unit
    def test_kelly_no_edge_returns_zero(self) -> None:
        """No edge should return zero position size."""
        risk, _ = _make_risk_manager()
        # 50% probability at 50 cents = fair odds, no edge
        size = risk.calculate_position_size(probability=0.50, market_price=0.50)
        assert size == 0.0
