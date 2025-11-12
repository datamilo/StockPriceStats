"""
Financial Constants

Single source of truth for financial calculation constants used throughout
the Swedish put options analysis system.

These constants ensure consistency across:
- Time-to-expiry calculations (DaysToExpiry / TRADING_DAYS_PER_YEAR)
- Black-Scholes pricing (T = DaysToExpiry / TRADING_DAYS_PER_YEAR)
- Implied volatility annualization (σ_annual = σ_daily * sqrt(TRADING_DAYS_PER_YEAR))
- Greeks calculations (all time-dependent Greeks use this convention)

CRITICAL: All parts of the system must use the same denominator to avoid
mixing trading-day and calendar-day conventions in calculations.
"""

# ============================================================================
# TIME-TO-EXPIRY CONSTANT (Critical for Options Pricing)
# ============================================================================

TRADING_DAYS_PER_YEAR = 252
"""
Number of trading days (business days) per year in Swedish market.

This is the standard convention for options pricing:
- Used in Black-Scholes model for time parameter T
- Used for annualizing volatility: σ_annual = σ_daily * sqrt(252)
- Must be consistent with DaysToExpiry calculations (business days only)

Reference:
- NYSE: 252 days (standard)
- Swedish exchanges: ~252 business days (weekends + Swedish holidays excluded)

USAGE:
  from constants import TRADING_DAYS_PER_YEAR

  # Calculate time-to-expiry in years
  years_to_expiry = days_to_expiry / TRADING_DAYS_PER_YEAR

  # Annualize daily volatility
  annual_volatility = daily_volatility * math.sqrt(TRADING_DAYS_PER_YEAR)

  # Pass to Black-Scholes
  T = days_to_expiry / TRADING_DAYS_PER_YEAR
  price = black_scholes(S, K, r, sigma, T, option_type='put')

CRITICAL: This constant was chosen to match:
1. DaysToExpiry calculations which use business days (numpy.busday_count)
2. Implied volatility annualization (IV historical uses 252)
3. All Black-Scholes and Greek calculations
"""

# ============================================================================
# Risk-Free Rate Convention
# ============================================================================

CONTINUOUS_COMPOUNDING = True
"""
Whether to use continuous compounding for risk-free rate.

If True: Use exp(r * T) convention in Black-Scholes
If False: Use (1 + r)^T convention

Standard convention in finance is continuous compounding.
"""

# ============================================================================
# Implied Volatility Storage Convention
# ============================================================================

IV_ANNUALIZATION_BASIS = TRADING_DAYS_PER_YEAR
"""
Number of trading days used when annualizing stored implied volatility.

Stored IV is typically calculated as:
  σ_stored = σ_daily * sqrt(IV_ANNUALIZATION_BASIS)

This is aliased to TRADING_DAYS_PER_YEAR for clarity.
Always use TRADING_DAYS_PER_YEAR as the canonical source.

Current status: IV is stored using 252 (trading days basis)
"""

# ============================================================================
# Volatility Calculation Standard
# ============================================================================

VOLATILITY_ANNUALIZATION_CONSTANT = TRADING_DAYS_PER_YEAR
"""
Alias for TRADING_DAYS_PER_YEAR for clarity in volatility calculations.

Usage: annual_vol = daily_vol * math.sqrt(VOLATILITY_ANNUALIZATION_CONSTANT)

Note: Always use TRADING_DAYS_PER_YEAR as the canonical source.
This alias exists for code clarity only.
"""


def validate_constants():
    """
    Verify constants are internally consistent.

    This function is designed to be safe for import-time calls but can also
    be called explicitly from tests.

    Returns:
        bool: True if validation passed

    Notes:
        - Does not raise exceptions on import (safe for production)
        - Logs warnings via standard logging module
        - Tests will explicitly call this and check the result
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        # Ensure annualization basis matches trading days
        assert IV_ANNUALIZATION_BASIS == TRADING_DAYS_PER_YEAR, \
            f"IV annualization basis ({IV_ANNUALIZATION_BASIS}) must equal " \
            f"trading days per year ({TRADING_DAYS_PER_YEAR})"

        # Ensure volatility annualization matches trading days
        assert VOLATILITY_ANNUALIZATION_CONSTANT == TRADING_DAYS_PER_YEAR, \
            f"Volatility annualization constant ({VOLATILITY_ANNUALIZATION_CONSTANT}) " \
            f"must equal trading days per year ({TRADING_DAYS_PER_YEAR})"

        return True
    except AssertionError as e:
        # Log but don't fail on import - allows partial initialization
        # Tests will explicitly call validate_constants() and check the result
        logger.warning(f"Constants validation failed: {e}")
        return False


# Safe import-time validation (won't block imports if validation fails)
_validation_passed = validate_constants()
