"""Unit tests for intent classifier training pipeline (CONV-20)."""

from __future__ import annotations

import pickle
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from src.training.train_intent import FEATURE_COLS, INTENT_CLASSES, train


def _make_synthetic_intent_df(n: int = 800) -> pd.DataFrame:
    """Create synthetic intent data with correlated features per class."""
    rng = np.random.default_rng(42)
    per_class = n // 4

    profiles = {
        "browsing": {
            "hesitation_score": (0.0, 0.2),
            "price_dwell_time_s": (0.0, 3.0),
            "rage_click_score": (0.0, 0.05),
            "scroll_retreat_count": (0, 2),
            "exit_intent_count": (0, 1),
            "checkout_hesitation_s": (0.0, 2.0),
            "velocity_variance": (0, 30000),
            "session_duration_s": (10, 90),
        },
        "comparing": {
            "hesitation_score": (0.1, 0.4),
            "price_dwell_time_s": (5.0, 25.0),
            "rage_click_score": (0.0, 0.1),
            "scroll_retreat_count": (3, 10),
            "exit_intent_count": (0, 2),
            "checkout_hesitation_s": (0.0, 5.0),
            "velocity_variance": (10000, 80000),
            "session_duration_s": (120, 400),
        },
        "deciding": {
            "hesitation_score": (0.3, 0.7),
            "price_dwell_time_s": (3.0, 15.0),
            "rage_click_score": (0.0, 0.1),
            "scroll_retreat_count": (1, 4),
            "exit_intent_count": (0, 1),
            "checkout_hesitation_s": (10.0, 60.0),
            "velocity_variance": (5000, 50000),
            "session_duration_s": (150, 500),
        },
        "exiting": {
            "hesitation_score": (0.5, 1.0),
            "price_dwell_time_s": (0.0, 5.0),
            "rage_click_score": (0.1, 0.8),
            "scroll_retreat_count": (0, 3),
            "exit_intent_count": (3, 8),
            "checkout_hesitation_s": (0.0, 5.0),
            "velocity_variance": (80000, 500000),
            "session_duration_s": (10, 60),
        },
    }

    rows = []
    for intent, ranges in profiles.items():
        for _ in range(per_class):
            row = {"intent_label": intent}
            for feat, (lo, hi) in ranges.items():
                if feat in ("scroll_retreat_count", "exit_intent_count"):
                    row[feat] = int(rng.integers(lo, hi + 1))
                else:
                    row[feat] = round(rng.uniform(lo, hi), 4)
            rows.append(row)

    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_df():
    return _make_synthetic_intent_df()


class TestIntentPipeline:
    def test_trains_and_returns_metrics(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_intent.load_intent_data", return_value=synthetic_df),
            patch("src.training.train_intent.ARTIFACTS_DIR", tmp_path),
        ):
            result = train(database_url="unused://mock")

        assert "accuracy" in result
        assert "confusion_matrix" in result
        assert "classification_report" in result
        assert result["accuracy"] >= 0.60

    def test_confusion_matrix_shape(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_intent.load_intent_data", return_value=synthetic_df),
            patch("src.training.train_intent.ARTIFACTS_DIR", tmp_path),
        ):
            result = train(database_url="unused://mock")

        cm = result["confusion_matrix"]
        assert len(cm) == 4
        assert all(len(row) == 4 for row in cm)

    def test_saves_model_file(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_intent.load_intent_data", return_value=synthetic_df),
            patch("src.training.train_intent.ARTIFACTS_DIR", tmp_path),
        ):
            train(database_url="unused://mock")

        model_path = tmp_path / "intent_v1.pkl"
        assert model_path.exists()

        with open(model_path, "rb") as f:
            model = pickle.load(f)

        sample = np.zeros((1, len(FEATURE_COLS)))
        proba = model.predict_proba(sample)
        assert proba.shape == (1, 4)

    def test_saves_metadata_with_label_encoder(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_intent.load_intent_data", return_value=synthetic_df),
            patch("src.training.train_intent.ARTIFACTS_DIR", tmp_path),
        ):
            train(database_url="unused://mock")

        meta_path = tmp_path / "intent_v1_meta.pkl"
        assert meta_path.exists()

        with open(meta_path, "rb") as f:
            meta = pickle.load(f)

        assert meta["feature_cols"] == FEATURE_COLS
        assert meta["intent_classes"] == INTENT_CLASSES
        assert meta["version"] == "v1"
        # Verify label encoder can decode
        decoded = meta["label_encoder"].inverse_transform([0, 1, 2, 3])
        assert list(decoded) == INTENT_CLASSES

    def test_early_stopping_used(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_intent.load_intent_data", return_value=synthetic_df),
            patch("src.training.train_intent.ARTIFACTS_DIR", tmp_path),
        ):
            result = train(database_url="unused://mock")

        assert result["best_iteration"] < 200
