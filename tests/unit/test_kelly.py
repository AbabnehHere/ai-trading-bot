"""Tests for Kelly Criterion calculation."""

import pytest

from src.utils.helpers import calculate_expected_value, edge_to_odds, kelly_criterion


class TestKellyCriterion:
    """Kelly criterion test suite."""

    @pytest.mark.unit
    def test_kelly_positive_edge(self) -> None:
        """Positive edge should return positive bet size."""
        # 60% chance of winning, 2x payout (decimal odds)
        result = kelly_criterion(probability=0.6, odds=2.0, fraction=1.0)
        # Full Kelly: f = (0.6 * 1 - 0.4) / 1 = 0.2
        assert result == pytest.approx(0.2, abs=0.001)

    @pytest.mark.unit
    def test_kelly_negative_edge_returns_zero(self) -> None:
        """Negative edge should return zero bet size."""
        # 40% chance of winning, 2x payout → negative edge
        result = kelly_criterion(probability=0.3, odds=2.0, fraction=1.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_fractional_kelly_reduces_size(self) -> None:
        """Fractional Kelly should be smaller than full Kelly."""
        full = kelly_criterion(probability=0.6, odds=2.0, fraction=1.0)
        quarter = kelly_criterion(probability=0.6, odds=2.0, fraction=0.25)
        assert quarter == pytest.approx(full * 0.25, abs=0.001)
        assert quarter < full

    @pytest.mark.unit
    def test_kelly_50_50_fair_odds_is_zero(self) -> None:
        """A fair bet (50% at 2x odds) should return zero — no edge."""
        result = kelly_criterion(probability=0.5, odds=2.0, fraction=1.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_kelly_invalid_inputs(self) -> None:
        """Invalid inputs should return zero."""
        assert kelly_criterion(probability=0.0, odds=2.0) == 0.0
        assert kelly_criterion(probability=1.0, odds=2.0) == 0.0
        assert kelly_criterion(probability=0.5, odds=0.0) == 0.0
        assert kelly_criterion(probability=-0.1, odds=2.0) == 0.0
        assert kelly_criterion(probability=0.5, odds=-1.0) == 0.0

    @pytest.mark.unit
    def test_kelly_polymarket_scenario(self) -> None:
        """Test with a realistic Polymarket scenario.

        Market price: $0.50 (implied 50% probability)
        Our estimate: 65% probability
        Decimal odds at $0.50: 1/0.50 = 2.0
        """
        our_prob = 0.65
        market_price = 0.50
        odds = 1.0 / market_price  # 2.0

        full = kelly_criterion(our_prob, odds, fraction=1.0)
        quarter = kelly_criterion(our_prob, odds, fraction=0.25)

        # Full Kelly: (0.65 * 1 - 0.35) / 1 = 0.30
        assert full == pytest.approx(0.30, abs=0.001)
        assert quarter == pytest.approx(0.075, abs=0.001)


class TestExpectedValue:
    """Expected value calculation tests."""

    @pytest.mark.unit
    def test_positive_ev_trade(self) -> None:
        """A trade where probability * payout exceeds cost is +EV."""
        ev = calculate_expected_value(probability=0.7, payout=1.0, cost=0.50)
        assert ev == pytest.approx(0.20, abs=0.001)

    @pytest.mark.unit
    def test_negative_ev_trade(self) -> None:
        """A trade where cost exceeds expected payout is -EV."""
        ev = calculate_expected_value(probability=0.3, payout=1.0, cost=0.50)
        assert ev == pytest.approx(-0.20, abs=0.001)

    @pytest.mark.unit
    def test_break_even_trade(self) -> None:
        """A fair trade has zero EV."""
        ev = calculate_expected_value(probability=0.5, payout=1.0, cost=0.50)
        assert ev == pytest.approx(0.0, abs=0.001)


class TestEdgeToOdds:
    """Edge to odds conversion tests."""

    @pytest.mark.unit
    def test_fifty_percent_gives_2x_odds(self) -> None:
        assert edge_to_odds(0.50) == pytest.approx(2.0)

    @pytest.mark.unit
    def test_twenty_five_percent_gives_4x_odds(self) -> None:
        assert edge_to_odds(0.25) == pytest.approx(4.0)

    @pytest.mark.unit
    def test_extreme_prices_return_zero(self) -> None:
        assert edge_to_odds(0.0) == 0.0
        assert edge_to_odds(1.0) == 0.0
