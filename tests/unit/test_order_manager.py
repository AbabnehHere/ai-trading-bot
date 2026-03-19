"""Tests for OrderManager — verifies fee tracking."""

import pytest

from src.core.order_manager import TAKER_FEE_RATE, OrderManager


class TestOrderManager:
    """Order manager test suite."""

    @pytest.mark.unit
    def test_paper_order_includes_fees(self) -> None:
        """Paper orders should calculate and include fee estimates."""
        om = OrderManager(paper=True)
        result = om.place_order(
            token_id="tok1",  # noqa: S106
            market_id="mkt1",
            side="BUY",
            size=100,
            price=0.50,
        )
        expected_fee = 100 * 0.50 * TAKER_FEE_RATE
        assert result["fees"] == pytest.approx(expected_fee, abs=0.001)
        assert result["status"] == "filled"
        assert result["is_paper"] is True

    @pytest.mark.unit
    def test_paper_cancel_succeeds(self) -> None:
        """Cancelling a paper order should return True."""
        om = OrderManager(paper=True)
        assert om.cancel_order("paper_1") is True

    @pytest.mark.unit
    def test_paper_open_orders_empty(self) -> None:
        """Paper mode should report no open orders."""
        om = OrderManager(paper=True)
        assert om.get_open_orders() == []
