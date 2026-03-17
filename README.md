SLO Golden Signals Dashboard
A full-stack SRE tool to calculate and visualize SLOs based on Google's 4 Golden Signals.
Define Critical User Journeys (CUJ), set SLO targets, compute error budgets, track consumption and burn rates with alert levels.

📊 Golden Signals & Formulas
Signal	SLI Formula	Example SLO
Availability	successful / total × 100	99.9%
Error Rate	failed / total × 100	< 0.1%
Latency	fast requests / total × 100	95% under 200ms
Saturation	current / capacity × 100	< 80% CPU
Key calculations:

Error Budget = (1 − SLO) × total requests

Budget Consumed = actual failures ÷ allowed failures × 100

Burn Rate = (% budget consumed) ÷ (elapsed days ÷ window days × 100)

Alert levels: Burn Rate < 2 → ✅ OK | ≥ 2 → ⚠️ Warning | ≥ 4 → 🔴 Critical | Budget > 100% → 💀 Breach

🛠 Tech Stack
Layer	Technology
Frontend	React (JavaScript)
Backend	FastAPI (Python)
API	REST / JSON
Data	Mock API (ready for Prometheus)
📁 Project Structure (Key Files)
text
slo-golden-signals/
├── backend/
│   ├── slo_main.py          # All 4 signal endpoints
│   └── requirements.txt
├── frontend-ui/
│   ├── src/
│   │   ├── App.jsx           # Main layout + state
│   │   ├── api/sloApi.js     # API calls to backend
│   │   └── components/       # Reusable UI parts
│   └── package.json
└── README.md

🚀 Quick Start

Prerequisites

Python 3.10+

Node.js 18+ (LTS)

Git

1. Clone
bash
git clone https://github.com/Arunkumar-SRE/slo-golden-signals.git
cd slo-golden-signals
2. Backend (FastAPI)
bash
cd backend
python -m venv .venv
# Activate: .venv\Scripts\activate (Windows) or source .venv/bin/activate (Mac/Linux)
pip install -r requirements.txt
uvicorn slo_main:app --reload --port 8000
Backend at http://localhost:8000 | Swagger docs at /docs

3. Frontend (React)
bash
cd frontend-ui
npm install
npm start
Frontend at http://localhost:3000

4. Use the Dashboard
Enter service name, CUJ, and metrics.

Click CALCULATE ALL SIGNALS.

View SLI, budget consumed, burn rate, and alert level.

Expand Show Step-by-Step Math for derivation.

🔌 API Endpoints
Method	Endpoint	Description
POST	/api/calculate-all	All 4 signals at once
POST	/api/availability	Availability only
POST	/api/error-rate	Error rate only
POST	/api/latency	Latency only
POST	/api/saturation	Saturation only
GET	/api/health	Health check

🔮 Roadmap (Optional)
Real Prometheus metrics

Burn rate charts

Multi-service support

Alert integrations (Slack, PagerDuty)

👤 Author
Arunkumar – SRE / DevOps Engineer
GitHub: @Arunkumar-SRE

📄 License
MIT – free to use, modify, and share.
