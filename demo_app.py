# ============================================================
# demo_app.py — Simulates a real service sending metrics
# to Prometheus.
#
# Generates realistic:
#   - HTTP request counts (success + failures)
#   - Latency histograms
#   - CPU saturation metrics
#
# Run: python demo_app.py
# Metrics visible at: http://localhost:8001/metrics
# ============================================================

import time
import random
import threading
from prometheus_client import (
    start_http_server,
    Counter,
    Histogram,
    Gauge,
    REGISTRY
)

# ── Define metrics ──────────────────────────────────────────

# Counts every HTTP request
# Labels: status (200/500), endpoint (/checkout, /login)
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['status', 'endpoint', 'job']
)

# Tracks how long requests take (in seconds)
# Buckets: we care most about 200ms threshold
http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['endpoint', 'job'],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0]
)

# Current CPU utilization (0-100%)
cpu_utilization = Gauge(
    'cpu_utilization_percent',
    'Current CPU utilization percentage',
    ['job']
)

# ── Traffic simulation ───────────────────────────────────────

SERVICE_NAME = "ecommerce-checkout"

def simulate_traffic():
    """
    Simulates realistic e-commerce traffic patterns.

    Every second:
    - Generates 50-200 requests
    - 98.5% succeed (200), 1.5% fail (500)
    - 95% of requests complete under 200ms
    - CPU fluctuates between 60-85%
    """
    print(f"🚀 Demo app running — sending metrics to Prometheus")
    print(f"📊 Metrics endpoint: http://localhost:8001/metrics")
    print(f"🛑 Press Ctrl+C to stop\n")

    while True:
        # Simulate a batch of requests every second
        batch_size = random.randint(50, 200)

        for _ in range(batch_size):
            endpoint = random.choice(['/checkout', '/login', '/cart', '/payment'])

            # 98.5% success rate → generates ~1.5% error rate
            if random.random() < 0.985:
                status = '200'
                # 95% of requests are fast (under 200ms)
                if random.random() < 0.95:
                    latency = random.uniform(0.01, 0.19)   # fast: 10-190ms
                else:
                    latency = random.uniform(0.2, 2.0)     # slow: 200ms-2s
            else:
                status = '500'
                latency = random.uniform(0.1, 1.0)

            # Record the request
            http_requests_total.labels(
                status=status,
                endpoint=endpoint,
                job=SERVICE_NAME
            ).inc()

            # Record the latency
            http_request_duration_seconds.labels(
                endpoint=endpoint,
                job=SERVICE_NAME
            ).observe(latency)

        # Simulate CPU fluctuating between 60-85%
        cpu_pct = random.uniform(60, 85)
        cpu_utilization.labels(job=SERVICE_NAME).set(cpu_pct)

        time.sleep(1)   # wait 1 second before next batch


if __name__ == '__main__':
    # Start metrics server on port 8001
    # Prometheus will scrape http://localhost:8001/metrics
    start_http_server(8001)

    # Start simulating traffic in background
    thread = threading.Thread(target=simulate_traffic, daemon=True)
    thread.start()

    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n✅ Demo app stopped")
