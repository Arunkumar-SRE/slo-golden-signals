// ============================================================
// ResultsPanel.jsx — All results on the RIGHT side
//
// Props:
//   results  → full response from FastAPI /api/calculate-all
//   error    → error message string if API call failed
// ============================================================

import SignalCard from "./SignalCard"

// Overall health banner at the top
const HEALTH_CONFIG = {
  OK:       { color: "#22c55e", bg: "rgba(5,46,22,0.9)",   label: "✅ All Systems Healthy",     desc: "All signals passing. Budget healthy." },
  WARNING:  { color: "#f59e0b", bg: "rgba(45,26,0,0.9)",   label: "⚠️ Warning",                 desc: "One or more signals burning fast. Investigate." },
  CRITICAL: { color: "#ef4444", bg: "rgba(45,0,0,0.9)",    label: "🔴 Critical",                desc: "Budget burning 4×+. Stop deployments." },
  BREACH:   { color: "#a855f7", bg: "rgba(26,0,48,0.9)",   label: "💀 SLO Breached",            desc: "Budget exhausted. SLO violated. Incident!" },
}

export default function ResultsPanel({ results, error }) {

  // ── Empty state — nothing calculated yet ──
  if (!results && !error) {
    return (
      <div style={{
        background:    "rgba(255,255,255,0.02)",
        border:        "1px solid rgba(255,255,255,0.07)",
        borderRadius:  16,
        padding:       40,
        display:       "flex",
        alignItems:    "center",
        justifyContent:"center",
        minHeight:     400,
        color:         "#1e293b",
        fontSize:      13,
        fontFamily:    "monospace",
        textAlign:     "center",
      }}>
        Fill in the inputs and hit Calculate
      </div>
    )
  }

  // ── Error state ──
  if (error) {
    return (
      <div style={{
        background:   "rgba(239,68,68,0.08)",
        border:       "1px solid rgba(239,68,68,0.3)",
        borderRadius: 16,
        padding:      24,
        color:        "#fca5a5",
        fontFamily:   "monospace",
        fontSize:     13,
      }}>
        <div style={{ fontWeight: 700, marginBottom: 8 }}>❌ Error</div>
        <div>{error}</div>
        <div style={{ color: "#64748b", marginTop: 12, fontSize: 11 }}>
          Make sure FastAPI is running: python -m uvicorn main:app --reload --port 8000
        </div>
      </div>
    )
  }

  // ── Results state ──
  const health = HEALTH_CONFIG[results.overall_health]

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>

      {/* ── Overall Health Banner ── */}
      <div style={{
        background:    health.bg,
        border:        `1px solid ${health.color}44`,
        borderRadius:  12,
        padding:       "14px 18px",
        display:       "flex",
        justifyContent:"space-between",
        alignItems:    "center",
      }}>
        <div>
          <div style={{ color: health.color, fontWeight: 700, fontSize: 15, fontFamily: "monospace" }}>
            {health.label}
          </div>
          <div style={{ color: "#64748b", fontSize: 11, marginTop: 3 }}>
            {results.service} · {results.cuj}
          </div>
        </div>
        <div style={{ color: "#64748b", fontSize: 11, textAlign: "right" }}>
          {health.desc}
        </div>
      </div>

      {/* ── 4 Signal Cards ── */}
      <SignalCard data={results.availability} icon="📡" />
      <SignalCard data={results.error_rate}   icon="❌" />
      <SignalCard data={results.latency}      icon="⚡" />
      <SignalCard data={results.saturation}   icon="🔥" />

      {/* ── Formula Reference Footer ── */}
      <div style={{
        background:   "rgba(255,255,255,0.02)",
        border:       "1px solid rgba(255,255,255,0.06)",
        borderRadius: 12,
        padding:      "14px 18px",
        fontSize:     11,
        color:        "#475569",
        fontFamily:   "monospace",
        lineHeight:   2,
      }}>
        <div style={{ color: "#64748b", marginBottom: 6, fontWeight: 700 }}>📐 KEY FORMULAS</div>
        <div><span style={{ color: "#6366f1" }}>Availability  </span> = successful ÷ total × 100</div>
        <div><span style={{ color: "#6366f1" }}>Error Rate    </span> = failed ÷ total × 100</div>
        <div><span style={{ color: "#6366f1" }}>Error Budget  </span> = (1 − SLO) × total requests</div>
        <div><span style={{ color: "#6366f1" }}>Consumed      </span> = actual failures ÷ allowed failures × 100</div>
        <div><span style={{ color: "#6366f1" }}>Burn Rate     </span> = consumed% ÷ (elapsed ÷ window × 100)</div>
      </div>

    </div>
  )
}
