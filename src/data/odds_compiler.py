# TODO: Implement in Phase 4
"""Compile "true odds" from external data sources.

Aggregates probability estimates from multiple external sources
to build an independent probability estimate for comparison with
Polymarket prices.
"""


class OddsCompiler:
    """Compiles true probability estimates from external sources."""

    def compile_probability(self, market_id: str) -> float:
        """Compile a true probability estimate for a market.

        Args:
            market_id: The market identifier.

        Returns:
            Estimated true probability (0-1).
        """
        raise NotImplementedError("Phase 4")

    def get_source_estimates(self, market_id: str) -> list[dict[str, float]]:
        """Get individual probability estimates from each source.

        Args:
            market_id: The market identifier.

        Returns:
            List of dicts with source name and probability estimate.
        """
        raise NotImplementedError("Phase 4")
