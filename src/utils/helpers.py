# TODO: Implement in Phase 3
"""Common utility functions used across the bot."""


def kelly_criterion(probability: float, odds: float, fraction: float = 0.25) -> float:
    """Calculate Kelly Criterion bet size.

    Uses fractional Kelly (default 1/4 Kelly) for conservative sizing.

    Args:
        probability: Estimated true probability of winning.
        odds: Decimal odds of the bet.
        fraction: Kelly fraction to use (0.25 = quarter Kelly).

    Returns:
        Recommended bet size as fraction of bankroll.
    """
    raise NotImplementedError("Phase 4")


def calculate_expected_value(probability: float, payout: float, cost: float) -> float:
    """Calculate expected value of a trade.

    Args:
        probability: Estimated probability of the outcome.
        payout: Payout if the outcome occurs.
        cost: Cost to enter the position.

    Returns:
        Expected value of the trade.
    """
    raise NotImplementedError("Phase 4")


def format_usd(amount: float) -> str:
    """Format a number as USD string.

    Args:
        amount: Dollar amount.

    Returns:
        Formatted string like "$1,234.56".
    """
    return f"${amount:,.2f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero.

    Args:
        numerator: The numerator.
        denominator: The denominator.
        default: Value to return if denominator is zero.

    Returns:
        Result of division or default value.
    """
    if denominator == 0:
        return default
    return numerator / denominator
