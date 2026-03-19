// ============================================================
// InputPanel.jsx — All input fields on the LEFT side
// ============================================================

// Reusable single input field
function Field({ label, name, value, onChange, hint, step = 1, type = "number" }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
      <label style={{
        color:         "#94a3b8",
        fontSize:      11,
        textTransform: "uppercase",
        letterSpacing: "0.06em",
        fontFamily:    "monospace",
      }}>
        {label}
      </label>
      <input
        type={type}
        name={name}
        value={value}
        step={step}
        onChange={(e) => onChange(name, e.target.value)}
        style={{
          background:   "rgba(255,255,255,0.05)",
          border:       "1px solid rgba(255,255,255,0.1)",
          borderRadius: 8,
          padding:      "9px 12px",
          color:        "#f1f5f9",
          fontSize:     13,
          fontFamily:   "monospace",
          outline:      "none",
          width:        "100%",
        }}
        onFocus={(e) => e.target.style.borderColor = "rgba(99,102,241,0.6)"}
        onBlur={(e)  => e.target.style.borderColor = "rgba(255,255,255,0.1)"}
      />
      {hint && (
        <span style={{ color: "#475569", fontSize: 10 }}>{hint}</span>
      )}
    </div>
  )
}

// Section divider label
function Section({ title, color = "#6366f1" }) {
  return (
    <div style={{
      color:         color,
      fontSize:      11,
      fontWeight:    700,
      textTransform: "uppercase",
      letterSpacing: "0.1em",
      borderBottom:  `1px solid ${color}33`,
      paddingBottom: 8,
      marginTop:     4,
    }}>
      {title}
    </div>
  )
}

export default function InputPanel({ inputs, onChange, onCalculate, loading, backendOk }) {
  return (
    <div style={{
      background:    "rgba(255,255,255,0.02)",
      border:        "1px solid rgba(255,255,255,0.07)",
      borderRadius:  16,
      padding:       24,
      display:       "flex",
      flexDirection: "column",
      gap:           16,
      height:        "fit-content",
    }}>

      {/* Panel title */}
      <div style={{
        color:         "#64748b",
        fontSize:      11,
        textTransform: "uppercase",
        letterSpacing: ".1em",
        borderBottom:  "1px solid rgba(255,255,255,0.06)",
        paddingBottom: 10
      }}>
        📥 Input Parameters
      </div>

      {/* ── Shared Settings ── */}
      <Section title="⚙️ Service & Window" />
      <Field label="Service Name"   name="service_name"  value={inputs.service_name}  onChange={onChange} hint="e.g. Checkout API"      type="text" />
      <Field label="CUJ"            name="cuj"           value={inputs.cuj}           onChange={onChange} hint="Critical User Journey"   type="text" />
      <Field label="Window (Days)"  name="window_days"   value={inputs.window_days}   onChange={onChange} hint="Rolling SLO window" />
      <Field label="Elapsed (Days)" name="elapsed_days"  value={inputs.elapsed_days}  onChange={onChange} hint="Days passed so far" />

      {/* ── Availability ── */}
      <Section title="📡 Availability" color="#22c55e" />
      <Field label="Total Requests"        name="total_requests"      value={inputs.total_requests}      onChange={onChange} hint="All requests this window" />
      <Field label="Successful Requests"   name="successful_requests" value={inputs.successful_requests} onChange={onChange} hint="Requests that succeeded" />
      <Field label="Availability SLO (%)"  name="availability_slo"    value={inputs.availability_slo}    onChange={onChange} hint="e.g. 99.9" step={0.01} />

      {/* ── Error Rate ── */}
      <Section title="❌ Error Rate" color="#ef4444" />
      <Field label="Failed Requests"     name="failed_requests" value={inputs.failed_requests} onChange={onChange} hint="Requests that failed" />
      <Field label="Error Rate SLO (%)"  name="error_rate_slo"  value={inputs.error_rate_slo}  onChange={onChange} hint="Max allowed error % e.g. 0.1" step={0.01} />

      {/* ── Latency ── */}
      <Section title="⚡ Latency" color="#f59e0b" />
      <Field label="Requests Under Threshold" name="requests_under_threshold" value={inputs.requests_under_threshold} onChange={onChange} hint="Requests faster than threshold" />
      <Field label="Threshold (ms)"           name="threshold_ms"             value={inputs.threshold_ms}             onChange={onChange} hint="e.g. 200ms" />
      <Field label="Latency SLO (%)"          name="latency_slo"              value={inputs.latency_slo}              onChange={onChange} hint="% of requests must be fast" step={0.1} />

      {/* ── Saturation ── */}
      <Section title="🔥 Saturation" color="#a855f7" />
      <Field label="Current Utilization (%)" name="current_utilization" value={inputs.current_utilization} onChange={onChange} hint="Current CPU or memory %" step={0.1} />
      <Field label="Saturation SLO (%)"      name="saturation_slo"      value={inputs.saturation_slo}      onChange={onChange} hint="Max allowed utilization %" step={0.1} />

      {/* ── Calculate Button ── */}
      <button
        onClick={onCalculate}
        disabled={loading}
        style={{
          marginTop:     8,
          background:    loading ? "rgba(99,102,241,0.3)" : "linear-gradient(135deg, #6366f1, #818cf8)",
          border:        "none",
          borderRadius:  10,
          padding:       "13px",
          color:         "#fff",
          fontSize:      13,
          fontWeight:    700,
          cursor:        loading ? "wait" : "pointer",
          fontFamily:    "monospace",
          letterSpacing: "0.05em",
          boxShadow:     loading ? "none" : "0 4px 20px rgba(99,102,241,0.3)",
          transition:    "all 0.2s",
        }}
      >
        {loading ? "⏳ Calculating..." : "▶ CALCULATE ALL SIGNALS"}
      </button>

      {/* ── Backend status indicator ── */}
      <div style={{ fontSize: 11, fontFamily: "monospace" }}>
        {backendOk === true  && <span style={{ color: "#22c55e" }}>● Backend connected</span>}
        {backendOk === false && <span style={{ color: "#ef4444" }}>✗ Backend offline — run: python -m uvicorn slo_main:app --reload --port 8000</span>}
        {backendOk === null  && <span style={{ color: "#64748b" }}>○ Checking backend...</span>}
      </div>

    </div>
  )
}