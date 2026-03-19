// ============================================================
// App.jsx — Prometheus Edition
// Fully automatic — fetches from Prometheus, no manual inputs
// ============================================================

import { useState, useEffect, useCallback } from "react"
import ResultsPanel from "./components/ResultsPanel"
import SignalCard   from "./components/SignalCard"

const BASE_URL = "http://localhost:8000"

// ── Default config — user can override in the UI ──
const DEFAULT_CONFIG = {
  prometheus_url:       "http://localhost:9090",
  job:                  "ecommerce-checkout",
  window_days:          30,
  elapsed_days:         1,
  availability_slo:     99.9,
  error_rate_slo:       0.1,
  latency_slo:          95.0,
  saturation_slo:       80.0,
  latency_threshold_ms: 200,
}

// ── Status indicator ──
function StatusDot({ ok, label }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 6, fontSize: 12, fontFamily: "monospace" }}>
      <div style={{
        width: 8, height: 8, borderRadius: "50%",
        background: ok === true ? "#22c55e" : ok === false ? "#ef4444" : "#64748b",
        boxShadow: ok === true ? "0 0 6px #22c55e" : "none",
      }} />
      <span style={{ color: ok === true ? "#22c55e" : ok === false ? "#ef4444" : "#64748b" }}>
        {label}
      </span>
    </div>
  )
}

// ── Config input field ──
function ConfigField({ label, name, value, onChange, type = "text" }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <label style={{ color: "#64748b", fontSize: 10, textTransform: "uppercase", letterSpacing: "0.06em" }}>
        {label}
      </label>
      <input
        type={type}
        value={value}
        onChange={(e) => onChange(name, e.target.value)}
        style={{
          background: "rgba(255,255,255,0.05)",
          border: "1px solid rgba(255,255,255,0.1)",
          borderRadius: 6,
          padding: "7px 10px",
          color: "#f1f5f9",
          fontSize: 12,
          fontFamily: "monospace",
          outline: "none",
          width: "100%",
        }}
        onFocus={(e) => e.target.style.borderColor = "rgba(99,102,241,0.6)"}
        onBlur={(e)  => e.target.style.borderColor = "rgba(255,255,255,0.1)"}
      />
    </div>
  )
}

export default function App() {
  const [config,      setConfig]      = useState(DEFAULT_CONFIG)
  const [results,     setResults]     = useState(null)
  const [loading,     setLoading]     = useState(false)
  const [error,       setError]       = useState(null)
  const [backendOk,   setBackendOk]   = useState(null)
  const [promOk,      setPromOk]      = useState(null)
  const [lastFetched, setLastFetched] = useState(null)
  const [autoRefresh, setAutoRefresh] = useState(false)

  // ── Update a single config field ──
  function handleConfigChange(name, value) {
    setConfig(prev => ({ ...prev, [name]: value }))
  }

  // ── Fetch from Prometheus ──
  const fetchFromPrometheus = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const payload = {
        ...config,
        window_days:          +config.window_days,
        elapsed_days:         +config.elapsed_days,
        availability_slo:     +config.availability_slo,
        error_rate_slo:       +config.error_rate_slo,
        latency_slo:          +config.latency_slo,
        saturation_slo:       +config.saturation_slo,
        latency_threshold_ms: +config.latency_threshold_ms,
      }

      const response = await fetch(`${BASE_URL}/api/prometheus/calculate-all`, {
        method:  "POST",
        headers: { "Content-Type": "application/json" },
        body:    JSON.stringify(payload),
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || `HTTP error ${response.status}`)
      }

      const data = await response.json()
      setResults(data)
      setLastFetched(new Date().toLocaleTimeString())

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }, [config])

  // ── Check backend + Prometheus on load ──
  useEffect(() => {
    // Check backend
    fetch(`${BASE_URL}/api/health`)
      .then(r => setBackendOk(r.ok))
      .catch(() => setBackendOk(false))

    // Check Prometheus
    fetch(`${BASE_URL}/api/prometheus/status`)
      .then(r => r.json())
      .then(d => setPromOk(d.connected))
      .catch(() => setPromOk(false))
  }, [])

  // ── Auto refresh every 30 seconds ──
  useEffect(() => {
    if (!autoRefresh) return
    const interval = setInterval(fetchFromPrometheus, 30000)
    return () => clearInterval(interval)
  }, [autoRefresh, fetchFromPrometheus])

  const ALERT_COLORS = {
    OK:       "#22c55e",
    WARNING:  "#f59e0b",
    CRITICAL: "#ef4444",
    BREACH:   "#a855f7",
  }

  return (
    <div style={{
      minHeight:       "100vh",
      background:      "#080c14",
      backgroundImage: "radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.12), transparent)",
      fontFamily:      "'IBM Plex Mono', monospace",
      color:           "#f1f5f9",
      padding:         "28px 20px",
    }}>
      <div style={{ maxWidth: 1200, margin: "0 auto" }}>

        {/* ── Header ── */}
        <div style={{ textAlign: "center", marginBottom: 28 }}>
          <div style={{
            display: "inline-block",
            background: "rgba(99,102,241,0.1)",
            border: "1px solid rgba(99,102,241,0.3)",
            borderRadius: 99,
            padding: "4px 16px",
            fontSize: 11,
            color: "#818cf8",
            letterSpacing: "0.1em",
            marginBottom: 14,
          }}>
            SRE TOOLKIT · 4 GOLDEN SIGNALS · PROMETHEUS
          </div>
          <h1 style={{ fontSize: 32, fontWeight: 800, margin: 0, letterSpacing: "-0.02em" }}>
            SLO <span style={{ color: "#818cf8" }}>Dashboard</span>
          </h1>
          <p style={{ color: "#475569", marginTop: 8, fontSize: 13 }}>
            Live metrics from Prometheus · Auto calculated
          </p>

          {/* Status dots */}
          <div style={{ display: "flex", gap: 20, justifyContent: "center", marginTop: 12 }}>
            <StatusDot ok={backendOk} label={backendOk ? "FastAPI connected" : "FastAPI offline"} />
            <StatusDot ok={promOk}    label={promOk    ? "Prometheus connected" : "Prometheus offline"} />
            {lastFetched && (
              <span style={{ color: "#475569", fontSize: 11, fontFamily: "monospace" }}>
                Last fetched: {lastFetched}
              </span>
            )}
          </div>
        </div>

        {/* ── Config + Fetch bar ── */}
        <div style={{
          background:   "rgba(255,255,255,0.02)",
          border:       "1px solid rgba(255,255,255,0.07)",
          borderRadius: 12,
          padding:      "16px 20px",
          marginBottom: 20,
        }}>
          <div style={{ color: "#64748b", fontSize: 11, textTransform: "uppercase", letterSpacing: ".1em", marginBottom: 14 }}>
            ⚙️ Configuration
          </div>

          {/* Config grid */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(5, 1fr)", gap: 12, marginBottom: 16 }}>
            <ConfigField label="Prometheus URL"    name="prometheus_url"       value={config.prometheus_url}       onChange={handleConfigChange} />
            <ConfigField label="Job / Service"     name="job"                  value={config.job}                  onChange={handleConfigChange} />
            <ConfigField label="Availability SLO %" name="availability_slo"   value={config.availability_slo}     onChange={handleConfigChange} type="number" />
            <ConfigField label="Error Rate SLO %"  name="error_rate_slo"       value={config.error_rate_slo}       onChange={handleConfigChange} type="number" />
            <ConfigField label="Latency SLO %"     name="latency_slo"          value={config.latency_slo}          onChange={handleConfigChange} type="number" />
            <ConfigField label="Saturation SLO %"  name="saturation_slo"       value={config.saturation_slo}       onChange={handleConfigChange} type="number" />
            <ConfigField label="Latency Threshold (ms)" name="latency_threshold_ms" value={config.latency_threshold_ms} onChange={handleConfigChange} type="number" />
            <ConfigField label="Window (days)"     name="window_days"          value={config.window_days}          onChange={handleConfigChange} type="number" />
            <ConfigField label="Elapsed (days)"    name="elapsed_days"         value={config.elapsed_days}         onChange={handleConfigChange} type="number" />
          </div>

          {/* Action buttons */}
          <div style={{ display: "flex", gap: 12, alignItems: "center" }}>

            {/* Fetch button */}
            <button
              onClick={fetchFromPrometheus}
              disabled={loading}
              style={{
                background:    loading ? "rgba(99,102,241,0.3)" : "linear-gradient(135deg, #6366f1, #818cf8)",
                border:        "none",
                borderRadius:  8,
                padding:       "10px 24px",
                color:         "#fff",
                fontSize:      13,
                fontWeight:    700,
                cursor:        loading ? "wait" : "pointer",
                fontFamily:    "monospace",
                letterSpacing: "0.05em",
                boxShadow:     loading ? "none" : "0 4px 20px rgba(99,102,241,0.3)",
              }}
            >
              {loading ? "⏳ Fetching from Prometheus..." : "▶ FETCH & CALCULATE"}
            </button>

            {/* Auto refresh toggle */}
            <button
              onClick={() => setAutoRefresh(p => !p)}
              style={{
                background:   autoRefresh ? "rgba(34,197,94,0.15)" : "rgba(255,255,255,0.05)",
                border:       `1px solid ${autoRefresh ? "rgba(34,197,94,0.4)" : "rgba(255,255,255,0.1)"}`,
                borderRadius: 8,
                padding:      "10px 18px",
                color:        autoRefresh ? "#22c55e" : "#64748b",
                fontSize:     12,
                cursor:       "pointer",
                fontFamily:   "monospace",
              }}
            >
              {autoRefresh ? "⏹ Stop Auto Refresh" : "🔄 Auto Refresh (30s)"}
            </button>

          </div>
        </div>

        {/* ── Error state ── */}
        {error && (
          <div style={{
            background:   "rgba(239,68,68,0.08)",
            border:       "1px solid rgba(239,68,68,0.3)",
            borderRadius: 12,
            padding:      "16px 20px",
            marginBottom: 20,
            color:        "#fca5a5",
            fontFamily:   "monospace",
            fontSize:     13,
          }}>
            <div style={{ fontWeight: 700, marginBottom: 6 }}>❌ Error fetching from Prometheus</div>
            <div>{error}</div>
            <div style={{ color: "#64748b", marginTop: 10, fontSize: 11, lineHeight: 1.8 }}>
              Make sure:<br/>
              1. Demo app is running: python demo_app.py<br/>
              2. Prometheus is running: .\prometheus.exe --config.file=prometheus.yml<br/>
              3. FastAPI is running: python -m uvicorn slo_main_prometheus:app --reload --port 8000
            </div>
          </div>
        )}

        {/* ── Empty state ── */}
        {!results && !error && !loading && (
          <div style={{
            background:    "rgba(255,255,255,0.02)",
            border:        "1px solid rgba(255,255,255,0.06)",
            borderRadius:  16,
            padding:       60,
            textAlign:     "center",
            color:         "#1e293b",
            fontSize:      14,
            fontFamily:    "monospace",
          }}>
            <div style={{ fontSize: 32, marginBottom: 12 }}>📡</div>
            <div>Hit FETCH & CALCULATE to pull live metrics from Prometheus</div>
          </div>
        )}

        {/* ── Results ── */}
        {results && (
          <>
            {/* Overall health banner */}
            <div style={{
              background:    `rgba(${results.overall_health === "OK" ? "5,46,22" : results.overall_health === "WARNING" ? "45,26,0" : results.overall_health === "CRITICAL" ? "45,0,0" : "26,0,48"},0.9)`,
              border:        `1px solid ${ALERT_COLORS[results.overall_health]}44`,
              borderRadius:  12,
              padding:       "14px 20px",
              marginBottom:  20,
              display:       "flex",
              justifyContent:"space-between",
              alignItems:    "center",
            }}>
              <div>
                <div style={{ color: ALERT_COLORS[results.overall_health], fontWeight: 700, fontSize: 15 }}>
                  {results.overall_health === "OK" ? "✅" : results.overall_health === "WARNING" ? "⚠️" : results.overall_health === "CRITICAL" ? "🔴" : "💀"} Overall Health: {results.overall_health}
                </div>
                <div style={{ color: "#64748b", fontSize: 11, marginTop: 3 }}>
                  {results.job} · Source: {results.source} · {results.prometheus_url}
                </div>
              </div>
              <div style={{ color: "#475569", fontSize: 11, textAlign: "right" }}>
                Data window: last 5 minutes
              </div>
            </div>

            {/* 4 signal cards */}
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
              <SignalCard data={results.availability} icon="📡" />
              <SignalCard data={results.error_rate}   icon="❌" />
              <SignalCard data={results.latency}      icon="⚡" />
              <SignalCard data={results.saturation}   icon="🔥" />
            </div>

            {/* Formula reference */}
            <div style={{
              marginTop:    20,
              background:   "rgba(255,255,255,0.02)",
              border:       "1px solid rgba(255,255,255,0.06)",
              borderRadius: 12,
              padding:      "14px 20px",
              fontSize:     11,
              color:        "#475569",
              fontFamily:   "monospace",
              lineHeight:   2,
            }}>
              <div style={{ color: "#64748b", marginBottom: 6, fontWeight: 700 }}>📐 KEY FORMULAS</div>
              <div><span style={{ color: "#6366f1" }}>Availability  </span> = successful ÷ total × 100</div>
              <div><span style={{ color: "#6366f1" }}>Error Budget  </span> = (1 − SLO) × total_requests</div>
              <div><span style={{ color: "#6366f1" }}>Consumed      </span> = actual_failures ÷ allowed_failures × 100</div>
              <div><span style={{ color: "#6366f1" }}>Burn Rate     </span> = consumed% ÷ (elapsed ÷ window × 100)</div>
            </div>
          </>
        )}

      </div>
    </div>
  )
}
