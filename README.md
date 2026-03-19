# SLO Golden Signals Dashboard

A full-stack SRE tool to calculate and visualize SLOs based on Google's 4 Golden Signals.
Define Critical User Journeys (CUJ), set SLO targets, compute error budgets, track consumption and burn rates with alert levels.

---

## Golden Signals and Formulas

| Signal | SLI Formula | Example SLO |
|---|---|---|
| Availability | successful / total x 100 | 99.9% |
| Error Rate | failed / total x 100 | < 0.1% |
| Latency | fast requests / total x 100 | 95% under 200ms |
| Saturation | current utilization % | < 80% CPU |

### Key Calculations

```
Error Budget    = (1 - SLO) x total_requests
Budget Consumed = actual_failures / allowed_failures x 100
Burn Rate       = (% budget consumed) / (elapsed_days / window_days x 100)
```

### Alert Levels

| Burn Rate | Status |
|---|---|
| < 2x | OK |
| >= 2x | Warning |
| >= 4x | Critical |
| Budget > 100% | Breach |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React (JavaScript) |
| Backend | FastAPI (Python) |
| API | REST / JSON |
| Version 1 | Mock API — manual inputs |
| Version 2 | Live Prometheus — automatic |

---

## Project Structure

```
slo-golden-signals/
│
├── backend/                        # Version 1 — Mock API backend
│   ├── slo_main.py                 # All 4 signal endpoints (mock)
│   └── requirements.txt
│
├── frontend-new/                   # Version 1 — React UI (manual inputs)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/sloApi.js
│   │   └── components/
│   └── package.json
│
├── frontend-ui-prometheus/         # Version 2 — React UI (auto Prometheus)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api/sloApi.js
│   │   └── components/
│   └── package.json
│
├── slo_main_prometheus.py          # Version 2 — FastAPI queries Prometheus
├── demo_app.py                     # Generates fake metrics for Prometheus
├── prometheus.yml                  # Prometheus scrape configuration
├── requirements_prometheus.txt     # Python dependencies for Version 2
├── .gitignore
└── README.md
```

---

## Versions

### Version 1 — Mock API (Manual Inputs)

User types metric values manually. FastAPI calculates SLOs and returns results.
Good for learning and understanding SLO math.

### Version 2 — Live Prometheus (Fully Automatic)

FastAPI queries real Prometheus metrics automatically. No manual input needed.
Supports auto-refresh every 30 seconds.

---

## Quick Start — Version 1 (Mock API)

### Prerequisites

- Python 3.10+
- Node.js 18+ from nodejs.org
- Git

### Step 1 — Clone the repo

```bash
git clone https://github.com/Arunkumar-SRE/slo-golden-signals.git
cd slo-golden-signals
```

### Step 2 — Start the backend

```bash
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate

# Mac / Linux
source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn slo_main:app --reload --port 8000
```

Backend runs at http://localhost:8000
Swagger docs at http://localhost:8000/docs

### Step 3 — Start the frontend

```bash
cd frontend-new
npm install
npm start
```

Frontend runs at http://localhost:3000

### Step 4 — Use the dashboard

1. Enter service name, CUJ, and metric values
2. Click CALCULATE ALL SIGNALS
3. View SLI, budget consumed, burn rate, and alert level
4. Click Show Step-by-Step Math for full derivation

---

## Quick Start — Version 2 (Live Prometheus)

### Prerequisites

- Python 3.10+
- Node.js 18+
- Prometheus — download from prometheus.io

### Run Order — Must follow this exact sequence

**Terminal 1 — Start Prometheus**

```bash
cd C:\Prometheus\prometheus-3.10.0.windows-amd64
.\prometheus.exe --config.file=prometheus.yml
```

Verify at http://localhost:9090

**Terminal 2 — Start demo app**

```bash
pip install prometheus-client
python demo_app.py
```

Verify metrics at http://localhost:8001/metrics

**Terminal 3 — Start FastAPI backend**

```bash
pip install -r requirements_prometheus.txt
python -m uvicorn slo_main_prometheus:app --reload --port 8000
```

Verify at http://localhost:8000/docs

**Terminal 4 — Start React frontend**

```bash
cd frontend-ui-prometheus
npm install
npm start
```

Frontend opens at http://localhost:3000

### Verify all components are running

| URL | Expected |
|---|---|
| http://localhost:8001/metrics | Prometheus metrics text |
| http://localhost:9090/targets | Both targets showing UP |
| http://localhost:8000/docs | Swagger UI |
| http://localhost:3000 | SLO Dashboard |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | /api/calculate-all | All 4 signals at once (Version 1) |
| POST | /api/prometheus/calculate-all | All 4 signals from Prometheus (Version 2) |
| POST | /api/availability | Availability signal only |
| POST | /api/error-rate | Error rate signal only |
| POST | /api/latency | Latency signal only |
| POST | /api/saturation | Saturation signal only |
| GET | /api/health | Health check |
| GET | /api/prometheus/status | Prometheus connectivity check |

---

## Roadmap

- Wire production Prometheus from Kubernetes cluster
- Add historical burn rate charts
- Add multi-service support
- Add Slack and PagerDuty alert integrations
- Write custom Kubernetes operator for SLO automation

---

## Author

Arunkumar — SRE / DevOps Engineer

GitHub: https://github.com/Arunkumar-SRE

---

## License

MIT — free to use, modify, and share.
