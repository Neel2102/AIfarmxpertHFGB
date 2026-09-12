import SVGChart from "./SVG-graph"
import { useTelemetryHistory, toSeries, axisBounds, HistoryPlaceholder } from "./useTelemetryHistory"

export default function MoistureSVGChart({ width = 600, height = 300 }) {
  const { loading, hasData, readings, error } = useTelemetryHistory()
  const data = toSeries(readings, "soil_moisture")

  if (loading || !hasData || data.length === 0) {
    return <HistoryPlaceholder loading={loading} error={error} height={height} />
  }

  const [yAxisMin, yAxisMax] = axisBounds(data, 0, 100)
  return (
    <SVGChart
      data={data}
      lineColor="#22c55e"
      label="Moisture Level"
      tooltipLabel="Moisture"
      tooltipValueColor="#32fc83"
      yAxisMin={yAxisMin}
      yAxisMax={yAxisMax}
      width={width}
      height={height}
    />
  )
}
