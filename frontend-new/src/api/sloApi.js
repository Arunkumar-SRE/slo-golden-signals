// ============================================================
// sloApi.js — All FastAPI calls live here
//
// WHY a separate file?
//   If the backend URL changes, you change it in ONE place.
//   Components never directly call fetch() — they call these functions.
// ============================================================

const BASE_URL = "http://localhost:8000"

// ── The ONE function React calls ──
// Sends all inputs → gets all 4 signals back in one response
export async function calculateAllSignals(inputs) {
  const response = await fetch(`${BASE_URL}/api/calculate-all`, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(inputs),
  })

  if (!response.ok) {
    // If backend returns an error, throw it so React can catch it
    const err = await response.json()
    throw new Error(err.detail || `HTTP error ${response.status}`)
  }

  return response.json()   // returns the full JSON result
}

// ── Health check — is backend running? ──
export async function checkHealth() {
  const response = await fetch(`${BASE_URL}/api/health`)
  return response.ok
}
