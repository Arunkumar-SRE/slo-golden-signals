# ============================================================
# test_slo.py — Automated tests for SLO calculations
#
# Run manually:  pytest test_slo.py -v
# Run by CI:     automatically on every git push
# ============================================================

import pytest

# ── Import the calculation functions from your FastAPI app ──
# We test the math directly without needing to start the server
from slo_main_prometheus import (
    get_alert_level,
    calc_burn_rate,
)


# ============================================================
# TEST GROUP 1 — Error Budget Math
# ============================================================

def test_error_budget_basic():
    """
    Given:  1,000,000 total requests, SLO = 99.9%
    Expect: allowed failures = 1,000
    """
    total_requests = 1_000_000
    slo_target     = 99.9
    slo_decimal    = slo_target / 100          # 0.999
    error_budget   = (1 - slo_decimal) * total_requests  # 1000

    assert round(error_budget, 0) == 1000, f"Expected 1000 but got {error_budget}"


def test_error_budget_99_5():
    """
    Given:  1,000,000 total requests, SLO = 99.5%
    Expect: allowed failures = 5,000
    """
    total_requests = 1_000_000
    slo_target     = 99.5
    slo_decimal    = slo_target / 100          # 0.995
    error_budget   = (1 - slo_decimal) * total_requests  # 5000

    assert round(error_budget, 0) == 5000, f"Expected 5000 but got {error_budget}"


def test_error_budget_consumed():
    """
    Given:  1,500 actual failures, 1,000 allowed
    Expect: budget consumed = 150%
    """
    actual_failures  = 1500
    allowed_failures = 1000
    consumed_pct     = (actual_failures / allowed_failures) * 100

    assert consumed_pct == 150.0, f"Expected 150.0 but got {consumed_pct}"


def test_error_budget_not_consumed():
    """
    Given:  500 actual failures, 1,000 allowed
    Expect: budget consumed = 50%
    """
    actual_failures  = 500
    allowed_failures = 1000
    consumed_pct     = (actual_failures / allowed_failures) * 100

    assert consumed_pct == 50.0, f"Expected 50.0 but got {consumed_pct}"


# ============================================================
# TEST GROUP 2 — Availability Calculation
# ============================================================

def test_availability_sli():
    """
    Given:  998,500 successful out of 1,000,000 total
    Expect: availability = 99.85%
    """
    successful = 998_500
    total      = 1_000_000
    sli        = (successful / total) * 100

    assert round(sli, 2) == 99.85, f"Expected 99.85 but got {sli}"


def test_availability_perfect():
    """
    Given:  all requests successful
    Expect: availability = 100%
    """
    successful = 1_000_000
    total      = 1_000_000
    sli        = (successful / total) * 100

    assert sli == 100.0, f"Expected 100.0 but got {sli}"


def test_availability_slo_breached():
    """
    Given:  SLI = 99.85%, SLO target = 99.9%
    Expect: SLO is breached (99.85 < 99.9)
    """
    sli        = 99.85
    slo_target = 99.9

    assert sli < slo_target, "SLO should be breached but test says passing"


def test_availability_slo_passing():
    """
    Given:  SLI = 99.95%, SLO target = 99.9%
    Expect: SLO is passing (99.95 > 99.9)
    """
    sli        = 99.95
    slo_target = 99.9

    assert sli >= slo_target, "SLO should be passing but test says breached"


# ============================================================
# TEST GROUP 3 — Burn Rate Calculation
# ============================================================

def test_burn_rate_normal():
    """
    Given:  consumed 33%, elapsed 10 of 30 days (33% of window)
    Expect: burn rate = 1.0 (consuming at exactly expected pace)
    """
    consumed_pct = 33.33
    elapsed_days = 10
    window_days  = 30

    burn_rate = calc_burn_rate(consumed_pct, elapsed_days, window_days)

    assert burn_rate == 1.0, f"Expected 1.0 but got {burn_rate}"


def test_burn_rate_high():
    """
    Given:  consumed 150%, elapsed 10 of 30 days
    Expect: burn rate = 4.5 (burning 4.5x faster than expected)

    Derivation:
      expected consumption = 10/30 x 100 = 33.33%
      burn rate = 150 / 33.33 = 4.5
    """
    consumed_pct = 150.0
    elapsed_days = 10
    window_days  = 30

    burn_rate = calc_burn_rate(consumed_pct, elapsed_days, window_days)

    assert burn_rate == 4.5, f"Expected 4.5 but got {burn_rate}"


def test_burn_rate_low():
    """
    Given:  consumed 10%, elapsed 10 of 30 days (33% of window)
    Expect: burn rate = 0.3 (burning slower than expected)
    """
    consumed_pct = 10.0
    elapsed_days = 10
    window_days  = 30

    burn_rate = calc_burn_rate(consumed_pct, elapsed_days, window_days)

    assert burn_rate == 0.3, f"Expected 0.3 but got {burn_rate}"


# ============================================================
# TEST GROUP 4 — Alert Levels
# ============================================================

def test_alert_ok():
    """
    Burn rate < 2 and consumed < 100% → should be OK
    """
    alert = get_alert_level(burn_rate=1.5, consumed_pct=50.0)
    assert alert == "OK", f"Expected OK but got {alert}"


def test_alert_warning():
    """
    Burn rate >= 2 but < 4 → should be WARNING
    """
    alert = get_alert_level(burn_rate=2.5, consumed_pct=80.0)
    assert alert == "WARNING", f"Expected WARNING but got {alert}"


def test_alert_critical():
    """
    Burn rate >= 4 → should be CRITICAL
    """
    alert = get_alert_level(burn_rate=4.5, consumed_pct=90.0)
    assert alert == "CRITICAL", f"Expected CRITICAL but got {alert}"


def test_alert_breach():
    """
    Budget consumed >= 100% → should be BREACH
    regardless of burn rate
    """
    alert = get_alert_level(burn_rate=4.5, consumed_pct=150.0)
    assert alert == "BREACH", f"Expected BREACH but got {alert}"


def test_alert_breach_overrides_critical():
    """
    Even with high burn rate, if budget > 100% → BREACH wins
    """
    alert = get_alert_level(burn_rate=10.0, consumed_pct=100.0)
    assert alert == "BREACH", f"Expected BREACH but got {alert}"


# ============================================================
# TEST GROUP 5 — Error Rate Calculation
# ============================================================

def test_error_rate_sli():
    """
    Given:  1,500 failed out of 1,000,000 total
    Expect: error rate = 0.15%
    """
    failed = 1_500
    total  = 1_000_000
    sli    = (failed / total) * 100

    assert round(sli, 4) == 0.15, f"Expected 0.15 but got {sli}"


def test_error_rate_slo_breached():
    """
    Given:  error rate = 0.15%, SLO allows max 0.1%
    Expect: SLO is breached (0.15 > 0.1)
    """
    error_rate = 0.15
    slo_target = 0.1

    assert error_rate > slo_target, "Error rate SLO should be breached"


def test_error_rate_slo_passing():
    """
    Given:  error rate = 0.05%, SLO allows max 0.1%
    Expect: SLO is passing (0.05 < 0.1)
    """
    error_rate = 0.05
    slo_target = 0.1

    assert error_rate <= slo_target, "Error rate SLO should be passing"


# ============================================================
# TEST GROUP 6 — Saturation Calculation
# ============================================================

def test_saturation_consumed():
    """
    Given:  CPU at 72%, SLO max = 80%
    Expect: budget consumed = 90%
    """
    current    = 72.0
    slo_target = 80.0
    consumed   = (current / slo_target) * 100

    assert consumed == 90.0, f"Expected 90.0 but got {consumed}"


def test_saturation_headroom():
    """
    Given:  CPU at 72%, SLO max = 80%
    Expect: headroom = 8%
    """
    current    = 72.0
    slo_target = 80.0
    headroom   = slo_target - current

    assert headroom == 8.0, f"Expected 8.0 but got {headroom}"


def test_saturation_breached():
    """
    Given:  CPU at 85%, SLO max = 80%
    Expect: SLO is breached
    """
    current    = 85.0
    slo_target = 80.0

    assert current >= slo_target, "Saturation SLO should be breached"