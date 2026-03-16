// ============================================================
// SignalCard.jsx — Displays results for ONE signal
//
// Props:
//   data   → the signal result object from FastAPI
//            e.g. result.availability
//   icon   → emoji for the signal
// ============================================================

import { useState } from "react"
import GaugeBar from "./GaugeBar"
import Derivation from "./Derivation"

// Alert level → colors and labels
const ALERT_CONFIG = {
  OK:       { color: "#22c55e", bg: "rgba(5,46,22,0.8)",   border: "rgba(34,197,94,0.2)",   label: "✅ Passing"      },
  WARNING:  { color: "#f59e0b", bg: "rgba(45,26,0,0.8)",   border: "rgba(245,158,11,0.2)",  label: "⚠️ Warning"      },
  CRITICAL: { color: "#ef4444", bg: "rgba(45,0,0,0.8)",    border: "rgba(239,68,68,0.2)",   label: "🔴 Critical"     },
  BREACH:   { color: "#a855f7", bg: "rgba(26,0,48,0.8)",   border: "rgba(168,85,247,0.2)",  label: "💀 Breached"     },
}

// Gauge color based on how much budget is consumed
function gaugeColor(consumedPct) {
  if (consumedPct >= 100) return "#a855f7"
  if (consumedPct >= 90)  return "#ef4444"
  if (consumedPct >= 50)  return "#f59e0b"
  return "#22c55e"
}

export default function SignalCard({ data, icon }) {
  // Controls showing/hiding the derivation section
  const [showSteps, setShowSteps] = useState(false)

  if (!data) return null

  const al = ALERT_CONFIG[data.alert_level]
  const gc = gaugeColor(data.consumed_pct)

  return (
    <div style={{
      background:   "rgba(255,255,255,0.03)",
      border:       `1px solid ${al.border}`,
      borderRadius: 16,
      padding:      20,
      display:      "flex",
      flexDirection:"column",
      gap:          14,
    }}>

      {/* ── Card Header: signal name + alert badge ── */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <span style={{ fontSize: 18 }}>{icon}</span>
          <span style={{ color: "#f1f5f9", fontWeight: 700, fontSize: 14, fontFamily: "monospace" }}>
            {data.signal}
          </span>
        </div>
        <span style={{
          background:   al.bg,
          border:       `1px solid ${al.border}`,
          color:        al.color,
          borderRadius: 99,
          padding:      "3px 10px",
          fontSize:     11,
          fontWeight:   700,
        }}>
          {al.label}
        </span>
      </div>

      {/* ── 3 Metric Pills: SLI / Budget Consumed / Burn Rate ── */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 8 }}>

        {/* SLI */}
        <div style={{
          background:   "rgba(255,255,255,0.04)",
          borderRadius: 10,
          padding:      "10px 12px",
        }}>
          <div style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>SLI</div>
          <div style={{ color: "#f1f5f9", fontSize: 18, fontWeight: 700, fontFamily: "monospace", marginTop: 3 }}>
            {data.sli}%
          </div>
          <div style={{ color: "#475569", fontSize: 10, marginTop: 2 }}>
            target {data.slo_target}%
          </div>
        </div>

        {/* Budget Consumed */}
        <div style={{
          background:   data.consumed_pct > 100 ? "rgba(168,85,247,0.08)" : "rgba(255,255,255,0.04)",
          borderRadius: 10,
          padding:      "10px 12px",
        }}>
          <div style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>Consumed</div>
          <div style={{
            color:      data.consumed_pct > 100 ? "#a855f7" : "#f1f5f9",
            fontSize:   18,
            fontWeight: 700,
            fontFamily: "monospace",
            marginTop:  3,
          }}>
            {data.consumed_pct}%
          </div>
          <div style={{ color: "#475569", fontSize: 10, marginTop: 2 }}>
            {data.remaining_pct}% remaining
          </div>
        </div>

        {/* Burn Rate */}
        <div style={{
          background:   data.burn_rate >= 2 ? "rgba(239,68,68,0.08)" : "rgba(255,255,255,0.04)",
          borderRadius: 10,
          padding:      "10px 12px",
        }}>
          <div style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>Burn Rate</div>
          <div style={{
            color:      data.burn_rate >= 4 ? "#ef4444" : data.burn_rate >= 2 ? "#f59e0b" : "#22c55e",
            fontSize:   18,
            fontWeight: 700,
            fontFamily: "monospace",
            marginTop:  3,
          }}>
            {data.burn_rate}×
          </div>
          <div style={{ color: "#475569", fontSize: 10, marginTop: 2 }}>
            vs expected pace
          </div>
        </div>

      </div>

      {/* ── Gauge Bars ── */}
      <div>
        <GaugeBar
          label="Budget Consumed"
          value={Math.min(data.consumed_pct, 100)}
          color={gc}
        />
        <GaugeBar
          label="SLO Health"
          value={data.remaining_pct}
          color="#6366f1"
        />
      </div>

      {/* ── Toggle Derivation ── */}
      <button
        onClick={() => setShowSteps(!showSteps)}
        style={{
          background:    "rgba(99,102,241,0.08)",
          border:        "1px solid rgba(99,102,241,0.2)",
          borderRadius:  8,
          color:         "#818cf8",
          fontSize:      11,
          fontFamily:    "monospace",
          padding:       "7px 12px",
          cursor:        "pointer",
          textAlign:     "left",
          letterSpacing: "0.04em",
        }}
      >
        {showSteps ? "▲ Hide" : "▼ Show"} Step-by-Step Math
      </button>

      {/* ── Derivation Steps (shown on toggle) ── */}
      {showSteps && <Derivation steps={data.steps} />}

    </div>
  )
}
