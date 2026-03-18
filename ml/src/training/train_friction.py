"""Train friction detector with SHAP explainability (CONV-21).

Usage:
    DATABASE_URL=postgresql://... python -m src.training.train_friction

Trains a binary classifier (high friction vs low friction) using
scale_pos_weight for class imbalance. Includes a SHAP TreeExplainer
for per-prediction feature attribution.
Saves as friction_v1.pkl + friction_v1_shap.pkl.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np
import shap
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.data.loader import FEATURE_COLS, load_friction_data

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"


def train(database_url: str | None = None) -> dict:
    """Train friction detector and save with SHAP explainer.

    Returns a dict with metrics and file paths.
    """
    db_url = database_url or os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/conversiono"
    )

    # 1. Load data
    print("Loading friction data...")
    df = load_friction_data(db_url)
    n_high = df["label"].sum()
    n_low = len(df) - n_high
    print(f"  Loaded {len(df)} samples: {n_high} high friction, {n_low} low friction")

    X = df[FEATURE_COLS].values
    y = df["label"].values

    # 2. Compute scale_pos_weight (auto)
    spw = n_low / max(n_high, 1)
    print(f"  scale_pos_weight: {spw:.2f}")

    # 3. Train/test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Train XGBoost
    print("Training XGBoost (friction detector)...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=6,
        scale_pos_weight=spw,
        eval_metric="auc",
        early_stopping_rounds=20,
        random_state=42,
        tree_method="hist",
    )

    model.fit(
        X_train, y_train,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 5. Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    auc = roc_auc_score(y_test, y_pred_proba)
    accuracy = float(np.mean(y_pred == y_test))
    report = classification_report(
        y_test, y_pred, target_names=["low_friction", "high_friction"]
    )

    print("\n== Results ====================================")
    print(f"  AUC:      {auc:.4f}")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"\n{report}")

    # 6. Init SHAP explainer
    print("Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)

    # Compute SHAP values on test set as a sanity check
    shap_values = explainer.shap_values(X_test[:5])
    print(f"  SHAP values shape: {np.array(shap_values).shape}")
    print("  Top feature importances (mean |SHAP| on test sample):")
    mean_abs = np.abs(explainer.shap_values(X_test[:100])).mean(axis=0)
    for feat, val in sorted(
        zip(FEATURE_COLS, mean_abs, strict=True), key=lambda x: -x[1]
    ):
        print(f"    {feat:30s} {val:.4f}")

    # 7. Save model
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    model_path = ARTIFACTS_DIR / "friction_v1.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"\n  Model saved: {model_path}")

    # Save explainer separately (can be large)
    shap_path = ARTIFACTS_DIR / "friction_v1_shap.pkl"
    with open(shap_path, "wb") as f:
        pickle.dump(explainer, f)
    print(f"  SHAP explainer saved: {shap_path}")

    meta_path = ARTIFACTS_DIR / "friction_v1_meta.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump({"feature_cols": FEATURE_COLS, "version": "v1"}, f)
    print(f"  Metadata saved: {meta_path}")
    print("===============================================")

    return {
        "auc": auc,
        "accuracy": accuracy,
        "classification_report": report,
        "model_path": str(model_path),
        "shap_path": str(shap_path),
        "best_iteration": model.best_iteration,
    }


if __name__ == "__main__":
    train()
