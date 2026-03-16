# ============================================================
# SLO Golden Signals — FastAPI Backend
# Calculates: Availability, Error Rate, Latency, Saturation
# ============================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

app = FastAPI(title="SLO Golden Signals API", version="1.0.0")

# ── CORS: allows React (port 3000) to call this API (port 8000) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SHARED HELPER FUNCTIONS
# ============================================================

def get_alert_level(burn_rate: float, consumed_pct: float) -> str:
    """
    Determines alert level based on burn rate and budget consumed.
    Same logic applies to ALL 4 signals.
    """
    if consumed_pct >= 100:  return "BREACH"
    elif burn_rate >= 4:     return "CRITICAL"
    elif burn_rate >= 2:     return "WARNING"
    else:                    return "OK"


def calc_burn_rate(consumed_pct: float, elapsed_days: float, window_days: float) -> float:
    """
    Burn Rate = how fast budget is burning vs expected pace.

    Expected consumption = elapsed / window
    e.g. 10 days into 30-day window = 33% should be consumed

    Burn Rate = actual consumed% / expected consumed%
    e.g. 150% consumed / 33% expected = 4.5x burn rate
    """
    expected_pct = (elapsed_days / window_days) * 100   # e.g. 33.33%
    if expected_pct == 0:
        return 0.0
    return round(consumed_pct / expected_pct, 2)


def build_steps(steps: list) -> list:
    """
    Formats derivation steps for the frontend.
    Each step has: step number, label, formula, result
    """
    return [
        {"n": i + 1, "label": s[0], "formula": s[1], "result": s[2]}
        for i, s in enumerate(steps)
    ]


# ============================================================
# REQUEST MODELS (Pydantic validates inputs automatically)
# ============================================================

class AvailabilityRequest(BaseModel):
    total_requests:      float   # e.g. 1,000,000
    successful_requests: float   # e.g. 998,500
    slo_target:          float   # e.g. 99.9  (as percentage)
    window_days:         float   # e.g. 30
    elapsed_days:        float   # e.g. 10
    service_name:        Optional[str] = "My Service"
    cuj:                 Optional[str] = "User Login"


class ErrorRateRequest(BaseModel):
    total_requests:  float   # e.g. 1,000,000
    failed_requests: float   # e.g. 1,500
    slo_target:      float   # e.g. 0.1 (allowed error % — must stay BELOW this)
    window_days:     float
    elapsed_days:    float
    service_name:    Optional[str] = "My Service"
    cuj:             Optional[str] = "User Login"


class LatencyRequest(BaseModel):
    total_requests:          float   # e.g. 1,000,000
    requests_under_threshold: float  # e.g. 950,000 (completed under 200ms)
    threshold_ms:            float   # e.g. 200 (the latency target in ms)
    slo_target:              float   # e.g. 95 (95% of requests must be fast)
    window_days:             float
    elapsed_days:            float
    service_name:            Optional[str] = "My Service"
    cuj:                     Optional[str] = "Checkout Page Load"


class SaturationRequest(BaseModel):
    current_utilization: float   # e.g. 72 (current CPU or memory %)
    slo_target:          float   # e.g. 80 (must stay BELOW this %)
    window_days:         float
    elapsed_days:        float
    resource_type:       Optional[str] = "CPU"   # CPU or Memory
    service_name:        Optional[str] = "My Service"
    cuj:                 Optional[str] = "API Server"


# ============================================================
# ENDPOINT 1 — AVAILABILITY
# POST /api/availability
# ============================================================
@app.post("/api/availability")
def calculate_availability(req: AvailabilityRequest):
    """
    Availability = Successful Requests / Total Requests

    Example:
      total      = 1,000,000
      successful = 998,500
      failed     = 1,500
      SLI        = 998500 / 1000000 = 99.85%
      SLO        = 99.9%
      budget     = 0.001 × 1,000,000 = 1,000 allowed failures
      consumed   = 1,500 / 1,000 = 150%  ← BREACHED
    """

    # Step 1 — SLO to decimal
    slo_decimal  = req.slo_target / 100                          # 0.999

    # Step 2 — How many failures are allowed (error budget)
    failed       = req.total_requests - req.successful_requests  # 1,500
    error_budget = (1 - slo_decimal) * req.total_requests        # 1,000

    # Step 3 — Actual availability (SLI)
    sli          = (req.successful_requests / req.total_requests) * 100  # 99.85%

    # Step 4 — Budget consumed
    consumed_pct = (failed / error_budget) * 100                 # 150%

    # Step 5 — Burn rate
    burn_rate    = calc_burn_rate(consumed_pct, req.elapsed_days, req.window_days)

    # Step 6 — Alert level
    alert        = get_alert_level(burn_rate, consumed_pct)

    # Step-by-step derivation for UI display
    steps = build_steps([
        ("SLO → Decimal",        f"{req.slo_target}% ÷ 100",                                         f"{slo_decimal}"),
        ("Failed Requests",      f"{int(req.total_requests):,} − {int(req.successful_requests):,}",   f"{int(failed):,}"),
        ("Error Budget",         f"(1 − {slo_decimal}) × {int(req.total_requests):,}",               f"{int(error_budget):,} allowed failures"),
        ("SLI (Availability)",   f"{int(req.successful_requests):,} ÷ {int(req.total_requests):,} × 100",  f"{round(sli, 4)}%"),
        ("Budget Consumed",      f"{int(failed):,} ÷ {int(error_budget):,} × 100",                   f"{round(consumed_pct, 2)}%"),
        ("Expected Consumption", f"{req.elapsed_days} ÷ {req.window_days} × 100",                    f"{round((req.elapsed_days/req.window_days)*100, 2)}%"),
        ("Burn Rate",            f"{round(consumed_pct,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%",  f"{burn_rate}×"),
        ("SLO Status",           f"{round(sli,4)}% vs target {req.slo_target}%",                     "BREACHED ❌" if sli < req.slo_target else "PASSING ✅"),
    ])

    return {
        "signal":         "Availability",
        "service":        req.service_name,
        "cuj":            req.cuj,
        "sli":            round(sli, 4),
        "slo_target":     req.slo_target,
        "slo_decimal":    slo_decimal,
        "failed":         int(failed),
        "error_budget":   int(error_budget),
        "consumed_pct":   round(consumed_pct, 2),
        "burn_rate":      burn_rate,
        "alert_level":    alert,
        "slo_breached":   sli < req.slo_target,
        "remaining_pct":  round(max(0, 100 - consumed_pct), 2),
        "steps":          steps,
    }


# ============================================================
# ENDPOINT 2 — ERROR RATE
# POST /api/error-rate
# ============================================================
@app.post("/api/error-rate")
def calculate_error_rate(req: ErrorRateRequest):
    """
    Error Rate = Failed Requests / Total Requests × 100

    Note: For error rate, the SLO is a MAX threshold.
    e.g. SLO = 0.1% means error rate must stay BELOW 0.1%

    Example:
      total   = 1,000,000
      failed  = 1,500
      SLI     = 1500 / 1000000 × 100 = 0.15%
      SLO     = 0.1% (must stay below this)
      budget  = 0.001 × 1,000,000 = 1,000 allowed failures
      consumed = 1,500 / 1,000 = 150%  ← BREACHED
    """

    # Step 1 — Error rate (SLI)
    sli          = (req.failed_requests / req.total_requests) * 100   # 0.15%

    # Step 2 — Allowed failures (budget)
    error_budget = (req.slo_target / 100) * req.total_requests        # 1,000

    # Step 3 — Budget consumed
    consumed_pct = (req.failed_requests / error_budget) * 100         # 150%

    # Step 4 — Burn rate and alert
    burn_rate    = calc_burn_rate(consumed_pct, req.elapsed_days, req.window_days)
    alert        = get_alert_level(burn_rate, consumed_pct)

    steps = build_steps([
        ("SLI (Error Rate)",     f"{int(req.failed_requests):,} ÷ {int(req.total_requests):,} × 100",   f"{round(sli, 4)}%"),
        ("Error Budget",         f"({req.slo_target}% ÷ 100) × {int(req.total_requests):,}",            f"{int(error_budget):,} allowed failures"),
        ("Budget Consumed",      f"{int(req.failed_requests):,} ÷ {int(error_budget):,} × 100",         f"{round(consumed_pct, 2)}%"),
        ("Expected Consumption", f"{req.elapsed_days} ÷ {req.window_days} × 100",                       f"{round((req.elapsed_days/req.window_days)*100, 2)}%"),
        ("Burn Rate",            f"{round(consumed_pct,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%",   f"{burn_rate}×"),
        ("SLO Status",           f"Error rate {round(sli,4)}% vs max allowed {req.slo_target}%",        "BREACHED ❌" if sli > req.slo_target else "PASSING ✅"),
    ])

    return {
        "signal":         "Error Rate",
        "service":        req.service_name,
        "cuj":            req.cuj,
        "sli":            round(sli, 4),
        "slo_target":     req.slo_target,
        "error_budget":   int(error_budget),
        "consumed_pct":   round(consumed_pct, 2),
        "burn_rate":      burn_rate,
        "alert_level":    alert,
        "slo_breached":   sli > req.slo_target,
        "remaining_pct":  round(max(0, 100 - consumed_pct), 2),
        "steps":          steps,
    }


# ============================================================
# ENDPOINT 3 — LATENCY
# POST /api/latency
# ============================================================
@app.post("/api/latency")
def calculate_latency(req: LatencyRequest):
    """
    Latency SLO = % of requests that complete under threshold_ms

    Example:
      total     = 1,000,000
      fast      = 950,000  (completed under 200ms)
      slow      = 50,000
      SLI       = 950,000 / 1,000,000 × 100 = 95%
      SLO       = 95% must be fast
      budget    = 0.05 × 1,000,000 = 50,000 allowed slow requests
      consumed  = 50,000 / 50,000 = 100%  ← at the limit
    """

    # Step 1 — Slow requests
    slow_requests = req.total_requests - req.requests_under_threshold   # 50,000

    # Step 2 — SLI (% of fast requests)
    sli           = (req.requests_under_threshold / req.total_requests) * 100  # 95%

    # Step 3 — Error budget (allowed slow requests)
    error_budget  = (1 - req.slo_target / 100) * req.total_requests    # 50,000

    # Step 4 — Budget consumed
    consumed_pct  = (slow_requests / error_budget) * 100 if error_budget > 0 else 0

    # Step 5 — Burn rate and alert
    burn_rate     = calc_burn_rate(consumed_pct, req.elapsed_days, req.window_days)
    alert         = get_alert_level(burn_rate, consumed_pct)

    steps = build_steps([
        ("Slow Requests",        f"{int(req.total_requests):,} − {int(req.requests_under_threshold):,}",       f"{int(slow_requests):,} requests over {req.threshold_ms}ms"),
        ("SLI (Latency)",        f"{int(req.requests_under_threshold):,} ÷ {int(req.total_requests):,} × 100", f"{round(sli, 4)}% under {req.threshold_ms}ms"),
        ("Error Budget",         f"(1 − {req.slo_target}%) × {int(req.total_requests):,}",                    f"{int(error_budget):,} allowed slow requests"),
        ("Budget Consumed",      f"{int(slow_requests):,} ÷ {int(error_budget):,} × 100",                     f"{round(consumed_pct, 2)}%"),
        ("Expected Consumption", f"{req.elapsed_days} ÷ {req.window_days} × 100",                             f"{round((req.elapsed_days/req.window_days)*100, 2)}%"),
        ("Burn Rate",            f"{round(consumed_pct,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%",  f"{burn_rate}×"),
        ("SLO Status",           f"{round(sli,4)}% fast vs target {req.slo_target}%",                         "BREACHED ❌" if sli < req.slo_target else "PASSING ✅"),
    ])

    return {
        "signal":         "Latency",
        "service":        req.service_name,
        "cuj":            req.cuj,
        "sli":            round(sli, 4),
        "slo_target":     req.slo_target,
        "threshold_ms":   req.threshold_ms,
        "slow_requests":  int(slow_requests),
        "error_budget":   int(error_budget),
        "consumed_pct":   round(consumed_pct, 2),
        "burn_rate":      burn_rate,
        "alert_level":    alert,
        "slo_breached":   sli < req.slo_target,
        "remaining_pct":  round(max(0, 100 - consumed_pct), 2),
        "steps":          steps,
    }


# ============================================================
# ENDPOINT 4 — SATURATION
# POST /api/saturation
# ============================================================
@app.post("/api/saturation")
def calculate_saturation(req: SaturationRequest):
    """
    Saturation = current resource utilization vs max allowed

    Example:
      current  = 72%  (current CPU usage)
      SLO      = 80%  (must stay below 80%)
      consumed = 72 / 80 × 100 = 90%  ← WARNING, getting close
    """

    # Step 1 — SLI is simply the current utilization
    sli           = req.current_utilization   # 72%

    # Step 2 — Budget consumed (how close to the limit)
    consumed_pct  = (req.current_utilization / req.slo_target) * 100   # 90%

    # Step 3 — Headroom remaining
    headroom      = req.slo_target - req.current_utilization            # 8%

    # Step 4 — Burn rate and alert
    burn_rate     = calc_burn_rate(consumed_pct, req.elapsed_days, req.window_days)
    alert         = get_alert_level(burn_rate, consumed_pct)

    steps = build_steps([
        ("SLI (Saturation)",     f"Current {req.resource_type} usage",                                 f"{sli}%"),
        ("SLO Target",           f"{req.resource_type} must stay below",                               f"{req.slo_target}%"),
        ("Budget Consumed",      f"{req.current_utilization}% ÷ {req.slo_target}% × 100",             f"{round(consumed_pct, 2)}%"),
        ("Headroom",             f"{req.slo_target}% − {req.current_utilization}%",                   f"{round(headroom, 2)}% remaining"),
        ("Expected Consumption", f"{req.elapsed_days} ÷ {req.window_days} × 100",                     f"{round((req.elapsed_days/req.window_days)*100, 2)}%"),
        ("Burn Rate",            f"{round(consumed_pct,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%",   f"{burn_rate}×"),
        ("SLO Status",           f"{sli}% utilization vs max {req.slo_target}%",                      "BREACHED ❌" if sli >= req.slo_target else "PASSING ✅"),
    ])

    return {
        "signal":         "Saturation",
        "service":        req.service_name,
        "cuj":            req.cuj,
        "resource_type":  req.resource_type,
        "sli":            round(sli, 2),
        "slo_target":     req.slo_target,
        "headroom":       round(headroom, 2),
        "consumed_pct":   round(consumed_pct, 2),
        "burn_rate":      burn_rate,
        "alert_level":    alert,
        "slo_breached":   sli >= req.slo_target,
        "remaining_pct":  round(max(0, 100 - consumed_pct), 2),
        "steps":          steps,
    }


# ============================================================
# ENDPOINT 5 — CALCULATE ALL 4 SIGNALS AT ONCE
# POST /api/calculate-all
# ============================================================
class AllSignalsRequest(BaseModel):
    # Shared
    service_name:  Optional[str] = "E-Commerce Checkout"
    cuj:           Optional[str] = "User Checkout Flow"
    window_days:   float = 30
    elapsed_days:  float = 10

    # Availability
    total_requests:       float = 1_000_000
    successful_requests:  float = 998_500
    availability_slo:     float = 99.9

    # Error Rate
    failed_requests:      float = 1_500
    error_rate_slo:       float = 0.1

    # Latency
    requests_under_threshold: float = 950_000
    threshold_ms:             float = 200
    latency_slo:              float = 95.0

    # Saturation
    current_utilization:  float = 72.0
    saturation_slo:       float = 80.0
    resource_type:        Optional[str] = "CPU"


@app.post("/api/calculate-all")
def calculate_all(req: AllSignalsRequest):
    """
    Single endpoint that calculates all 4 golden signals at once.
    React calls this ONE endpoint and gets everything back.
    """

    avail   = calculate_availability(AvailabilityRequest(
        total_requests=req.total_requests,
        successful_requests=req.successful_requests,
        slo_target=req.availability_slo,
        window_days=req.window_days,
        elapsed_days=req.elapsed_days,
        service_name=req.service_name,
        cuj=req.cuj,
    ))

    err     = calculate_error_rate(ErrorRateRequest(
        total_requests=req.total_requests,
        failed_requests=req.failed_requests,
        slo_target=req.error_rate_slo,
        window_days=req.window_days,
        elapsed_days=req.elapsed_days,
        service_name=req.service_name,
        cuj=req.cuj,
    ))

    lat     = calculate_latency(LatencyRequest(
        total_requests=req.total_requests,
        requests_under_threshold=req.requests_under_threshold,
        threshold_ms=req.threshold_ms,
        slo_target=req.latency_slo,
        window_days=req.window_days,
        elapsed_days=req.elapsed_days,
        service_name=req.service_name,
        cuj=req.cuj,
    ))

    sat     = calculate_saturation(SaturationRequest(
        current_utilization=req.current_utilization,
        slo_target=req.saturation_slo,
        window_days=req.window_days,
        elapsed_days=req.elapsed_days,
        resource_type=req.resource_type,
        service_name=req.service_name,
        cuj=req.cuj,
    ))

    # Overall health — if ANY signal is breached, overall is breached
    all_signals   = [avail, err, lat, sat]
    alert_priority = {"BREACH": 4, "CRITICAL": 3, "WARNING": 2, "OK": 1}
    worst_alert    = max(all_signals, key=lambda s: alert_priority[s["alert_level"]])

    return {
        "service":          req.service_name,
        "cuj":              req.cuj,
        "overall_health":   worst_alert["alert_level"],
        "availability":     avail,
        "error_rate":       err,
        "latency":          lat,
        "saturation":       sat,
    }


# ── Health check ──
@app.get("/api/health")
def health():
    return {"status": "OK", "service": "SLO Golden Signals API"}
