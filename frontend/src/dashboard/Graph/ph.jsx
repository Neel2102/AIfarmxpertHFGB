import SVGChart from "./SVG-graph"
import { useTelemetryHistory, toSeries, axisBounds, HistoryPlaceholder } from "./useTelemetryHistory"

export default function PhSVGChart({ width = 600, height = 300 }) {
  const { loading, hasData, readings, error } = useTelemetryHistory()
  const data = toSeries(readings, "soil_ph")

  if (loading || !hasData || data.length === 0) {
    return <HistoryPlaceholder loading={loading} error={error} height={height} />
  }

  const [yAxisMin, yAxisMax] = axisBounds(data, 0, 14)
  return (
    <SVGChart
      data={data}
      lineColor="#8b5cf6"
      label="Soil pH"
      tooltipLabel="pH"
      tooltipValueColor="#a78bfa"
      yAxisMin={yAxisMin}
      yAxisMax={yAxisMax}
      width={width}
      height={height}
    />
  )
}
