import SVGChart from "./SVG-graph"
import { useTelemetryHistory, toSeries, axisBounds, HistoryPlaceholder } from "./useTelemetryHistory"

export default function AllSVGChart({ width = 600, height = 300 }) {
  const { loading, hasData, readings, error } = useTelemetryHistory()

  const moisture = toSeries(readings, "soil_moisture")
  const temperature = toSeries(readings, "soil_temperature")
  const ph = toSeries(readings, "soil_ph")

  const datasets = []
  if (moisture.length) {
    const [min, max] = axisBounds(moisture, 0, 100)
    datasets.push({ data: moisture, lineColor: "#22c55e", tooltipLabel: "Moisture", yAxisMin: min, yAxisMax: max })
  }
  if (temperature.length) {
    const [min, max] = axisBounds(temperature, 0, 50)
    datasets.push({
      data: temperature, lineColor: "#f59e0b", tooltipLabel: "Temperature",
      yAxisMin: min, yAxisMax: max, fillOpacityTop: 0.35, fillOpacityBottom: 0.08,
    })
  }
  if (ph.length) {
    const [min, max] = axisBounds(ph, 0, 14)
    datasets.push({
      data: ph, lineColor: "#8b5cf6", tooltipLabel: "pH",
      yAxisMin: min, yAxisMax: max, fillOpacityTop: 0.35, fillOpacityBottom: 0.08,
    })
  }

  // Only series with real stored readings are plotted; a sensor that has never
  // reported is simply absent rather than drawn as a flat line at zero.
  if (loading || !hasData || datasets.length === 0) {
    return <HistoryPlaceholder loading={loading} error={error} height={height} />
  }

  const [yAxisMin, yAxisMax] = axisBounds(moisture.length ? moisture : datasets[0].data, 0, 100)
  return (
    <SVGChart
      useIndependentYAxis={true}
      showPoints={false}
      hoverRadius={25}
      yAxisMin={yAxisMin}
      yAxisMax={yAxisMax}
      datasets={datasets}
      label="All"
      width={width}
      height={height}
    />
  )
}
