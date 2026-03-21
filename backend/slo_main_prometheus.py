# ============================================================
# slo_main_prometheus.py
# FastAPI backend that queries REAL Prometheus metrics
# and calculates all 4 Golden Signals automatically.
#
# No manual input needed — everything comes from Prometheus.
# ============================================================

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import httpx
import asyncio

app = FastAPI(title="SLO Golden Signals — Prometheus Edition")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Configuration ────────────────────────────────────────────
PROMETHEUS_URL = "http://localhost:9090"   # change if remote
SERVICE_NAME   = "ecommerce-checkout"       # must match job label
WINDOW_DAYS    = 30
ELAPSED_DAYS   = 1    # using 1 day window for demo (rate over time)

# ── SLO Targets ──────────────────────────────────────────────
SLO_AVAILABILITY = 99.9    # 99.9% availability
SLO_ERROR_RATE   = 0.1     # max 0.1% error rate
SLO_LATENCY      = 95.0    # 95% of requests under 200ms
SLO_SATURATION   = 80.0    # CPU must stay below 80%
LATENCY_THRESHOLD_MS = 200  # 200ms threshold


# ============================================================
# PROMETHEUS QUERY HELPER
# ============================================================

async def query_prometheus(promql: str) -> float:
    """
    Calls the Prometheus HTTP API with a PromQL query.
    Returns the numeric result.

    Prometheus API:
      GET /api/v1/query?query=<PromQL>

    Response format:
      {
        "status": "success",
        "data": {
          "result": [
            { "metric": {}, "value": [timestamp, "value"] }
          ]
        }
      }
    """
    url = f"{PROMETHEUS_URL}/api/v1/query"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params={"query": promql})

        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Prometheus returned {response.status_code}"
            )

        data = response.json()

        if data["status"] != "success":
            raise HTTPException(
                status_code=502,
                detail=f"Prometheus query failed: {data}"
            )

        results = data["data"]["result"]

        if not results:
            return 0.0   # no data = 0

        # result[0][1] is the value as a string → convert to float
        return float(results[0]["value"][1])


# ============================================================
# PROMQL QUERIES — one per metric we need
# ============================================================

def promql_total_requests(job: str) -> str:
    """Total requests in the last 5 minutes"""
    return f'sum(increase(http_requests_total{{job="{job}"}}[5m]))'

def promql_failed_requests(job: str) -> str:
    """Failed requests (5xx) in the last 5 minutes"""
    return f'sum(increase(http_requests_total{{job="{job}",status="500"}}[5m]))'

def promql_successful_requests(job: str) -> str:
    """Successful requests (2xx) in the last 5 minutes"""
    return f'sum(increase(http_requests_total{{job="{job}",status="200"}}[5m]))'

def promql_fast_requests(job: str, threshold_seconds: float) -> str:
    """Requests completed under threshold_seconds"""
    return f'sum(increase(http_request_duration_seconds_bucket{{job="{job}",le="{threshold_seconds}"}}[5m]))'

def promql_cpu_utilization(job: str) -> str:
    """Current CPU utilization percentage"""
    return f'avg(cpu_utilization_percent{{job="{job}"}})'


# ============================================================
# SHARED CALCULATION HELPERS
# ============================================================

def get_alert_level(burn_rate: float, consumed_pct: float) -> str:
    if consumed_pct >= 100: return "BREACH"
    elif burn_rate >= 4:    return "CRITICAL"
    elif burn_rate >= 2:    return "WARNING"
    else:                   return "OK"

def calc_burn_rate(consumed_pct: float, elapsed: float, window: float) -> float:
    expected = (elapsed / window) * 100
    if expected == 0: return 0.0
    return round(consumed_pct / expected, 2)

def build_steps(steps: list) -> list:
    return [
        {"n": i+1, "label": s[0], "formula": s[1], "result": s[2]}
        for i, s in enumerate(steps)
    ]


# ============================================================
# REQUEST MODEL — only needs config overrides
# ============================================================
class PrometheusRequest(BaseModel):
    prometheus_url:       Optional[str]   = PROMETHEUS_URL
    job:                  Optional[str]   = SERVICE_NAME
    window_days:          Optional[float] = WINDOW_DAYS
    elapsed_days:         Optional[float] = ELAPSED_DAYS
    availability_slo:     Optional[float] = SLO_AVAILABILITY
    error_rate_slo:       Optional[float] = SLO_ERROR_RATE
    latency_slo:          Optional[float] = SLO_LATENCY
    saturation_slo:       Optional[float] = SLO_SATURATION
    latency_threshold_ms: Optional[float] = LATENCY_THRESHOLD_MS


# ============================================================
# MAIN ENDPOINT — fetches ALL metrics and calculates ALL signals
# POST /api/prometheus/calculate-all
# ============================================================
@app.post("/api/prometheus/calculate-all")
async def calculate_all_from_prometheus(req: PrometheusRequest):
    """
    1. Queries Prometheus for all metrics
    2. Calculates all 4 golden signals
    3. Returns complete SLO analysis
    """

    # ── Step 1: Fetch all metrics from Prometheus in parallel ──
    try:
        (
            total_requests,
            failed_requests,
            successful_requests,
            fast_requests,
            cpu_utilization,
        ) = await asyncio.gather(
            query_prometheus(promql_total_requests(req.job)),
            query_prometheus(promql_failed_requests(req.job)),
            query_prometheus(promql_successful_requests(req.job)),
            query_prometheus(promql_fast_requests(req.job, req.latency_threshold_ms / 1000)),
            query_prometheus(promql_cpu_utilization(req.job)),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch from Prometheus: {str(e)}. Is Prometheus running at {req.prometheus_url}?"
        )

    # Guard against zero division
    if total_requests == 0:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for job='{req.job}'. Is the demo app running?"
        )

    # ── Step 2: Calculate Availability ──
    avail_slo_dec    = req.availability_slo / 100
    avail_budget     = (1 - avail_slo_dec) * total_requests
    avail_sli        = (successful_requests / total_requests) * 100
    avail_consumed   = (failed_requests / avail_budget) * 100 if avail_budget > 0 else 0
    avail_burn       = calc_burn_rate(avail_consumed, req.elapsed_days, req.window_days)
    avail_alert      = get_alert_level(avail_burn, avail_consumed)

    availability = {
        "signal":        "Availability",
        "source":        "Prometheus",
        "job":           req.job,
        "sli":           round(avail_sli, 4),
        "slo_target":    req.availability_slo,
        "total_requests":int(total_requests),
        "failed":        int(failed_requests),
        "error_budget":  int(avail_budget),
        "consumed_pct":  round(avail_consumed, 2),
        "burn_rate":     avail_burn,
        "alert_level":   avail_alert,
        "slo_breached":  avail_sli < req.availability_slo,
        "remaining_pct": round(max(0, 100 - avail_consumed), 2),
        "steps": build_steps([
            ("Total Requests (Prometheus)",   f"increase(http_requests_total[5m])",          f"{int(total_requests):,}"),
            ("Failed Requests (Prometheus)",  f"status=500 in last 5m",                      f"{int(failed_requests):,}"),
            ("SLO → Decimal",                 f"{req.availability_slo}% ÷ 100",              f"{avail_slo_dec}"),
            ("Error Budget",                  f"(1-{avail_slo_dec}) × {int(total_requests):,}", f"{int(avail_budget):,} allowed failures"),
            ("SLI (Availability)",            f"{int(successful_requests):,} ÷ {int(total_requests):,} × 100", f"{round(avail_sli,4)}%"),
            ("Budget Consumed",               f"{int(failed_requests):,} ÷ {int(avail_budget):,} × 100",       f"{round(avail_consumed,2)}%"),
            ("Burn Rate",                     f"{round(avail_consumed,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%", f"{avail_burn}×"),
            ("SLO Status",                    f"{round(avail_sli,4)}% vs target {req.availability_slo}%",       "BREACHED ❌" if avail_sli < req.availability_slo else "PASSING ✅"),
        ])
    }

    # ── Step 3: Calculate Error Rate ──
    err_sli       = (failed_requests / total_requests) * 100
    err_budget    = (req.error_rate_slo / 100) * total_requests
    err_consumed  = (failed_requests / err_budget) * 100 if err_budget > 0 else 0
    err_burn      = calc_burn_rate(err_consumed, req.elapsed_days, req.window_days)
    err_alert     = get_alert_level(err_burn, err_consumed)

    error_rate = {
        "signal":       "Error Rate",
        "source":       "Prometheus",
        "job":          req.job,
        "sli":          round(err_sli, 4),
        "slo_target":   req.error_rate_slo,
        "error_budget": int(err_budget),
        "consumed_pct": round(err_consumed, 2),
        "burn_rate":    err_burn,
        "alert_level":  err_alert,
        "slo_breached": err_sli > req.error_rate_slo,
        "remaining_pct":round(max(0, 100 - err_consumed), 2),
        "steps": build_steps([
            ("Failed Requests (Prometheus)", f"status=500 in last 5m",                           f"{int(failed_requests):,}"),
            ("SLI (Error Rate)",             f"{int(failed_requests):,} ÷ {int(total_requests):,} × 100", f"{round(err_sli,4)}%"),
            ("Error Budget",                 f"({req.error_rate_slo}% ÷ 100) × {int(total_requests):,}",  f"{int(err_budget):,} allowed failures"),
            ("Budget Consumed",              f"{int(failed_requests):,} ÷ {int(err_budget):,} × 100",      f"{round(err_consumed,2)}%"),
            ("Burn Rate",                    f"{round(err_consumed,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%", f"{err_burn}×"),
            ("SLO Status",                   f"Error rate {round(err_sli,4)}% vs max {req.error_rate_slo}%", "BREACHED ❌" if err_sli > req.error_rate_slo else "PASSING ✅"),
        ])
    }

    # ── Step 4: Calculate Latency ──
    slow_requests   = total_requests - fast_requests
    lat_sli         = (fast_requests / total_requests) * 100
    lat_budget      = (1 - req.latency_slo / 100) * total_requests
    lat_consumed    = (slow_requests / lat_budget) * 100 if lat_budget > 0 else 0
    lat_burn        = calc_burn_rate(lat_consumed, req.elapsed_days, req.window_days)
    lat_alert       = get_alert_level(lat_burn, lat_consumed)

    latency = {
        "signal":        "Latency",
        "source":        "Prometheus",
        "job":           req.job,
        "sli":           round(lat_sli, 4),
        "slo_target":    req.latency_slo,
        "threshold_ms":  req.latency_threshold_ms,
        "slow_requests": int(slow_requests),
        "error_budget":  int(lat_budget),
        "consumed_pct":  round(lat_consumed, 2),
        "burn_rate":     lat_burn,
        "alert_level":   lat_alert,
        "slo_breached":  lat_sli < req.latency_slo,
        "remaining_pct": round(max(0, 100 - lat_consumed), 2),
        "steps": build_steps([
            ("Fast Requests (Prometheus)",  f"duration < {req.latency_threshold_ms}ms in last 5m",       f"{int(fast_requests):,}"),
            ("Slow Requests",               f"{int(total_requests):,} − {int(fast_requests):,}",         f"{int(slow_requests):,}"),
            ("SLI (Latency)",               f"{int(fast_requests):,} ÷ {int(total_requests):,} × 100",   f"{round(lat_sli,4)}%"),
            ("Error Budget",                f"(1 − {req.latency_slo}%) × {int(total_requests):,}",       f"{int(lat_budget):,} allowed slow requests"),
            ("Budget Consumed",             f"{int(slow_requests):,} ÷ {int(lat_budget):,} × 100",       f"{round(lat_consumed,2)}%"),
            ("Burn Rate",                   f"{round(lat_consumed,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%", f"{lat_burn}×"),
            ("SLO Status",                  f"{round(lat_sli,4)}% fast vs target {req.latency_slo}%",    "BREACHED ❌" if lat_sli < req.latency_slo else "PASSING ✅"),
        ])
    }

    # ── Step 5: Calculate Saturation ──
    sat_sli      = round(cpu_utilization, 2)
    sat_consumed = (cpu_utilization / req.saturation_slo) * 100
    sat_burn     = calc_burn_rate(sat_consumed, req.elapsed_days, req.window_days)
    sat_alert    = get_alert_level(sat_burn, sat_consumed)
    headroom     = req.saturation_slo - cpu_utilization

    saturation = {
        "signal":        "Saturation",
        "source":        "Prometheus",
        "job":           req.job,
        "resource_type": "CPU",
        "sli":           sat_sli,
        "slo_target":    req.saturation_slo,
        "headroom":      round(headroom, 2),
        "consumed_pct":  round(sat_consumed, 2),
        "burn_rate":     sat_burn,
        "alert_level":   sat_alert,
        "slo_breached":  cpu_utilization >= req.saturation_slo,
        "remaining_pct": round(max(0, 100 - sat_consumed), 2),
        "steps": build_steps([
            ("CPU Utilization (Prometheus)", f"avg(cpu_utilization_percent)",               f"{sat_sli}%"),
            ("SLO Target",                  f"CPU must stay below",                         f"{req.saturation_slo}%"),
            ("Budget Consumed",             f"{sat_sli}% ÷ {req.saturation_slo}% × 100",   f"{round(sat_consumed,2)}%"),
            ("Headroom",                    f"{req.saturation_slo}% − {sat_sli}%",          f"{round(headroom,2)}% remaining"),
            ("Burn Rate",                   f"{round(sat_consumed,2)}% ÷ {round((req.elapsed_days/req.window_days)*100,2)}%", f"{sat_burn}×"),
            ("SLO Status",                  f"{sat_sli}% vs max {req.saturation_slo}%",     "BREACHED ❌" if cpu_utilization >= req.saturation_slo else "PASSING ✅"),
        ])
    }

    # ── Step 6: Overall health ──
    all_signals    = [availability, error_rate, latency, saturation]
    alert_priority = {"BREACH": 4, "CRITICAL": 3, "WARNING": 2, "OK": 1}
    worst          = max(all_signals, key=lambda s: alert_priority[s["alert_level"]])

    return {
        "source":         "Prometheus",
        "prometheus_url": req.prometheus_url,
        "job":            req.job,
        "overall_health": worst["alert_level"],
        "availability":   availability,
        "error_rate":     error_rate,
        "latency":        latency,
        "saturation":     saturation,
    }


# ── Health check ──
@app.get("/api/health")
def health():
    return {"status": "OK", "mode": "Prometheus", "url": PROMETHEUS_URL}


# ── Check Prometheus connectivity ──
@app.get("/api/prometheus/status")
async def prometheus_status():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{PROMETHEUS_URL}/-/healthy")
            return {"connected": r.status_code == 200, "url": PROMETHEUS_URL}
    except Exception as e:
        return {"connected": False, "url": PROMETHEUS_URL, "error": str(e)}
