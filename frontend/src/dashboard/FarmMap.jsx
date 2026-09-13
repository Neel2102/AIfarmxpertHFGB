import React, { useEffect, useState, useRef, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import toast from "react-hot-toast";
import {
  Wheat,
  ClipboardList,
  Pencil,
  Crosshair,
  Square,
  MapPin,
  Trash2,
  BarChart3,
  Sprout,
  Mountain,
  Droplets,
  Sun,
  Ruler,
  Rocket,
  Save,
  Microscope,
  CheckCircle2,
  Lightbulb,
  Loader2,
  Activity
} from "lucide-react";
import "../styles/Dashboard/FarmMap.css";

const API_BASE_URL = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';
const GOOGLE_MAPS_API_KEY = process.env.REACT_APP_GOOGLE_MAPS_API_KEY;

let googleMapsPromise;
const loadGoogleMaps = () => {
  if (window.google?.maps?.importLibrary) {
    return Promise.all([
      window.google.maps.importLibrary("maps"),
      window.google.maps.importLibrary("geometry")
    ]).then(([mapsLibrary, geometryLibrary]) => ({
      ...mapsLibrary,
      ...geometryLibrary,
      geometry: geometryLibrary
    }));
  }
  if (!GOOGLE_MAPS_API_KEY) return Promise.reject(new Error("REACT_APP_GOOGLE_MAPS_API_KEY is missing"));
  if (googleMapsPromise) return googleMapsPromise;

  googleMapsPromise = new Promise((resolve, reject) => {
    const callbackName = "__farmxpertGoogleMapsReady";
    window[callbackName] = () => {
      if (!window.google?.maps?.importLibrary) {
        reject(new Error("Google Maps loaded without its library loader"));
        return;
      }
      Promise.all([
        window.google.maps.importLibrary("maps"),
        window.google.maps.importLibrary("geometry")
      ]).then(([mapsLibrary, geometryLibrary]) => resolve({
        ...mapsLibrary,
        ...geometryLibrary,
        geometry: geometryLibrary
      })).catch(reject);
    };
    window.gm_authFailure = () => reject(new Error("Google Maps rejected this API key. Enable billing and Maps JavaScript API in Google Cloud."));
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${encodeURIComponent(GOOGLE_MAPS_API_KEY)}&loading=async&callback=${callbackName}&v=weekly`;
    script.async = true;
    script.defer = true;
    script.onerror = () => reject(new Error("Could not load Google Maps. Check the API key and network connection."));
    document.head.appendChild(script);
  });
  return googleMapsPromise;
};

const polygonFeature = coordinates => ({
  type: "Feature",
  properties: {},
  geometry: { type: "Polygon", coordinates: [coordinates] }
});
export default function FarmMap() {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const shapesRef = useRef([]);
  const previewShapeRef = useRef(null);
  const polygonPointsRef = useRef([]);
  const drawingModeRef = useRef(null);
  const finishDrawingRef = useRef(null);
  const [mapReady, setMapReady] = useState(false);
  const navigate = useNavigate();

  const [farmPolygon, setFarmPolygon] = useState(null);
  const [polygonCoordinates, setPolygonCoordinates] = useState([]);
  const [areaSqMeters, setAreaSqMeters] = useState(null);
  const [areaHectares, setAreaHectares] = useState(null);
  const [areaAcres, setAreaAcres] = useState(null);
  const [drawingEnabled, setDrawingEnabled] = useState(false);
  const [drawingMode, setDrawingMode] = useState(null);
  const [polygonPointCount, setPolygonPointCount] = useState(0);
  const [mapError, setMapError] = useState("");
  const [activeStep, setActiveStep] = useState(1);
  const [status, setStatus] = useState({ text: "No area selected", area: "Not calculated", isSuccess: false });
  const [buttonsEnabled, setButtonsEnabled] = useState(false);
  const [saving, setSaving] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);

  // Form state
  const [formData, setFormData] = useState({
    soil_type: "black",
    water_source: "borewell",
    season: "kharif",
    land_area: "5.2",
    crop_preferences: "cotton,soybean"
  });

  const calculateArea = useCallback((coordinates) => {
    if (coordinates.length < 3 || !window.google?.maps?.geometry) return null;
    const squareMeters = window.google.maps.geometry.spherical.computeArea(coordinates);
    return {
      squareMeters,
      hectares: squareMeters / 10000,
      acres: squareMeters / 4046.8564224
    };
  }, []);

  const updatePolygonState = useCallback((coordinates) => {
    if (coordinates.length < 3) return false;
    const area = calculateArea(coordinates);
    if (!area) return false;
    const coordinateValues = coordinates.map(point => ({ lat: point.lat(), lng: point.lng() }));
    setPolygonCoordinates(coordinateValues);
    setAreaSqMeters(area.squareMeters);
    setAreaHectares(area.hectares);
    setAreaAcres(area.acres);
    const geoCoordinates = coordinateValues.map(({ lat, lng }) => [lng, lat]);
    const feature = polygonFeature([...geoCoordinates, geoCoordinates[0]]);
    setFarmPolygon(feature);
    setFormData(prev => ({ ...prev, land_area: area.acres.toFixed(2) }));
    setStatus({ text: "Area selected successfully", area: `${area.acres.toFixed(2)} acres`, isSuccess: true });
    setButtonsEnabled(true);
    setActiveStep(3);
    return true;
  }, [calculateArea]);

  // Pre-fill from onboarding cached data on initial mount
  useEffect(() => {
    const cachedOnboarding = localStorage.getItem('farm_layout_data');
    if (cachedOnboarding) {
      try {
        const parsed = JSON.parse(cachedOnboarding);
        setFormData(prev => ({
          ...prev,
          soil_type: parsed.soil_type || prev.soil_type,
          water_source: parsed.water_source || prev.water_source,
          season: parsed.season || prev.season,
          land_area: parsed.land_area ? String(parsed.land_area) : prev.land_area,
          crop_preferences: parsed.crop_preferences || prev.crop_preferences
        }));
      } catch (err) {
        console.warn('Could not parse farm_layout_data:', err);
      }
    }
  }, []);

  const removePreview = () => {
    if (previewShapeRef.current) {
      previewShapeRef.current.setMap(null);
      previewShapeRef.current = null;
    }
  };

  const updatePolygonFromShape = useCallback((shape) => {
    updatePolygonState(shape.getPath().getArray());
  }, [updatePolygonState]);

  const attachPolygonListeners = useCallback((shape) => {
    const path = shape.getPath();
    ["set_at", "insert_at", "remove_at"].forEach(eventName => {
      path.addListener(eventName, () => updatePolygonFromShape(shape));
    });
    shape.addListener("dragend", () => updatePolygonFromShape(shape));
  }, [updatePolygonFromShape]);

  const finishShape = (shape, feature) => {
    removePreview();
    shapesRef.current.push(shape);
    if (feature.geometry.type === "Polygon") {
      updatePolygonState(shape.getPath().getArray());
      setTimeout(() => document.querySelector(".farm-map-form-section")?.scrollIntoView({ behavior: "smooth" }), 100);
      attachPolygonListeners(shape);
    }
    drawingModeRef.current = null;
    polygonPointsRef.current = [];
    setDrawingMode(null);
    setDrawingEnabled(false);
  };

  // Initialize Google Map and manual drawing interactions.
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return undefined;
    let disposed = false;

    loadGoogleMaps().then(maps => {
      if (disposed || !mapRef.current) return;
      const map = new maps.Map(mapRef.current, { center: { lat: 23.0225, lng: 72.5714 }, zoom: 13, mapTypeId: "hybrid" });
      mapInstanceRef.current = map;
      setMapReady(true);

      // Use the user's location once for the initial viewport; map control remains manual afterward.
      if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          position => {
            if (!disposed) {
              map.setCenter({ lat: position.coords.latitude, lng: position.coords.longitude });
              map.setZoom(15);
            }
          },
          () => {
            // Keep the existing default center when location access is denied or unavailable.
          },
          { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
        );
      }

      map.addListener("click", event => {
        if (drawingModeRef.current !== "polygon") return;
        polygonPointsRef.current.push(event.latLng);
        setPolygonPointCount(polygonPointsRef.current.length);
        const path = polygonPointsRef.current;
        if (previewShapeRef.current) previewShapeRef.current.setPath(path);
        else previewShapeRef.current = new maps.Polygon({
          map,
          paths: path,
          strokeColor: "#10b981",
          strokeWeight: 3,
          fillColor: "#10b981",
          fillOpacity: 0.12
        });
      });
      map.addListener("dblclick", () => {
        if (drawingModeRef.current === "polygon") finishDrawingRef.current?.();
      });

      const token = localStorage.getItem('access_token');
      if (token) {
        fetch(`${API_BASE_URL}/auth/farm-layout`, { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } })
          .then(response => {
            if (response.status === 401) {
              localStorage.removeItem('access_token');
              localStorage.removeItem('refresh_token');
              localStorage.removeItem('session_token');
              navigate('/login', { replace: true });
              return null;
            }
            return response.ok ? response.json() : null;
          })
          .then(data => {
            if (!data?.has_layout || !data.polygon || disposed) return;
            const restoredPolygon = data.polygon.type === 'Feature' ? data.polygon : { type: 'Feature', geometry: data.polygon };
            const path = restoredPolygon.geometry.coordinates[0].map(([lng, lat]) => ({ lat, lng }));
            const polygon = new maps.Polygon({ map, paths: path, editable: true, draggable: true, fillColor: "#10b981", fillOpacity: 0.25, strokeColor: "#10b981", strokeWeight: 2 });
            shapesRef.current.push(polygon);
            attachPolygonListeners(polygon);
            updatePolygonState(polygon.getPath().getArray());
            const savedFormData = data.form_data || {};
            if (Object.keys(savedFormData).length > 0) {
              const otherFormData = { ...savedFormData };
              delete otherFormData.land_area;
              setFormData(prev => ({ ...prev, ...otherFormData }));
            }
            setStatus(prev => ({ ...prev, text: 'Loaded saved farm layout from cloud', isSuccess: true }));
            setActiveStep(3);
            setButtonsEnabled(true);
          })
          .catch(err => console.warn('Could not load saved farm layout:', err));
      }
    }).catch(error => setMapError(error.message));

    return () => {
      disposed = true;
      removePreview();
      shapesRef.current.forEach(shape => shape.setMap(null));
      shapesRef.current = [];
      mapInstanceRef.current = null;
      setMapReady(false);
    };
  }, [attachPolygonListeners, calculateArea, updatePolygonState]);

  // Enable drawing
  const enableDrawing = () => {
    startDrawing("polygon");
  };

  const startDrawing = mode => {
    if (!mapInstanceRef.current) return;
    removePreview();
    shapesRef.current.forEach(shape => shape.setMap(null));
    shapesRef.current = [];
    setPolygonCoordinates([]);
    setAreaSqMeters(null);
    setAreaHectares(null);
    setAreaAcres(null);
    setFarmPolygon(null);
    setFormData(prev => ({ ...prev, land_area: "" }));
    setButtonsEnabled(false);
    polygonPointsRef.current = [];
    setPolygonPointCount(0);
    drawingModeRef.current = "polygon";
    setDrawingMode("polygon");
    setDrawingEnabled(true);
    setActiveStep(2);
    setStatus({ text: "Drawing polygon; double-click to finish", area: "Not calculated", isSuccess: false });
  };

  const finishDrawing = () => {
    const mode = drawingModeRef.current;
    const points = polygonPointsRef.current;
    if (mode !== "polygon" || !mapInstanceRef.current || points.length < 3) {
      setStatus({ text: "Add at least 3 points to complete the polygon", area: "Not calculated", isSuccess: false });
      return;
    }
    const maps = window.google.maps;
    const path = points.map(point => ({ lat: point.lat(), lng: point.lng() }));
    const shape = new maps.Polygon({ map: mapInstanceRef.current, paths: path, editable: true, draggable: true, fillColor: "#10b981", fillOpacity: 0.25, strokeColor: "#10b981", strokeWeight: 2 });
    const coordinates = path.map(point => [point.lng, point.lat]);
    const feature = polygonFeature([...coordinates, coordinates[0]]);
    finishShape(shape, feature);
  };
  finishDrawingRef.current = finishDrawing;

  const stopDrawing = () => {
    removePreview();
    polygonPointsRef.current = [];
    setPolygonPointCount(0);
    drawingModeRef.current = null;
    setDrawingEnabled(false);
    setDrawingMode(null);
    setStatus(prev => prev.isSuccess
      ? prev
      : { text: "Drawing stopped. Select an area to try again.", area: "Not calculated", isSuccess: false });
  };

  // Clear drawing
  const clearDrawing = () => {
    shapesRef.current.forEach(shape => shape.setMap(null));
    shapesRef.current = [];
    removePreview();
    polygonPointsRef.current = [];
    setPolygonPointCount(0);
    drawingModeRef.current = null;
    setFarmPolygon(null);
    setPolygonCoordinates([]);
    setAreaSqMeters(null);
    setAreaHectares(null);
    setAreaAcres(null);
    setFormData(prev => ({ ...prev, land_area: "" }));
    setStatus({ text: "No area selected", area: "Not calculated", isSuccess: false });
    setActiveStep(1);
    setButtonsEnabled(false);

    setDrawingEnabled(false);
    setDrawingMode(null);
  };

  // Handle form changes
  const handleFormChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const getFarmPayload = () => {
    const cropPreferences = formData.crop_preferences
      .split(",")
      .map(crop => crop.trim())
      .filter(Boolean);
    const coordinates = farmPolygon?.geometry?.coordinates?.[0] || [];
    const center = coordinates.length
      ? coordinates.reduce((result, [lng, lat]) => ({ lat: result.lat + lat, lng: result.lng + lng }), { lat: 0, lng: 0 })
      : { lat: 23.0225, lng: 72.5714 };
    if (coordinates.length) {
      center.lat /= coordinates.length;
      center.lng /= coordinates.length;
    }
    return {
      farm_location: { lat: center.lat, lon: center.lng },
      land_area_acres: parseFloat(formData.land_area),
      soil_type: formData.soil_type,
      water_source: formData.water_source,
      season: formData.season,
      crop_preferences: cropPreferences,
      polygon: farmPolygon,
      polygonCoordinates,
      areaSqMeters,
      areaHectares,
      areaAcres,
      form_data: {
        ...formData,
        crop_preferences: cropPreferences.join(","),
        polygonCoordinates,
        areaSqMeters,
        areaHectares,
        areaAcres
      }
    };
  };

  const saveLayoutToBackend = async (payload, token) => {
    const response = await fetch(`${API_BASE_URL}/auth/farm-layout`, {
      method: 'PUT',
      headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
      body: JSON.stringify({
        polygon: payload.polygon,
        polygonCoordinates: payload.polygonCoordinates,
        areaSqMeters: payload.areaSqMeters,
        areaHectares: payload.areaHectares,
        areaAcres: payload.areaAcres,
        center: [payload.farm_location.lat, payload.farm_location.lon],
        area_acres: payload.land_area_acres,
        soil_type: payload.soil_type,
        irrigation_type: payload.water_source,
        form_data: payload.form_data
      })
    });
    const result = await response.json();
    if (response.status === 401) {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('session_token');
      navigate('/login', { replace: true });
      throw new Error('Your session has expired. Please log in again.');
    }
    if (!response.ok || !result.success) throw new Error(result.detail || result.message || 'Save failed');
    return result;
  };

  // Save farm data to backend
  const saveFarmData = async () => {
    if (!farmPolygon || polygonCoordinates.length < 3 || areaSqMeters === null) {
      alert("Please select a farm area first");
      return;
    }

    setSaving(true);
    const payload = getFarmPayload();

    try {
      const token = localStorage.getItem('access_token');
      if (!token) throw new Error('Please log in before saving your farm layout.');
      await saveLayoutToBackend(payload, token);

      setStatus({ text: "Farm layout saved to database!", area: `${parseFloat(formData.land_area).toFixed(2)} acres`, isSuccess: true });
      setActiveStep(4);
      toast.success("Data saved successfully", { duration: 3000 });
      setTimeout(() => {
        setStatus(prev => ({ ...prev, text: "Area selected", isSuccess: true }));
        setSaving(false);
      }, 2500);
    } catch (err) {
      alert(err.message || 'Failed to save farm layout. Please try again.');
      setSaving(false);
    }
  };

  // Send the complete farm payload to the agent, then persist the returned result.
  const analyzeFarm = async () => {
    if (!farmPolygon || polygonCoordinates.length < 3 || areaSqMeters === null) {
      alert("Please select a farm area first");
      return;
    }

    setAnalyzing(true);
    try {
      const token = localStorage.getItem('access_token');
      if (!token) throw new Error('Please log in before analyzing your farm.');
      const farmData = getFarmPayload();
      await saveLayoutToBackend(farmData, token);
      const sessionId = localStorage.getItem('farm_session_id') || crypto.randomUUID();
      localStorage.setItem('farm_session_id', sessionId);
      const response = await fetch(`${API_BASE_URL}/super-agent/query`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: `Analyze this farm layout and recommend crops by plot for ${farmData.land_area_acres} acres.`,
          session_id: sessionId,
          context: { farm_data: farmData }
        })
      });
      const result = await response.json();
      if (!response.ok || !result.success) throw new Error(result.detail || 'Farm analysis failed');
      const farmResult = { ...farmData, analyzed_at: new Date().toISOString(), agent_result: result };
      localStorage.setItem("savedFarmData", JSON.stringify(farmData));
      localStorage.setItem("farmResult", JSON.stringify(farmResult));
      setStatus({ text: "Analysis complete and saved to database.", area: `${farmData.land_area_acres} acres`, isSuccess: true });
      setActiveStep(4);
      navigate('/dashboard/orchestrator');
    } catch (err) {
      setStatus({ text: err.message || "Farm analysis failed", area: `${formData.land_area} acres`, isSuccess: false });
    } finally {
      setAnalyzing(false);
    }
  };

  return (
    <div className="farm-map-container">
      <h2 className="farm-map-header">
        <Wheat className="w-6 h-6 text-emerald-400" />
        Farm Layout Designer
      </h2>

      {/* Info Panel */}
      <div className="farm-map-info-panel">
        <h4 className="farm-map-info-title">
          <ClipboardList className="w-4 h-4 text-emerald-400" />
          Quick Start Guide
        </h4>

        <div className={`farm-map-workflow-step ${activeStep === 1 ? "step-active" : activeStep > 1 ? "step-completed" : "step-inactive"}`}>
          <div className="step-number">1</div>
          <div>Click "Select Area" to enable drawing</div>
        </div>

        <div className={`farm-map-workflow-step ${activeStep === 2 ? "step-active" : activeStep > 2 ? "step-completed" : "step-inactive"}`}>
          <div className="step-number">2</div>
          <div>Click points; double-click to finish the boundary</div>
        </div>

        <div className={`farm-map-workflow-step ${activeStep === 3 ? "step-active" : activeStep > 3 ? "step-completed" : "step-inactive"}`}>
          <div className="step-number">3</div>
          <div>Fill in farm details below</div>
        </div>

        <div className={`farm-map-workflow-step ${activeStep === 4 ? "step-active" : activeStep > 4 ? "step-completed" : "step-inactive"}`}>
          <div className="step-number">4</div>
          <div>Save your work or Analyze directly</div>
        </div>

        <div className={`farm-map-drawing-indicator ${drawingEnabled ? "drawing-active" : "drawing-inactive"}`}>
          {drawingEnabled ? (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Pencil className="w-3.5 h-3.5 text-emerald-400 animate-pulse" />
              Drawing Mode: Active - {drawingMode}
            </span>
          ) : (
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}>
              <Crosshair className="w-3.5 h-3.5 text-slate-400" />
              Drawing Mode: Inactive
            </span>
          )}
        </div>
      </div>

      {/* Map */}
      <div ref={mapRef} className="farm-map-leaflet">
        {mapError && <div className="farm-map-error">{mapError}. Add your key as REACT_APP_GOOGLE_MAPS_API_KEY in .env and rebuild.</div>}
      </div>

      {/* Controls */}
      <div className="farm-map-controls">
        <div className="farm-map-button-group">
          <button
            className={`farm-map-btn ${drawingEnabled ? "btn-warning" : "btn-primary"}`}
            onClick={drawingEnabled ? stopDrawing : enableDrawing}
            disabled={!mapReady}
          >
            {drawingEnabled ? (
              <>
                <Square className="w-4 h-4" /> Stop Drawing
              </>
            ) : (
              <>
                <MapPin className="w-4 h-4" /> Select Area
              </>
            )}
          </button>
          <button
            className="farm-map-btn btn-success"
            onClick={finishDrawing}
            disabled={!drawingEnabled || polygonPointCount < 3}
          >
            <CheckCircle2 className="w-4 h-4" /> Finish Drawing
          </button>
          <button
            className="farm-map-btn btn-danger"
            onClick={clearDrawing}
            disabled={!buttonsEnabled && !drawingEnabled}
          >
            <Trash2 className="w-4 h-4" /> Reset Polygon
          </button>
        </div>

        {/* Status Panel */}
        <div className={`farm-map-status-panel ${status.isSuccess ? "status-success" : ""}`}>
          <h4 className="status-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <BarChart3 className="w-4 h-4 text-emerald-400" /> Current Status
          </h4>
          <div className="status-content">
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              {status.isSuccess ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> : <Activity className="w-4 h-4 text-slate-400" />}
              <strong>Status:</strong> {status.text}
            </div>
            <div><strong>Area:</strong> {status.area}</div>
          </div>
        </div>

        {/* Form Section */}
        <div className="farm-map-form-section">
          <h4 className="form-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sprout className="w-5 h-5 text-emerald-400" /> Farm Details
          </h4>

          <div className="form-grid">
            <div className="form-group">
              <label htmlFor="soil_type" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Mountain className="w-3.5 h-3.5 text-emerald-400" /> Soil Type
              </label>
              <select
                id="soil_type"
                value={formData.soil_type}
                onChange={(e) => handleFormChange("soil_type", e.target.value)}
              >
                <option value="black">Black Soil</option>
                <option value="red">Red Soil</option>
                <option value="alluvial">Alluvial Soil</option>
                <option value="sandy">Sandy Soil</option>
                <option value="clay">Clay Soil</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="water_source" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Droplets className="w-3.5 h-3.5 text-cyan-400" /> Water Source
              </label>
              <select
                id="water_source"
                value={formData.water_source}
                onChange={(e) => handleFormChange("water_source", e.target.value)}
              >
                <option value="borewell">Borewell</option>
                <option value="canal">Canal</option>
                <option value="rain">Rain-fed</option>
                <option value="drip">Drip Irrigation</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="season" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Sun className="w-3.5 h-3.5 text-amber-400" /> Season
              </label>
              <select
                id="season"
                value={formData.season}
                onChange={(e) => handleFormChange("season", e.target.value)}
              >
                <option value="kharif">Kharif (Monsoon)</option>
                <option value="rabi">Rabi (Winter)</option>
                <option value="zaid">Zaid (Summer)</option>
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="land_area" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Ruler className="w-3.5 h-3.5 text-emerald-400" /> Land Area (acres)
              </label>
              <input
                type="number"
                id="land_area"
                value={formData.land_area}
                onChange={(e) => handleFormChange("land_area", e.target.value)}
                step="0.1"
                min="0.1"
                readOnly={areaAcres !== null}
              />
            </div>
          </div>

          <div className="form-group full-width">
            <label htmlFor="crop_preferences" style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Wheat className="w-3.5 h-3.5 text-emerald-400" /> Crop Preferences (comma-separated)
            </label>
            <input
              type="text"
              id="crop_preferences"
              value={formData.crop_preferences}
              onChange={(e) => handleFormChange("crop_preferences", e.target.value)}
              placeholder="e.g., cotton, soybean, wheat"
            />
          </div>
        </div>

        {/* Action Buttons */}
        <div className="farm-map-actions">
          <h4 className="actions-title" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Rocket className="w-5 h-5 text-emerald-400" /> Next Steps
          </h4>
          <div className="farm-map-button-group">
            <button
              className="farm-map-btn btn-success"
              onClick={saveFarmData}
              disabled={!buttonsEnabled || saving}
            >
              {saving ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Saving...
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" /> Save Farm Data
                </>
              )}
            </button>
            <button
              className="farm-map-btn btn-warning"
              onClick={analyzeFarm}
              disabled={!buttonsEnabled || analyzing}
            >
              {analyzing ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Analyzing...
                </>
              ) : (
                <>
                  <Microscope className="w-4 h-4" /> Analyze & Auto-Save
                </>
              )}
            </button>
          </div>
          <p className="actions-tip" style={{ display: 'flex', alignItems: 'flex-start', gap: '6px' }}>
            <Lightbulb className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <span>Complete the boundary, enter farm details, then analyze to save and receive agent recommendations.</span>
          </p>
        </div>
      </div>
    </div>
  );
}
