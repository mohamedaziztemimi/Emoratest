"""Train XGBoost conversion predictor (CONV-18).

Usage:
    DATABASE_URL=postgresql://... python -m src.training.train_xgboost

Trains a binary classifier (purchase vs abandon) with SMOTE oversampling.
Saves the model as predictor_v1.pkl in the ml/artifacts/ directory.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np
from imblearn.over_sampling import SMOTE
from sklearn.metrics import classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from src.data.loader import load_training_data

FEATURE_COLS = [
    "hesitation_score",
    "price_dwell_time_s",
    "rage_click_score",
    "scroll_retreat_count",
    "exit_intent_count",
    "checkout_hesitation_s",
    "velocity_variance",
    "session_duration_s",
]

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"


def train(database_url: str | None = None) -> dict:
    """Train XGBoost baseline and save as predictor_v1.pkl.

    Returns a dict with metrics (auc, accuracy, classification_report).
    """
    db_url = database_url or os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/conversiono"
    )

    # 1. Load data
    print("Loading training data...")
    df = load_training_data(db_url)
    print(f"  Loaded {len(df)} samples: {df['label'].sum()} purchase, "
          f"{(df['label'] == 0).sum()} abandon")

    X = df[FEATURE_COLS].values
    y = df["label"].values

    # 2. Train/test split (stratified to preserve class ratio)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 3. SMOTE oversampling on training set only
    print("Applying SMOTE...")
    smote = SMOTE(random_state=42)
    X_train_res, y_train_res = smote.fit_resample(X_train, y_train)
    print(f"  After SMOTE: {len(X_train_res)} samples "
          f"({(y_train_res == 1).sum()} purchase, {(y_train_res == 0).sum()} abandon)")

    # 4. Train XGBoost
    print("Training XGBoost...")
    model = XGBClassifier(
        n_estimators=300,
        max_depth=6,
        early_stopping_rounds=20,
        eval_metric="auc",
        random_state=42,
        tree_method="hist",
    )

    model.fit(
        X_train_res, y_train_res,
        eval_set=[(X_test, y_test)],
        verbose=False,
    )

    # 5. Evaluate
    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = model.predict(X_test)

    auc = roc_auc_score(y_test, y_pred_proba)
    accuracy = float(np.mean(y_pred == y_test))
    report = classification_report(y_test, y_pred, target_names=["abandon", "purchase"])

    print("\n== Results ====================================")
    print(f"  AUC:      {auc:.4f} {'PASS' if auc >= 0.70 else 'FAIL (need >= 0.70)'}")
    print(f"  Accuracy: {accuracy:.4f}")
    print(f"\n{report}")

    # 6. Save model
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS_DIR / "predictor_v1.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"  Model saved: {model_path}")

    # Also save feature names for inference
    meta_path = ARTIFACTS_DIR / "predictor_v1_meta.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump({"feature_cols": FEATURE_COLS, "version": "v1"}, f)
    print(f"  Metadata saved: {meta_path}")
    print("===============================================")

    return {
        "auc": auc,
        "accuracy": accuracy,
        "classification_report": report,
        "model_path": str(model_path),
        "best_iteration": model.best_iteration,
    }


if __name__ == "__main__":
    train()
