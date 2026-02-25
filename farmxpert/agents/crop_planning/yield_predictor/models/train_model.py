import argparse
import json
import os
from dataclasses import asdict, dataclass

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from sklearn.metrics import mean_absolute_error, mean_squared_error
 
 
@dataclass
class TrainingConfig:
     data_path: str
     artifacts_dir: str
     district_encoding: str
     log_target: bool
     test_years: int
     random_seed: int
     iterations: int
     depth: int
     learning_rate: float
     l2_leaf_reg: float
 
 
def _smape(y_true: np.ndarray, y_pred: np.ndarray, eps: float = 1e-9) -> float:
     denom = (np.abs(y_true) + np.abs(y_pred) + eps)
     return float(np.mean(2.0 * np.abs(y_pred - y_true) / denom) * 100.0)
 
 
def _ensure_str(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
     out = df.copy()
     for c in cols:
         out[c] = out[c].astype("string").fillna("Unknown")
     return out
 
 
def _compute_yield(df: pd.DataFrame) -> pd.DataFrame:
     out = df.copy()
     out["Yield"] = out["Production"] / out["Area"]
     return out
 
 
def _basic_clean(df: pd.DataFrame) -> pd.DataFrame:
     out = df.copy()
 
     out = out[(out["Area"].notna()) & (out["Area"] > 0)]
     out = out[(out["Production"].notna()) & (out["Production"] > 0)]
     out = _compute_yield(out)
     out = out.replace([np.inf, -np.inf], np.nan)
     out = out[out["Yield"].notna()]
     return out
 
 
def _clip_outliers_per_crop(
     df: pd.DataFrame,
     lower_q: float = 0.005,
     upper_q: float = 0.995,
 ) -> pd.DataFrame:
     out = df.copy()
 
     def _clip(g: pd.DataFrame) -> pd.DataFrame:
         lo = float(g["Yield"].quantile(lower_q))
         hi = float(g["Yield"].quantile(upper_q))
         g = g.copy()
         g["Yield"] = g["Yield"].clip(lower=lo, upper=hi)
         return g
 
     return out.groupby("Crop", group_keys=False).apply(_clip)
 
 
def _district_frequency_encoding(train_df: pd.DataFrame, df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, float]]:
     freqs = train_df["District_Name"].value_counts(normalize=True, dropna=False).to_dict()
 
     out = df.copy()
     out["District_Freq"] = out["District_Name"].map(freqs).fillna(0.0).astype(float)
     return out, {str(k): float(v) for k, v in freqs.items()}
 
 
def _time_split(df: pd.DataFrame, test_years: int) -> tuple[pd.DataFrame, pd.DataFrame, int]:
     years = sorted(df["Crop_Year"].dropna().unique().tolist())
     if len(years) < (test_years + 2):
         raise ValueError(f"Not enough unique years to split: years={len(years)}, test_years={test_years}")
 
     cutoff_year = int(years[-(test_years + 1)])
     train_df = df[df["Crop_Year"] <= cutoff_year].copy()
     test_df = df[df["Crop_Year"] > cutoff_year].copy()
     return train_df, test_df, cutoff_year
 
 
def train_and_evaluate(cfg: TrainingConfig) -> dict:
     raw = pd.read_csv(cfg.data_path)
 
     expected = {"State_Name", "District_Name", "Crop_Year", "Season", "Crop", "Area", "Production"}
     missing = expected.difference(set(raw.columns))
     if missing:
         raise ValueError(f"Dataset missing columns: {sorted(missing)}")
 
     df = raw.copy()
     df["Crop_Year"] = pd.to_numeric(df["Crop_Year"], errors="coerce")
     df["Area"] = pd.to_numeric(df["Area"], errors="coerce")
     df["Production"] = pd.to_numeric(df["Production"], errors="coerce")
 
     cat_cols = ["State_Name", "District_Name", "Crop", "Season"]
     df = _ensure_str(df, cat_cols)
     df = _basic_clean(df)
     df = _clip_outliers_per_crop(df)
 
     train_df, test_df, cutoff_year = _time_split(df, test_years=cfg.test_years)
 
     feature_cols = ["State_Name", "District_Name", "Crop", "Season", "Crop_Year", "Area"]
     cat_features = [0, 1, 2, 3]
 
     district_freq_map: dict[str, float] | None = None
     if cfg.district_encoding == "freq":
         train_df, district_freq_map = _district_frequency_encoding(train_df, train_df)
         test_df, _ = _district_frequency_encoding(train_df, test_df)
         feature_cols = ["State_Name", "Crop", "Season", "Crop_Year", "Area", "District_Freq"]
         cat_features = [0, 1, 2]
 
     y_train = train_df["Yield"].astype(float).to_numpy()
     y_test = test_df["Yield"].astype(float).to_numpy()
 
     if cfg.log_target:
         y_train_fit = np.log1p(y_train)
         y_test_fit = np.log1p(y_test)
     else:
         y_train_fit = y_train
         y_test_fit = y_test
 
     X_train = train_df[feature_cols]
     X_test = test_df[feature_cols]
 
     train_pool = Pool(X_train, y_train_fit, cat_features=cat_features)
     test_pool = Pool(X_test, y_test_fit, cat_features=cat_features)
 
     model = CatBoostRegressor(
         loss_function="RMSE",
         random_seed=cfg.random_seed,
         iterations=cfg.iterations,
         depth=cfg.depth,
         learning_rate=cfg.learning_rate,
         l2_leaf_reg=cfg.l2_leaf_reg,
         allow_writing_files=False,
     )
 
     model.fit(
         train_pool,
         eval_set=test_pool,
         verbose=200,
         use_best_model=True,
         early_stopping_rounds=200,
     )
 
     pred_test_fit = model.predict(X_test)
     pred_train_fit = model.predict(X_train)
 
     if cfg.log_target:
         pred_test = np.expm1(pred_test_fit)
         pred_train = np.expm1(pred_train_fit)
     else:
         pred_test = pred_test_fit
         pred_train = pred_train_fit
 
     metrics = {
         "cutoff_year": int(cutoff_year),
         "n_train": int(len(train_df)),
         "n_test": int(len(test_df)),
         "rmse_test": float(np.sqrt(mean_squared_error(y_test, pred_test))),
         "mae_test": float(mean_absolute_error(y_test, pred_test)),
         "smape_test": _smape(y_test, pred_test),
         "rmse_train": float(np.sqrt(mean_squared_error(y_train, pred_train))),
         "mae_train": float(mean_absolute_error(y_train, pred_train)),
         "smape_train": _smape(y_train, pred_train),
     }
 
     os.makedirs(cfg.artifacts_dir, exist_ok=True)
     model_path = os.path.join(cfg.artifacts_dir, "catboost_yield_model.cbm")
     meta_path = os.path.join(cfg.artifacts_dir, "model_metadata.json")
     fi_png_path = os.path.join(cfg.artifacts_dir, "feature_importance.png")
     fi_csv_path = os.path.join(cfg.artifacts_dir, "feature_importance.csv")
     metrics_path = os.path.join(cfg.artifacts_dir, "metrics.json")
 
     model.save_model(model_path)
 
     fi = model.get_feature_importance(prettified=True)
     fi.to_csv(fi_csv_path, index=False)
 
     top = fi.sort_values("Importances", ascending=False).head(20)
     plt.figure(figsize=(10, 7))
     plt.barh(list(reversed(top["Feature Id"].tolist())), list(reversed(top["Importances"].tolist())))
     plt.title("Top Feature Importances")
     plt.tight_layout()
     plt.savefig(fi_png_path, dpi=200)
     plt.close()
 
     metadata = {
         "config": asdict(cfg),
         "feature_cols": feature_cols,
         "cat_features": cat_features,
         "district_freq_map": district_freq_map,
     }
 
     with open(meta_path, "w", encoding="utf-8") as f:
         json.dump(metadata, f, indent=2)
     with open(metrics_path, "w", encoding="utf-8") as f:
         json.dump(metrics, f, indent=2)
 
     return {"metrics": metrics, "artifacts_dir": cfg.artifacts_dir}
 
 
def _parse_args() -> argparse.Namespace:
     p = argparse.ArgumentParser()
     p.add_argument("--data", dest="data_path", default=os.path.join("data", "crop_production.csv"))
     p.add_argument("--artifacts", dest="artifacts_dir", default=os.path.join("models", "artifacts"))
     p.add_argument("--district-encoding", choices=["raw", "freq"], default="raw")
     p.add_argument("--log-target", action="store_true")
     p.add_argument("--test-years", type=int, default=3)
     p.add_argument("--seed", type=int, default=42)
     p.add_argument("--iterations", type=int, default=5000)
     p.add_argument("--depth", type=int, default=8)
     p.add_argument("--learning-rate", type=float, default=0.05)
     p.add_argument("--l2-leaf-reg", type=float, default=5.0)
     return p.parse_args()
 
 
if __name__ == "__main__":
     args = _parse_args()
     cfg = TrainingConfig(
         data_path=args.data_path,
         artifacts_dir=args.artifacts_dir,
         district_encoding=args.district_encoding,
         log_target=bool(args.log_target),
         test_years=int(args.test_years),
         random_seed=int(args.seed),
         iterations=int(args.iterations),
         depth=int(args.depth),
         learning_rate=float(args.learning_rate),
         l2_leaf_reg=float(args.l2_leaf_reg),
     )
     result = train_and_evaluate(cfg)
     print(json.dumps(result["metrics"], indent=2))
