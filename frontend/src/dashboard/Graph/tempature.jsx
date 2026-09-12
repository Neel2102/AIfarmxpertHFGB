import SVGChart from "./SVG-graph"
import { useTelemetryHistory, toSeries, axisBounds, HistoryPlaceholder } from "./useTelemetryHistory"

export default function TemperatureSVGChart({ width = 600, height = 300 }) {
  const { loading, hasData, readings, error } = useTelemetryHistory()
  const data = toSeries(readings, "soil_temperature")

  if (loading || !hasData || data.length === 0) {
    return <HistoryPlaceholder loading={loading} error={error} height={height} />
  }

  const [yAxisMin, yAxisMax] = axisBounds(data, 0, 50)
  return (
    <SVGChart
      data={data}
      lineColor="#f59e0b"
      label="Soil Temperature"
      tooltipLabel="Temperature"
      tooltipValueColor="#fbbf24"
      yAxisMin={yAxisMin}
      yAxisMax={yAxisMax}
      width={width}
      height={height}
    />
  )
}
