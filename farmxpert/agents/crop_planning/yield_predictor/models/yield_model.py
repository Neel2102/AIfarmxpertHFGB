import json
import os
from dataclasses import dataclass

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor
 
 
@dataclass
class ModelArtifacts:
    model: CatBoostRegressor
    feature_cols: list[str]
    district_encoding: str
    log_target: bool
    district_freq_map: dict[str, float] | None
 
 
_CACHED: ModelArtifacts | None = None
 
 
def _default_artifacts_dir() -> str:
    env_dir = os.getenv("YIELD_MODEL_ARTIFACTS_DIR")
    if env_dir:
        return env_dir

    base = os.path.dirname(__file__)
    preferred = [
        os.path.join(base, "artifacts"),
        os.path.join(base, "artifacts_raw"),
        os.path.join(base, "artifacts_freq"),
    ]
    for d in preferred:
        if os.path.exists(os.path.join(d, "catboost_yield_model.cbm")) and os.path.exists(
            os.path.join(d, "model_metadata.json")
        ):
            return d

    return os.path.join(base, "artifacts")
 
 
def load_artifacts(artifacts_dir: str | None = None) -> ModelArtifacts:
    global _CACHED
    if _CACHED is not None:
        return _CACHED
 
    artifacts_dir = artifacts_dir or _default_artifacts_dir()
    model_path = os.path.join(artifacts_dir, "catboost_yield_model.cbm")
    meta_path = os.path.join(artifacts_dir, "model_metadata.json")
 
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}. Train the model first (models/train_model.py).")
    if not os.path.exists(meta_path):
        raise FileNotFoundError(f"Metadata file not found: {meta_path}. Train the model first (models/train_model.py).")
 
    with open(meta_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
 
    cfg = meta.get("config", {})
    feature_cols = meta.get("feature_cols")
    if not feature_cols:
        raise ValueError("model_metadata.json missing feature_cols")
 
    model = CatBoostRegressor()
    model.load_model(model_path)
 
    _CACHED = ModelArtifacts(
        model=model,
        feature_cols=list(feature_cols),
        district_encoding=str(cfg.get("district_encoding", "raw")),
        log_target=bool(cfg.get("log_target", False)),
        district_freq_map=meta.get("district_freq_map"),
    )
    return _CACHED
 
 
def _normalize_inputs(payload: dict) -> dict:
    required = ["State_Name", "District_Name", "Crop", "Season", "Crop_Year", "Area"]
    missing = [k for k in required if k not in payload]
    if missing:
        raise ValueError(f"Missing required fields: {missing}")
 
    out: dict = {}
    out["State_Name"] = str(payload.get("State_Name") or "Unknown")
    out["District_Name"] = str(payload.get("District_Name") or "Unknown")
    out["Crop"] = str(payload.get("Crop") or "Unknown")
    out["Season"] = str(payload.get("Season") or "Unknown")
 
    try:
        out["Crop_Year"] = int(payload.get("Crop_Year"))
    except Exception as e:
        raise ValueError("Crop_Year must be an integer") from e
 
    try:
        out["Area"] = float(payload.get("Area"))
    except Exception as e:
        raise ValueError("Area must be a number") from e
 
    if not np.isfinite(out["Area"]) or out["Area"] <= 0:
        raise ValueError("Area must be > 0")
 
    if "Production" in payload:
        raise ValueError("Production must not be provided as an input feature (leakage).")
 
    return out
 
 
def _to_features_df(normalized: dict, artifacts: ModelArtifacts) -> pd.DataFrame:
    row = dict(normalized)
 
    if artifacts.district_encoding == "freq":
        freq_map = artifacts.district_freq_map or {}
        row["District_Freq"] = float(freq_map.get(str(row.get("District_Name")), 0.0))
 
    df = pd.DataFrame([row])
    for c in ["State_Name", "District_Name", "Crop", "Season"]:
        if c in df.columns:
            df[c] = df[c].astype("string").fillna("Unknown")
 
    return df[artifacts.feature_cols]
 
 
def predict_yield(input_data):
    """Predict yield for a single query.

    Accepts:
    - dict with keys: State_Name, District_Name, Crop, Season, Crop_Year, Area
    - or JSON string of that dict
    """
    if isinstance(input_data, str):
        try:
            payload = json.loads(input_data)
        except json.JSONDecodeError as e:
            raise ValueError("String input must be valid JSON") from e
    elif isinstance(input_data, dict):
        payload = input_data
    else:
        raise ValueError("input_data must be a dict or JSON string")

    artifacts = load_artifacts()
    normalized = _normalize_inputs(payload)
    X = _to_features_df(normalized, artifacts)
    pred_fit = float(artifacts.model.predict(X)[0])

    pred = float(np.expm1(pred_fit)) if artifacts.log_target else float(pred_fit)
    if not np.isfinite(pred) or pred < 0:
        pred = max(0.0, float(pred) if np.isfinite(pred) else 0.0)

    return {
        "predicted_yield": pred,
        "yield_unit_note": "Yield is typically tonnes/hectare; for Coconut, dataset production appears to be nuts, so yield may be nuts/hectare.",
        "inputs": normalized,
    }
