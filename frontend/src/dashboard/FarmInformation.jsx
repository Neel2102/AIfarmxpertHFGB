import { useState, useEffect, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { motion } from "framer-motion"
import { Droplets, ThermometerSun, FlaskRoundIcon as Flask, Info, RefreshCw, Calendar, Sprout, AlertTriangle, Cpu } from "lucide-react"
import MoistureSVGChart from "./Graph/moisture"
import TemperatureSVGChart from "./Graph/tempature"
import PhSVGChart from "./Graph/ph"
import AllSVGChart from "./Graph/all"
import SoilGauge from "./Graph/soil-gauge"
import "../styles/Dashboard/FarmInfoDashboard/farminformation.css"

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api'

const initialSoilData = {
  moisture: null,
  temperature: null,
  ph: null,
  nitrogen: null,
  phosphorus: null,
  potassium: null,
  lastUpdated: null,
  iot: {
    status: "loading",
    error: null,
    source: null,
  },
}

// Responsive chart container component
function ResponsiveChartContainer({ selectedChart }) {
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })
  const containerRef = useRef(null)

  useEffect(() => {
    function updateSize() {
      if (containerRef.current) {
        const width = containerRef.current.clientWidth
        const height = 300
        setDimensions({ width, height })
      }
    }
    updateSize()
    window.addEventListener("resize", updateSize)
    return () => window.removeEventListener("resize", updateSize)
  }, [])

  return (
    <div ref={containerRef} className="responsive-chart-container" style={{ height: dimensions.height }}>
      {selectedChart === "moisture" && <MoistureSVGChart width={dimensions.width} height={dimensions.height} />}
      {selectedChart === "temperature" && <TemperatureSVGChart width={dimensions.width} height={dimensions.height} />}
      {selectedChart === "ph" && <PhSVGChart width={dimensions.width} height={dimensions.height} />}
      {selectedChart === "all" && <AllSVGChart width={dimensions.width} height={dimensions.height} />}
    </div>
  )
}

export default function FarmerDashboard() {
  const navigate = useNavigate()
  const [soilData, setSoilData] = useState(initialSoilData)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedChart, setSelectedChart] = useState("moisture")

  const isNum = (v) => typeof v === "number" && Number.isFinite(v)
  const fmt1 = (v) => (isNum(v) ? v.toFixed(1) : "--")

  const fetchLatestSoilData = async () => {
    const token = localStorage.getItem('access_token')
    const headers = token ? { Authorization: `Bearer ${token}` } : {}

    // First try user-specific soil test telemetry
    try {
      const response = await fetch(`${API_BASE_URL}/soil-tests/latest`, { headers })
      if (response.ok) {
        const json = await response.json()
        if (json?.has_data && json?.test) {
          const t = json.test
          const moisture = typeof t.soil_moisture === 'number' ? t.soil_moisture : null
          const temperature = typeof t.soil_temperature === 'number' ? t.soil_temperature : null
          const ph = typeof t.soil_ph === 'number' ? t.soil_ph : null
          
          if (moisture !== null || temperature !== null || ph !== null) {
            return {
              moisture,
              temperature,
              ph,
              nitrogen: typeof t.nitrogen === 'number' ? t.nitrogen : null,
              phosphorus: typeof t.phosphorus === 'number' ? t.phosphorus : null,
              potassium: typeof t.potassium === 'number' ? t.potassium : null,
              fetchedAt: t.test_date || t.created_at || new Date().toISOString(),
              source: t.source || "IoT Sensor",
              hasData: true,
            }
          }
        }
      }
    } catch (err) {
      console.warn("Could not fetch /soil-tests/latest:", err)
    }

    // Try Blynk telemetry if hardware connected
    try {
      const blynkRes = await fetch(`${API_BASE_URL}/blynk/telemetry/live`, { headers })
      if (blynkRes.ok) {
        const blynkJson = await blynkRes.json()
        if (blynkJson?.has_data && blynkJson?.data) {
          const d = blynkJson.data
          return {
            moisture: typeof d.soil_moisture === 'number' ? d.soil_moisture : null,
            temperature: typeof d.soil_temperature === 'number' ? d.soil_temperature : null,
            ph: typeof d.soil_ph === 'number' ? d.soil_ph : null,
            nitrogen: typeof d.nitrogen === 'number' ? d.nitrogen : null,
            phosphorus: typeof d.phosphorus === 'number' ? d.phosphorus : null,
            potassium: typeof d.potassium === 'number' ? d.potassium : null,
            fetchedAt: d.recorded_at || new Date().toISOString(),
            source: "Blynk IoT",
            hasData: true,
          }
        }
      }
    } catch (err) {
      console.warn("Could not fetch /blynk/telemetry/live:", err)
    }

    return {
      moisture: null,
      temperature: null,
      ph: null,
      nitrogen: null,
      phosphorus: null,
      potassium: null,
      fetchedAt: null,
      source: null,
      hasData: false,
    }
  }

  const refreshData = async () => {
    setIsLoading(true)
    try {
      const latest = await fetchLatestSoilData()

      if (!latest.hasData || (latest.moisture === null && latest.temperature === null && latest.ph === null)) {
        setSoilData({
          moisture: null,
          temperature: null,
          ph: null,
          nitrogen: null,
          phosphorus: null,
          potassium: null,
          lastUpdated: null,
          iot: {
            status: "offline",
            error: "No sensor readings detected",
            source: null,
          },
        })
      } else {
        setSoilData({
          moisture: latest.moisture,
          temperature: latest.temperature,
          ph: latest.ph,
          nitrogen: latest.nitrogen,
          phosphorus: latest.phosphorus,
          potassium: latest.potassium,
          lastUpdated: latest.fetchedAt,
          iot: {
            status: "live",
            error: null,
            source: latest.source,
          },
        })
      }
    } catch (e) {
      setSoilData({
        moisture: null,
        temperature: null,
        ph: null,
        nitrogen: null,
        phosphorus: null,
        potassium: null,
        lastUpdated: null,
        iot: {
          status: "offline",
          error: String(e?.message || e),
          source: null,
        },
      })
    }
    setIsLoading(false)
  }

  // Get suggestions based on soil data
  const getSuggestions = () => {
    const suggestions = []

    if (!isNum(soilData.moisture) && !isNum(soilData.temperature) && !isNum(soilData.ph)) {
      suggestions.push({
        type: "info",
        title: "Live Telemetry Waiting",
        description: "Connect an IoT soil sensor to unlock automated watering schedules & condition alerts.",
        icon: Sprout,
      })
      suggestions.push({
        type: "info",
        title: "Scheduled Maintenance",
        description: "Remember to check your irrigation system weekly.",
        icon: Calendar,
      })
      return suggestions
    }

    if (isNum(soilData.moisture) && soilData.moisture < 40) {
      suggestions.push({
        type: "warning",
        title: "Low Soil Moisture",
        description: "Your soil is too dry. Consider watering your crops soon.",
        icon: Droplets,
      })
    } else if (isNum(soilData.moisture) && soilData.moisture > 80) {
      suggestions.push({
        type: "warning",
        title: "High Soil Moisture",
        description: "Your soil is too wet. Avoid watering until moisture levels decrease.",
        icon: Droplets,
      })
    }

    if (isNum(soilData.temperature) && soilData.temperature < 18) {
      suggestions.push({
        type: "warning",
        title: "Low Soil Temperature",
        description: "Soil temperature is low. Consider using mulch to increase soil temperature.",
        icon: ThermometerSun,
      })
    } else if (isNum(soilData.temperature) && soilData.temperature > 28) {
      suggestions.push({
        type: "warning",
        title: "High Soil Temperature",
        description: "Soil temperature is high. Consider providing shade or irrigation.",
        icon: ThermometerSun,
      })
    }

    if (isNum(soilData.ph) && soilData.ph < 5.5) {
      suggestions.push({
        type: "warning",
        title: "Low Soil pH",
        description: "Your soil is too acidic. Consider adding lime to raise pH.",
        icon: Flask,
      })
    } else if (isNum(soilData.ph) && soilData.ph > 7.5) {
      suggestions.push({
        type: "warning",
        title: "High Soil pH",
        description: "Your soil is too alkaline. Consider adding sulfur to lower pH.",
        icon: Flask,
      })
    }

    if (suggestions.length === 0) {
      suggestions.push({
        type: "info",
        title: "Optimal Soil Conditions",
        description: "Your soil conditions are currently optimal for most crops.",
        icon: Info,
      })
    }

    suggestions.push({
      type: "info",
      title: "Scheduled Maintenance",
      description: "Remember to check your irrigation system weekly.",
      icon: Calendar,
    })

    suggestions.push({
      type: "info",
      title: "Crop Rotation",
      description: "Consider rotating crops next season to maintain soil health.",
      icon: Sprout,
    })

    return suggestions
  }

  const formatDate = (dateString) => {
    if (!dateString) return "No sensor data"
    const date = new Date(dateString)
    return date.toLocaleString()
  }

  const [clientLastUpdated, setClientLastUpdated] = useState("")

  useEffect(() => {
    setClientLastUpdated(formatDate(soilData.lastUpdated))
  }, [soilData.lastUpdated])

  const getStatusColor = (value, type) => {
    if (type === "moisture") {
      if (value < 40 || value > 80) return "status-warning-farminformation"
      return "status-optimal-farminformation"
    } else if (type === "temperature") {
      if (value < 18 || value > 28) return "status-warning-farminformation"
      return "status-optimal-farminformation"
    } else if (type === "ph") {
      if (value < 5.5 || value > 7.5) return "status-warning-farminformation"
      return "status-optimal-farminformation"
    }
    return "status-optimal-farminformation"
  }

  useEffect(() => {
    refreshData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  const suggestions = getSuggestions()

  return (
    <div className="dashboard-container-farminformation">
      <div className="container-farminformation">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="flex-col-gap-2rem"
        >
          <div className="flex-col-gap-1rem">
            <div className="dashboard-header-farminformation">
              <h1 className="dashboard-title-farminformation">Farmer Dashboard</h1>
              <p className="dashboard-subtitle-farminformation">Monitor your soil conditions and get personalized recommendations.</p>
            </div>
            <div className="flex-row-justify-end">
              <button onClick={refreshData} disabled={isLoading} className="btn-farminformation btn-primary-farminformation">
                <RefreshCw
                  className={isLoading ? "animate-rotate-farminformation" : ""}
                />
                {isLoading ? "Refreshing..." : "Refresh Data"}
              </button>
            </div>
          </div>

          {(!isNum(soilData.moisture) || soilData.iot?.status === "offline") && (
            <div className="sensor-unavailable-banner" style={{
              background: 'rgba(245, 158, 11, 0.08)',
              border: '1px solid rgba(245, 158, 11, 0.25)',
              borderRadius: '16px',
              padding: '16px 20px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '16px',
              flexWrap: 'wrap'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <AlertTriangle size={24} style={{ color: '#fbbf24', flexShrink: 0 }} />
                <div>
                  <div style={{ fontWeight: 700, color: 'var(--dash-text-heading)', fontSize: '0.94rem', fontFamily: 'Orbitron, monospace' }}>
                    Sensor Data Unavailable
                  </div>
                  <div style={{ fontSize: '0.82rem', color: 'var(--dash-text-muted)', marginTop: '2px' }}>
                    No active IoT telemetry detected from your farm sensors. Connect hardware in IoT settings or stream readings to view live moisture and nutrient levels.
                  </div>
                </div>
              </div>
              <button
                onClick={() => navigate('/dashboard/hardware-iot')}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '8px',
                  padding: '8px 16px',
                  borderRadius: '10px',
                  border: '1px solid var(--dash-emerald)',
                  background: 'rgba(16, 185, 129, 0.15)',
                  color: 'var(--dash-emerald)',
                  fontFamily: 'Orbitron, monospace',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <Cpu size={15} /> Configure Hardware IoT
              </button>
            </div>
          )}

          <div className="stats-grid-farminformation">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 }}
            >
              <div className="stat-card-farminformation">
                <div className="stat-header-farminformation">
                  <div className="stat-title-farminformation">Soil Moisture</div>
                  <Droplets className="stat-icon-farminformation" />
                </div>
                <div className="flex-row-space-between">
                  <div>
                    <div className="stat-value-farminformation">
                      {isNum(soilData.moisture) ? `${fmt1(soilData.moisture)}%` : "--"}
                    </div>
                    <div
                      className={`stat-status-farminformation ${isNum(soilData.moisture)
                        ? getStatusColor(soilData.moisture, "moisture")
                        : "status-warning-farminformation"
                        }`}
                    >
                      {isNum(soilData.moisture)
                        ? soilData.moisture < 40
                          ? "Low"
                          : soilData.moisture > 80
                            ? "High"
                            : "Optimal"
                        : "Unavailable"}
                    </div>
                  </div>
                  <SoilGauge value={isNum(soilData.moisture) ? soilData.moisture : 0} type="moisture" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.2 }}
            >
              <div className="stat-card-farminformation">
                <div className="stat-header-farminformation">
                  <div className="stat-title-farminformation">Soil Temperature</div>
                  <ThermometerSun className="stat-icon-farminformation" />
                </div>
                <div className="flex-row-space-between">
                  <div>
                    <div className="stat-value-farminformation">
                      {isNum(soilData.temperature) ? `${fmt1(soilData.temperature)}°C` : "--"}
                    </div>
                    <div
                      className={`stat-status-farminformation ${isNum(soilData.temperature)
                        ? getStatusColor(soilData.temperature, "temperature")
                        : "status-warning-farminformation"
                        }`}
                    >
                      {isNum(soilData.temperature)
                        ? soilData.temperature < 18
                          ? "Low"
                          : soilData.temperature > 28
                            ? "High"
                            : "Optimal"
                        : "Unavailable"}
                    </div>
                  </div>
                  <SoilGauge value={isNum(soilData.temperature) ? soilData.temperature : 0} type="temperature" />
                </div>
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.3 }}
            >
              <div className="stat-card-farminformation">
                <div className="stat-header-farminformation">
                  <div className="stat-title-farminformation">Soil pH</div>
                  <Flask className="stat-icon-farminformation" />
                </div>
                <div className="flex-row-space-between">
                  <div>
                    <div className="stat-value-farminformation">
                      {isNum(soilData.ph) ? `${fmt1(soilData.ph)} pH` : "--"}
                    </div>
                    <div
                      className={`stat-status-farminformation ${isNum(soilData.ph) ? getStatusColor(soilData.ph, "ph") : "status-warning-farminformation"
                        }`}
                    >
                      {isNum(soilData.ph)
                        ? soilData.ph < 5.5
                          ? "Acidic"
                          : soilData.ph > 7.5
                            ? "Alkaline"
                            : "Optimal"
                        : "Unavailable"}
                    </div>
                  </div>
                  <SoilGauge value={isNum(soilData.ph) ? soilData.ph : 0} type="ph" />
                </div>
              </div>
            </motion.div>
          </div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <div className="chart-container-farminformation">
              <div className="chart-header-farminformation">
                <div className="chart-title-farminformation">Soil Data History</div>
                <div className="chart-description-farminformation">Last updated: {clientLastUpdated}</div>
              </div>
              <div className="chart-buttons-farminformation">
                <button
                  className={`chart-button-farminformation ${selectedChart === "moisture" ? "active-farminformation" : ""}`}
                  onClick={() => setSelectedChart("moisture")}
                >
                  Moisture Graph
                </button>
                <button
                  className={`chart-button-farminformation ${selectedChart === "temperature" ? "active-farminformation" : ""}`}
                  onClick={() => setSelectedChart("temperature")}
                >
                  Temperature Graph
                </button>
                <button
                  className={`chart-button-farminformation ${selectedChart === "ph" ? "active-farminformation" : ""}`}
                  onClick={() => setSelectedChart("ph")}
                >
                  pH Graph
                </button>
                <button
                  className={`chart-button-farminformation ${selectedChart === "all" ? "active-farminformation" : ""}`}
                  onClick={() => setSelectedChart("all")}
                >
                  All
                </button>
              </div>
              <ResponsiveChartContainer selectedChart={selectedChart} />
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.5 }}
          >
            <div className="chart-container-farminformation">
              <div className="chart-header-farminformation">
                <div className="chart-title-farminformation">Recommendations & Alerts</div>
                <div className="chart-description-farminformation">Based on your current soil conditions</div>
              </div>
              <div className="suggestions-list-farminformation">
                {suggestions.map((suggestion, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.1 * index }}
                  >
                    <div className={`alert-farminformation alert-${suggestion.type}-farminformation`}>
                      <suggestion.icon className="alert-icon-farminformation" />
                      <div>
                        <div className="alert-title-farminformation">{suggestion.title}</div>
                        <div>{suggestion.description}</div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          </motion.div>
        </motion.div>
      </div>
    </div>
  )
}