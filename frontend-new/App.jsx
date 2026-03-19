// ============================================================
// App.jsx — Main component. Wires everything together.
//
// This file does 4 things:
//   1. Holds all input state (useState)
//   2. Calls FastAPI when button clicked (calculateAllSignals)
//   3. Holds the results state
//   4. Renders InputPanel (left) + ResultsPanel (right)
// ============================================================

import { useState, useEffect } from "react"
import { calculateAllSignals, checkHealth } from "./api/sloApi"
import InputPanel   from "./components/InputPanel"
import ResultsPanel from "./components/ResultsPanel"

// ── Default input values (your blueprint numbers) ──
const DEFAULT_INPUTS = {
  service_name:             "E-Commerce Checkout",
  cuj:                      "User Checkout Flow",
  window_days:              30,
  elapsed_days:             10,

  // Availability
  total_requests:           1000000,
  successful_requests:      998500,
  availability_slo:         99.9,

  // Error Rate
  failed_requests:          1500,
  error_rate_slo:           0.1,

  // Latency
  requests_under_threshold: 950000,
  threshold_ms:             200,
  latency_slo:              95.0,

  // Saturation
  current_utilization:      72.0,
  saturation_slo:           80.0,
  resource_type:            "CPU",
}

export default function App() {

  // ── State: inputs, results, loading, error, backend status ──
  const [inputs,    setInputs]    = useState(DEFAULT_INPUTS)
  const [results,   setResults]   = useState(null)
  const [loading,   setLoading]   = useState(false)
  const [error,     setError]     = useState(null)
  const [backendOk, setBackendOk] = useState(null)

  // ── Check backend health when page loads ──
  useEffect(() => {
    checkHealth()
      .then(ok  => setBackendOk(ok))
      .catch(()  => setBackendOk(false))
  }, [])

  // ── Update a single input field ──
  // Called by InputPanel whenever user types something
  function handleChange(name, value) {
    setInputs(prev => ({
      ...prev,          // keep all existing values
      [name]: value     // update only the changed field
    }))
  }

  // ── Call FastAPI and get results ──
  async function handleCalculate() {
    setLoading(true)
    setError(null)

    try {
      // Convert all string values to numbers before sending
      const payload = {
        ...inputs,
        window_days:              +inputs.window_days,
        elapsed_days:             +inputs.elapsed_days,
        total_requests:           +inputs.total_requests,
        successful_requests:      +inputs.successful_requests,
        availability_slo:         +inputs.availability_slo,
        failed_requests:          +inputs.failed_requests,
        error_rate_slo:           +inputs.error_rate_slo,
        requests_under_threshold: +inputs.requests_under_threshold,
        threshold_ms:             +inputs.threshold_ms,
        latency_slo:              +inputs.latency_slo,
        current_utilization:      +inputs.current_utilization,
        saturation_slo:           +inputs.saturation_slo,
      }

      const data = await calculateAllSignals(payload)
      setResults(data)

    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  // ── Render ──
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
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{
            display:      "inline-block",
            background:   "rgba(99,102,241,0.1)",
            border:       "1px solid rgba(99,102,241,0.3)",
            borderRadius: 99,
            padding:      "4px 16px",
            fontSize:     11,
            color:        "#818cf8",
            letterSpacing:"0.1em",
            marginBottom: 14,
          }}>
            SRE TOOLKIT · 4 GOLDEN SIGNALS · MOCK API
          </div>
          <h1 style={{
            fontSize:      32,
            fontWeight:    800,
            margin:        0,
            letterSpacing: "-0.02em",
          }}>
            SLO <span style={{ color: "#818cf8" }}>Dashboard</span>
          </h1>
          <p style={{ color: "#475569", marginTop: 8, fontSize: 13 }}>
            Availability · Error Rate · Latency · Saturation
          </p>
        </div>

        {/* ── Two Column Layout: Left = Inputs, Right = Results ── */}
        <div style={{
          display:             "grid",
          gridTemplateColumns: "380px 1fr",   // fixed left, flexible right
          gap:                 24,
          alignItems:          "start",        // top-align both panels
        }}>

          {/* LEFT — Inputs */}
          <InputPanel
            inputs={inputs}
            onChange={handleChange}
            onCalculate={handleCalculate}
            loading={loading}
            backendOk={backendOk}
          />

          {/* RIGHT — Results */}
          <ResultsPanel
            results={results}
            error={error}
          />

        </div>

      </div>
    </div>
  )
}
