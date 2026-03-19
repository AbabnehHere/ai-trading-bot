"""Tests for Convergence strategy."""

from datetime import UTC, datetime, timedelta

import pytest

from src.strategy.convergence import ConvergenceStrategy


class TestConvergenceStrategy:
    """Convergence strategy test suite."""

    @pytest.mark.unit
    def test_generates_signal_for_near_certain_market(self) -> None:
        """Markets near resolution with clear outcome should generate signal."""
        strategy = ConvergenceStrategy(
            {
                "min_probability_for_entry": 0.95,
                "max_days_to_resolution": 14,
                "min_spread_cents": 0.03,
            }
        )
        end_date = (datetime.now(UTC) + timedelta(days=5)).isoformat()
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.96},
                {"token_id": "no", "outcome": "No", "price": 0.04},
            ],
            "end_date_iso": end_date,
        }
        signal = strategy.evaluate(market)
        assert signal is not None
        assert signal.side == "BUY"
        assert signal.price == 0.96

    @pytest.mark.unit
    def test_rejects_market_too_far_from_resolution(self) -> None:
        """Markets far from resolution should not generate signal."""
        strategy = ConvergenceStrategy({"max_days_to_resolution": 14})
        end_date = (datetime.now(UTC) + timedelta(days=60)).isoformat()
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.96},
            ],
            "end_date_iso": end_date,
        }
        assert strategy.evaluate(market) is None

    @pytest.mark.unit
    def test_rejects_market_with_small_spread(self) -> None:
        """Markets where spread is too small should not generate signal."""
        strategy = ConvergenceStrategy({"min_spread_cents": 0.03})
        end_date = (datetime.now(UTC) + timedelta(days=5)).isoformat()
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.99},
            ],
            "end_date_iso": end_date,
        }
        # Spread = 1.0 - 0.99 = 0.01 < 0.03 minimum
        assert strategy.evaluate(market) is None

    @pytest.mark.unit
    def test_rejects_uncertain_market(self) -> None:
        """Markets where no outcome is near-certain should return None."""
        strategy = ConvergenceStrategy({"min_probability_for_entry": 0.95})
        end_date = (datetime.now(UTC) + timedelta(days=5)).isoformat()
        market = {
            "id": "test",
            "question": "Will X happen?",
            "tokens": [
                {"token_id": "yes", "outcome": "Yes", "price": 0.70},
                {"token_id": "no", "outcome": "No", "price": 0.30},
            ],
            "end_date_iso": end_date,
        }
        assert strategy.evaluate(market) is None
