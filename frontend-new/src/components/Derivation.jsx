// ============================================================
// Derivation.jsx — Shows step-by-step math for each signal
//
// Props:
//   steps  → array of { n, label, formula, result }
//            comes directly from FastAPI response
// ============================================================

export default function Derivation({ steps }) {
  if (!steps || steps.length === 0) return null

  return (
    <div style={{ marginTop: 16 }}>

      {/* Section title */}
      <div style={{
        color:         "#6366f1",
        fontSize:      11,
        fontWeight:    700,
        letterSpacing: "0.08em",
        textTransform: "uppercase",
        marginBottom:  10,
      }}>
        🧮 Step-by-Step Derivation
      </div>

      {/* Steps list */}
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {steps.map((step) => (
          <div key={step.n} style={{
            display:       "grid",
            gridTemplateColumns: "24px 1fr auto",
            alignItems:    "center",
            gap:           10,
            background:    "rgba(255,255,255,0.02)",
            border:        "1px solid rgba(255,255,255,0.05)",
            borderRadius:  8,
            padding:       "8px 12px",
          }}>
            {/* Step number */}
            <span style={{
              color:      "#6366f1",
              fontWeight: 700,
              fontSize:   12,
              fontFamily: "monospace",
            }}>
              {step.n}
            </span>

            {/* Label + formula */}
            <div>
              <div style={{ color: "#64748b", fontSize: 11 }}>{step.label}</div>
              <div style={{ color: "#475569", fontSize: 10, fontFamily: "monospace", marginTop: 2 }}>
                {step.formula}
              </div>
            </div>

            {/* Result */}
            <span style={{
              color:      "#f1f5f9",
              fontWeight: 700,
              fontSize:   12,
              fontFamily: "monospace",
              textAlign:  "right",
            }}>
              {step.result}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
