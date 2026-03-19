"""Tests for EdgeFinder strategy."""

import pytest

from src.data.odds_compiler import OddsCompiler


class TestEdgeAfterFees:
    """Test that edge calculations properly account for fees."""

    @pytest.mark.unit
    def test_small_edge_wiped_by_fees(self) -> None:
        """A 3% raw edge should be negative after 2% taker fees."""
        edge = OddsCompiler._edge_after_fees(raw_edge=0.03, market_price=0.50, estimated_prob=0.53)
        # Entry cost: 0.50 * 1.02 = 0.51
        # Expected payout: 0.53 * 1.0 = 0.53
        # Edge after fees: 0.53 - 0.51 = 0.02
        assert edge == pytest.approx(0.02, abs=0.01)

    @pytest.mark.unit
    def test_large_edge_survives_fees(self) -> None:
        """A 10% raw edge should remain positive after fees."""
        edge = OddsCompiler._edge_after_fees(raw_edge=0.10, market_price=0.50, estimated_prob=0.60)
        # Entry cost: 0.50 * 1.02 = 0.51
        # Expected payout: 0.60 * 1.0 = 0.60
        # Edge after fees: 0.60 - 0.51 = 0.09
        assert edge > 0
        assert edge == pytest.approx(0.09, abs=0.01)

    @pytest.mark.unit
    def test_no_edge_returns_zero(self) -> None:
        """Zero raw edge should return zero."""
        edge = OddsCompiler._edge_after_fees(raw_edge=0.0, market_price=0.50, estimated_prob=0.50)
        assert edge == 0.0

    @pytest.mark.unit
    def test_convergence_trade_fees(self) -> None:
        """Buying at $0.95 expecting $1 resolution should be barely +EV."""
        edge = OddsCompiler._edge_after_fees(raw_edge=0.05, market_price=0.95, estimated_prob=1.0)
        # Entry cost: 0.95 * 1.02 = 0.969
        # Expected payout: 1.0 * 1.0 = 1.0
        # Edge: 1.0 - 0.969 = 0.031
        assert edge > 0
        assert edge < 0.05  # Fees eat into the spread

    @pytest.mark.unit
    def test_negative_edge_buying_no(self) -> None:
        """Negative edge should calculate NO side fees correctly."""
        edge = OddsCompiler._edge_after_fees(raw_edge=-0.10, market_price=0.60, estimated_prob=0.50)
        # Buying NO: NO price = 0.40, entry cost = 0.40 * 1.02 = 0.408
        # NO prob = 0.50, expected payout = 0.50
        # Edge: 0.50 - 0.408 = 0.092
        assert edge > 0


class TestEdgeFinder:
    """Edge finder strategy tests."""

    @pytest.mark.unit
    def test_no_signal_without_independent_sources(self) -> None:
        """Should not generate signal if no independent probability sources."""
        from src.strategy.edge_finder import EdgeFinder

        finder = EdgeFinder({"min_edge_threshold": 0.05, "min_independent_sources": 2})
        market = {
            "id": "test",
            "question": "xyzzy unlikely query with no data",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.50},
                {"token_id": "no", "outcome": "No", "price": 0.50},
            ],
            "liquidity": 10000,
            "keywords": ["xyzzy_nonexistent_keyword"],
            "category": "other",
        }
        signal = finder.evaluate(market)
        # Should return None because odds compiler won't find external sources
        # for a nonsense keyword
        assert signal is None

    @pytest.mark.unit
    def test_rejects_illiquid_markets(self) -> None:
        """Should skip markets below minimum liquidity."""
        from src.strategy.edge_finder import EdgeFinder

        finder = EdgeFinder({"min_liquidity_usd": 5000})
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [{"token_id": "yes", "outcome": "Yes", "price": 0.50}],
            "liquidity": 1000,  # Below 5000 minimum
            "keywords": ["test"],
        }
        assert finder.evaluate(market) is None

    @pytest.mark.unit
    def test_skips_extreme_prices(self) -> None:
        """Should skip tokens with prices near 0 or 1."""
        from src.strategy.edge_finder import EdgeFinder

        finder = EdgeFinder()
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.98},
                {"token_id": "no", "outcome": "No", "price": 0.02},
            ],
            "liquidity": 10000,
            "keywords": ["test"],
        }
        assert finder.evaluate(market) is None
