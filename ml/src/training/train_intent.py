"""Train intent classifier — 4-class XGBoost (CONV-20).

Usage:
    DATABASE_URL=postgresql://... python -m src.training.train_intent

Classifies user intent: browsing / comparing / deciding / exiting.
Saves the model as intent_v1.pkl in the ml/artifacts/ directory.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np
import shap
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.data.loader import FEATURE_COLS, load_intent_data

ARTIFACTS_DIR = Path(__file__).resolve().parent.parent.parent / "artifacts"

INTENT_CLASSES = ["browsing", "comparing", "deciding", "exiting"]

# Map seed data labels to target classes (includes identity for already-mapped data)
LABEL_MAP = {
    "browsing": "browsing",
    "comparing": "comparing",
    "buying": "deciding",
    "returning": "exiting",
    "deciding": "deciding",
    "exiting": "exiting",
}


def train(database_url: str | None = None) -> dict:
    """Train 4-class intent classifier and save as intent_v1.pkl.

    Returns a dict with metrics (accuracy, confusion_matrix, classification_report).
    """
    db_url = database_url or os.environ.get(
        "DATABASE_URL", "postgresql://localhost:5432/emoratest"
    )

    # 1. Load data
    print("Loading intent data...")
    df = load_intent_data(db_url)

    # Map labels to target classes
    df["intent_label"] = df["intent_label"].map(LABEL_MAP)
    df = df.dropna(subset=["intent_label"])

    print(f"  Loaded {len(df)} samples:")
    for label in INTENT_CLASSES:
        count = (df["intent_label"] == label).sum()
        print(f"    {label}: {count}")

    X = df[FEATURE_COLS].values

    # 2. Encode labels
    le = LabelEncoder()
    le.fit(INTENT_CLASSES)
    y = le.transform(df["intent_label"].values)

    # 3. Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Train XGBoost multi-class
    print("Training XGBoost (multi-class)...")
    model = XGBClassifier(
        n_estimators=200,
        max_depth=5,
        learning_rate=0.05,
        objective="multi:softmax",
        num_class=len(INTENT_CLASSES),
        eval_metric="mlogloss",
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
    y_pred = model.predict(X_test)
    accuracy = float(np.mean(y_pred == y_test))

    cm = confusion_matrix(y_test, y_pred)
    report = classification_report(
        y_test, y_pred, target_names=INTENT_CLASSES
    )

    print("\n== Results ====================================")
    print(f"  Accuracy: {accuracy:.4f}")
    print("\nConfusion Matrix:")
    # Header
    header = "              " + "  ".join(f"{c:>10s}" for c in INTENT_CLASSES)
    print(header)
    for i, row in enumerate(cm):
        row_str = "  ".join(f"{v:>10d}" for v in row)
        print(f"  {INTENT_CLASSES[i]:>12s}  {row_str}")
    print(f"\n{report}")

    # 6. Build SHAP explainer (CONV-23)
    print("Building SHAP TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    shap_sample = explainer.shap_values(X_test[:5])
    print(f"  SHAP values shape: {np.array(shap_sample).shape}")

    # 7. Save model + SHAP explainer + label encoder
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    model_path = ARTIFACTS_DIR / "intent_v1.pkl"
    with open(model_path, "wb") as f:
        pickle.dump(model, f)
    print(f"  Model saved: {model_path}")

    shap_path = ARTIFACTS_DIR / "intent_v1_shap.pkl"
    with open(shap_path, "wb") as f:
        pickle.dump(explainer, f)
    print(f"  SHAP explainer saved: {shap_path}")

    meta_path = ARTIFACTS_DIR / "intent_v1_meta.pkl"
    with open(meta_path, "wb") as f:
        pickle.dump({
            "feature_cols": FEATURE_COLS,
            "label_encoder": le,
            "intent_classes": INTENT_CLASSES,
            "version": "v1",
        }, f)
    print(f"  Metadata saved: {meta_path}")
    print("===============================================")

    return {
        "accuracy": accuracy,
        "confusion_matrix": cm.tolist(),
        "classification_report": report,
        "model_path": str(model_path),
        "shap_path": str(shap_path),
        "best_iteration": model.best_iteration,
    }


if __name__ == "__main__":
    train()
