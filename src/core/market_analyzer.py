"""Market analysis and opportunity detection.

Scans active Polymarket markets, evaluates liquidity, volume,
and identifies potential trading opportunities using configured strategies.
"""

from typing import Any

from src.data.market_data import MarketDataClient
from src.strategy.base_strategy import BaseStrategy, TradeSignal
from src.utils.logger import get_logger

logger = get_logger(__name__)


class MarketAnalyzer:
    """Analyzes Polymarket markets for trading opportunities."""

    def __init__(
        self,
        market_data: MarketDataClient,
        strategies: list[BaseStrategy],
        config: dict[str, Any] | None = None,
    ) -> None:
        """Initialize the market analyzer.

        Args:
            market_data: Client for fetching market data.
            strategies: List of trading strategies to evaluate.
            config: Market filtering configuration.
        """
        self._market_data = market_data
        self._strategies = strategies
        cfg = config or {}
        self._min_volume = cfg.get("min_volume", 10000)
        self._min_liquidity = cfg.get("min_liquidity", 5000)
        self._max_spread = cfg.get("max_spread", 0.10)
        self._excluded_categories: list[str] = cfg.get("excluded_categories", [])

    def scan_markets(self) -> list[dict[str, Any]]:
        """Scan all active markets and return candidates for trading.

        Returns:
            List of market dicts that pass initial filters.
        """
        try:
            markets = self._market_data.get_markets(active_only=True, limit=200)
        except Exception as e:
            logger.error("Failed to fetch markets", error=str(e))
            return []

        candidates = []
        for market in markets:
            if self._passes_filters(market):
                candidates.append(market)

        logger.info("Market scan complete", total=len(markets), candidates=len(candidates))
        return candidates

    def find_opportunities(self, markets: list[dict[str, Any]]) -> list[TradeSignal]:
        """Run all strategies against candidate markets.

        Args:
            markets: List of candidate market dicts.

        Returns:
            List of trade signals found across all strategies and markets.
        """
        signals: list[TradeSignal] = []

        for market in markets:
            # Normalize market data from Gamma API to strategy format
            market = self._normalize_market(market)
            for strategy in self._strategies:
                try:
                    signal = strategy.evaluate(market)
                    if signal:
                        signals.append(signal)
                        logger.info(
                            "Opportunity found",
                            strategy=strategy.get_name(),
                            market_id=signal.market_id,
                            edge=signal.edge,
                        )
                except Exception as e:
                    logger.warning(
                        "Strategy evaluation failed",
                        strategy=strategy.get_name(),
                        market_id=market.get("id", ""),
                        error=str(e),
                    )

        # Sort by edge (highest first)
        signals.sort(key=lambda s: s.edge, reverse=True)
        return signals

    def evaluate_liquidity(self, token_id: str) -> dict[str, Any]:
        """Evaluate the liquidity profile of a specific market token.

        Args:
            token_id: The token identifier.

        Returns:
            Liquidity metrics including spread, depth, and mid price.
        """
        try:
            book = self._market_data.get_orderbook(token_id)
            bids = book.get("bids", [])
            asks = book.get("asks", [])

            best_bid = float(bids[0]["price"]) if bids else 0
            best_ask = float(asks[0]["price"]) if asks else 1
            spread = best_ask - best_bid
            mid = (best_bid + best_ask) / 2

            bid_depth = sum(float(b["size"]) for b in bids[:5])
            ask_depth = sum(float(a["size"]) for a in asks[:5])

            return {
                "best_bid": best_bid,
                "best_ask": best_ask,
                "spread": spread,
                "mid_price": mid,
                "bid_depth_5": bid_depth,
                "ask_depth_5": ask_depth,
                "is_liquid": spread <= self._max_spread and (bid_depth + ask_depth) > 100,
            }
        except Exception as e:
            logger.warning("Liquidity evaluation failed", token_id=token_id, error=str(e))
            return {"is_liquid": False, "spread": 1.0}

    def _normalize_market(self, market: dict[str, Any]) -> dict[str, Any]:
        """Normalize Gamma API market data to the format strategies expect.

        Gamma API returns outcomePrices as JSON strings and clobTokenIds
        separately. This converts to a unified 'tokens' list.
        """
        import json as _json

        # Parse tokens from Gamma API format
        if "tokens" not in market:
            outcomes_raw = market.get("outcomes", "[]")
            prices_raw = market.get("outcomePrices", "[]")
            token_ids_raw = market.get("clobTokenIds", "[]")

            def _parse(raw: Any) -> list[Any]:
                if isinstance(raw, str):
                    return _json.loads(raw)  # type: ignore[no-any-return]
                return raw if isinstance(raw, list) else []

            try:
                outcomes = _parse(outcomes_raw)
                prices = _parse(prices_raw)
                token_ids = _parse(token_ids_raw)
            except (ValueError, TypeError):
                outcomes, prices, token_ids = [], [], []

            tokens = []
            for i, outcome in enumerate(outcomes or []):
                token = {
                    "outcome": outcome,
                    "price": float(prices[i]) if i < len(prices) else 0,
                    "token_id": token_ids[i] if i < len(token_ids) else "",
                }
                tokens.append(token)
            market["tokens"] = tokens

        # Normalize end date
        if "end_date_iso" not in market:
            market["end_date_iso"] = market.get("endDateIso", market.get("endDate", ""))

        # Extract keywords from question
        if "keywords" not in market:
            question = market.get("question", "")
            market["keywords"] = [w for w in question.split() if len(w) > 3][:5]

        return market

    def _passes_filters(self, market: dict[str, Any]) -> bool:
        """Check if a market passes basic quality filters."""
        volume = float(market.get("volume", 0) or 0)
        liquidity = float(market.get("liquidity", 0) or 0)
        category = market.get("category", "")

        if volume < self._min_volume:
            return False
        if liquidity < self._min_liquidity:
            return False
        if category in self._excluded_categories:
            return False
        return not market.get("closed", False)
