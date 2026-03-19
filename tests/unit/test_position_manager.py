"""Tests for PositionManager — verifies position tracking and fee accounting."""

import pytest

from src.core.position_manager import TAKER_FEE_RATE, PositionManager
from src.data.market_data import MarketDataClient


def _make_positions(balance: float = 1000.0, use_taker_fees: bool = True) -> PositionManager:
    """Create a position manager for testing."""
    market_data = MarketDataClient()
    return PositionManager(
        market_data, balance, paper=True, use_taker_fees=use_taker_fees, skip_db_reload=True
    )


class TestPositionManager:
    """Position manager test suite."""

    @pytest.mark.unit
    def test_buy_deducts_cost_plus_fees(self) -> None:
        """Buying should deduct price * size + fees from cash."""
        pm = _make_positions(1000.0, use_taker_fees=True)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)

        notional = 100 * 0.50  # $50
        expected_fee = notional * TAKER_FEE_RATE  # $1
        expected_cash = 1000.0 - notional - expected_fee  # $949

        assert pm.get_cash_balance() == pytest.approx(expected_cash, abs=0.01)
        assert pm.get_total_fees_paid() == pytest.approx(expected_fee, abs=0.01)

    @pytest.mark.unit
    def test_sell_adds_proceeds_minus_fees(self) -> None:
        """Selling should add proceeds - fees to cash."""
        pm = _make_positions(1000.0, use_taker_fees=True)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)
        pm.record_fill("mkt1", "tok1", "SELL", size=100, price=0.60)

        # Bought at $50 + $1 fee = $51 cost
        # Sold at $60 - $1.20 fee = $58.80 proceeds
        # Cash = 1000 - 51 + 58.80 = 1007.80
        assert pm.get_cash_balance() == pytest.approx(1007.80, abs=0.01)
        assert pm.get_position_count() == 0

    @pytest.mark.unit
    def test_fees_eat_small_profits(self) -> None:
        """Fees should make tiny price moves unprofitable."""
        pm = _make_positions(1000.0, use_taker_fees=True)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)
        # Sell at 1 cent profit per share
        pm.record_fill("mkt1", "tok1", "SELL", size=100, price=0.51)

        # Gross profit: $1.00
        # Buy fee: $1.00, Sell fee: $1.02
        # Net: $1.00 - $1.00 - $1.02 = -$1.02
        assert pm.get_cash_balance() < 1000.0  # Should have lost money

    @pytest.mark.unit
    def test_no_fees_when_maker(self) -> None:
        """With maker fees (0%), no fees should be charged."""
        pm = _make_positions(1000.0, use_taker_fees=False)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)

        assert pm.get_cash_balance() == pytest.approx(950.0, abs=0.01)
        assert pm.get_total_fees_paid() == 0.0

    @pytest.mark.unit
    def test_portfolio_value_includes_positions(self) -> None:
        """Portfolio value should include cash + position value."""
        pm = _make_positions(1000.0, use_taker_fees=False)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)

        # Cash: $950, Position: 100 shares * $0.50 = $50
        # Total: $1000
        assert pm.get_portfolio_value() == pytest.approx(1000.0, abs=0.01)

    @pytest.mark.unit
    def test_drawdown_calculation(self) -> None:
        """Drawdown should reflect decline from peak value."""
        pm = _make_positions(1000.0, use_taker_fees=False)
        # Record peak value
        pm.get_portfolio_value()  # Sets peak to 1000

        # Simulate loss by reducing cash
        pm._cash = 900.0
        drawdown = pm.get_drawdown()
        assert drawdown == pytest.approx(0.10, abs=0.01)

    @pytest.mark.unit
    def test_pnl_accounts_for_fees(self) -> None:
        """Position P&L should account for entry fees and estimated exit fees."""
        pm = _make_positions(1000.0, use_taker_fees=True)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.50)

        # Current price same as entry — should show loss due to fees
        pnl = pm.get_position_pnl("mkt1", current_price=0.50)
        assert pnl["unrealized_pnl"] < 0  # Negative because of exit fee estimate
        assert pnl["pnl_pct"] < 0  # Cost basis includes entry fee

    @pytest.mark.unit
    def test_convergence_trade_profitability(self) -> None:
        """Test if a convergence trade (buy at $0.95, resolve at $1.00) is
        profitable after fees. With 2% taker fees, it should be barely profitable."""
        pm = _make_positions(1000.0, use_taker_fees=True)
        pm.record_fill("mkt1", "tok1", "BUY", size=100, price=0.95)
        pm.record_fill("mkt1", "tok1", "SELL", size=100, price=1.00)

        # Gross profit: $5.00 (100 * $0.05)
        # Buy fee: 100 * 0.95 * 0.02 = $1.90
        # Sell fee: 100 * 1.00 * 0.02 = $2.00
        # Net: $5.00 - $1.90 - $2.00 = $1.10
        assert pm.get_cash_balance() > 1000.0  # Still profitable
        # But total fees are significant relative to profit
        assert pm.get_total_fees_paid() == pytest.approx(3.90, abs=0.01)
