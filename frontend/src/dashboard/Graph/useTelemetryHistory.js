import { useEffect, useState } from "react"
import { API_BASE_URL } from "../../services/apiBase"

/**
 * Real stored telemetry for the signed-in farmer's device.
 *
 * The soil history charts used to render a hardcoded Mon–Sun series, so the page
 * showed a convincing week of readings for a farm that had never recorded one.
 * This hook returns only measurements the backend actually stored; when there
 * are none it reports `hasData: false` so the chart can say so plainly instead
 * of drawing an invented trend.
 */
export function useTelemetryHistory(hours = 168) {
  const [state, setState] = useState({ loading: true, hasData: false, readings: [], error: null })

  useEffect(() => {
    let cancelled = false

    const load = async () => {
      try {
        const token = localStorage.getItem("access_token")
        const headers = token ? { Authorization: `Bearer ${token}` } : {}
        const res = await fetch(`${API_BASE_URL}/blynk/telemetry/history?hours=${hours}`, { headers })
        if (!res.ok) throw new Error(`History request failed with status ${res.status}`)
        const json = await res.json()
        if (cancelled) return
        // Oldest first, so the chart reads left to right.
        const readings = (json.readings || []).slice().reverse()
        setState({ loading: false, hasData: readings.length > 0, readings, error: null })
      } catch (e) {
        if (cancelled) return
        console.warn("Could not load telemetry history:", e)
        setState({
          loading: false,
          hasData: false,
          readings: [],
          error: "Sensor history is temporarily unavailable.",
        })
      }
    }

    load()
    return () => { cancelled = true }
  }, [hours])

  return state
}

/**
 * Turn stored readings into {time, value} points for one field, using the real
 * recorded_at timestamps. Readings where that sensor reported nothing are left
 * out rather than plotted as 0.
 */
export function toSeries(readings, field) {
  return (readings || [])
    .filter((r) => typeof r[field] === "number" && Number.isFinite(r[field]))
    .map((r) => ({
      time: r.recorded_at
        ? new Date(r.recorded_at).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
        : "",
      value: r[field],
    }))
}

/** Padded min/max for a real series, so the axis fits the actual data. */
export function axisBounds(series, fallbackMin = 0, fallbackMax = 100) {
  if (!series || series.length === 0) return [fallbackMin, fallbackMax]
  const values = series.map((p) => p.value)
  const min = Math.min(...values)
  const max = Math.max(...values)
  if (min === max) return [min - 1, max + 1]
  const pad = (max - min) * 0.1
  return [min - pad, max + pad]
}

/** Shared empty/loading/error panel for the history charts. */
export function HistoryPlaceholder({ loading, error, height = 300 }) {
  const message = loading
    ? "Loading sensor history…"
    : error || "No sensor history recorded yet. Readings appear here once your IoT device reports."
  return (
    <div
      style={{
        height,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        textAlign: "center",
        padding: "0 24px",
        color: "var(--dash-text-muted, #9ca3af)",
        fontSize: "0.86rem",
      }}
    >
      {message}
    </div>
  )
}
