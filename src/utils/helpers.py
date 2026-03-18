"""Common utility functions used across the bot."""

from datetime import UTC, datetime


def kelly_criterion(probability: float, odds: float, fraction: float = 0.25) -> float:
    """Calculate Kelly Criterion bet size.

    Uses fractional Kelly (default 1/4 Kelly) for conservative sizing.

    Full Kelly: f = (p * b - q) / b
    Where: p = probability of winning, b = net odds, q = 1 - p

    Args:
        probability: Estimated true probability of winning (0-1).
        odds: Decimal odds of the bet (payout / stake).
        fraction: Kelly fraction to use (0.25 = quarter Kelly).

    Returns:
        Recommended bet size as fraction of bankroll (0 if no edge).
    """
    if probability <= 0 or probability >= 1 or odds <= 0:
        return 0.0
    q = 1 - probability
    b = odds - 1  # Net odds
    if b <= 0:
        return 0.0
    full_kelly = (probability * b - q) / b
    if full_kelly <= 0:
        return 0.0
    return full_kelly * fraction


def calculate_expected_value(probability: float, payout: float, cost: float) -> float:
    """Calculate expected value of a trade.

    Args:
        probability: Estimated probability of the outcome (0-1).
        payout: Payout if the outcome occurs.
        cost: Cost to enter the position.

    Returns:
        Expected value of the trade.
    """
    return (probability * payout) - cost


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


def now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(UTC).isoformat()


def edge_to_odds(market_price: float) -> float:
    """Convert a market price (0-1) to decimal odds.

    Args:
        market_price: The market price (implied probability).

    Returns:
        Decimal odds (e.g., price 0.50 → odds 2.0).
    """
    if market_price <= 0 or market_price >= 1:
        return 0.0
    return 1.0 / market_price
