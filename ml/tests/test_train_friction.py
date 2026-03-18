"""Unit tests for friction detector training pipeline (CONV-21)."""

from __future__ import annotations

import pickle
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest
import shap

from src.training.train_friction import FEATURE_COLS, train


def _make_synthetic_friction_df(n: int = 600) -> pd.DataFrame:
    """Create synthetic friction data with correlated features."""
    rng = np.random.default_rng(42)
    n_high = n // 3  # ~33% high friction
    n_low = n - n_high

    rows = []
    for label, count in [(1, n_high), (0, n_low)]:
        for _ in range(count):
            if label == 1:  # high friction
                rows.append({
                    "hesitation_score": rng.uniform(0.4, 1.0),
                    "price_dwell_time_s": rng.uniform(10.0, 45.0),
                    "rage_click_score": rng.uniform(0.2, 0.9),
                    "scroll_retreat_count": int(rng.integers(3, 12)),
                    "exit_intent_count": int(rng.integers(2, 8)),
                    "checkout_hesitation_s": rng.uniform(15.0, 120.0),
                    "velocity_variance": rng.uniform(80000, 500000),
                    "session_duration_s": rng.uniform(30, 200),
                    "label": 1,
                })
            else:  # low friction
                rows.append({
                    "hesitation_score": rng.uniform(0.0, 0.3),
                    "price_dwell_time_s": rng.uniform(0.5, 10.0),
                    "rage_click_score": rng.uniform(0.0, 0.1),
                    "scroll_retreat_count": int(rng.integers(0, 3)),
                    "exit_intent_count": int(rng.integers(0, 2)),
                    "checkout_hesitation_s": rng.uniform(0.0, 10.0),
                    "velocity_variance": rng.uniform(0, 50000),
                    "session_duration_s": rng.uniform(60, 600),
                    "label": 0,
                })

    return pd.DataFrame(rows)


@pytest.fixture()
def synthetic_df():
    return _make_synthetic_friction_df()


class TestFrictionPipeline:
    def test_trains_and_returns_metrics(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_friction.load_friction_data", return_value=synthetic_df),
            patch("src.training.train_friction.ARTIFACTS_DIR", tmp_path),
        ):
            result = train(database_url="unused://mock")

        assert "auc" in result
        assert "accuracy" in result
        assert "shap_path" in result
        assert result["auc"] >= 0.70

    def test_saves_model_and_shap(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_friction.load_friction_data", return_value=synthetic_df),
            patch("src.training.train_friction.ARTIFACTS_DIR", tmp_path),
        ):
            train(database_url="unused://mock")

        # Model file
        model_path = tmp_path / "friction_v1.pkl"
        assert model_path.exists()
        with open(model_path, "rb") as f:
            model = pickle.load(f)
        sample = np.zeros((1, len(FEATURE_COLS)))
        proba = model.predict_proba(sample)
        assert proba.shape == (1, 2)

        # SHAP explainer file
        shap_path = tmp_path / "friction_v1_shap.pkl"
        assert shap_path.exists()
        with open(shap_path, "rb") as f:
            explainer = pickle.load(f)
        assert isinstance(explainer, shap.TreeExplainer)

    def test_shap_explains_predictions(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_friction.load_friction_data", return_value=synthetic_df),
            patch("src.training.train_friction.ARTIFACTS_DIR", tmp_path),
        ):
            train(database_url="unused://mock")

        with open(tmp_path / "friction_v1_shap.pkl", "rb") as f:
            explainer = pickle.load(f)

        # SHAP values should have one value per feature
        sample = np.zeros((1, len(FEATURE_COLS)))
        shap_values = explainer.shap_values(sample)
        assert np.array(shap_values).shape[-1] == len(FEATURE_COLS)

    def test_saves_metadata(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_friction.load_friction_data", return_value=synthetic_df),
            patch("src.training.train_friction.ARTIFACTS_DIR", tmp_path),
        ):
            train(database_url="unused://mock")

        meta_path = tmp_path / "friction_v1_meta.pkl"
        assert meta_path.exists()
        with open(meta_path, "rb") as f:
            meta = pickle.load(f)
        assert meta["feature_cols"] == FEATURE_COLS
        assert meta["version"] == "v1"

    def test_early_stopping_used(self, synthetic_df, tmp_path):
        with (
            patch("src.training.train_friction.load_friction_data", return_value=synthetic_df),
            patch("src.training.train_friction.ARTIFACTS_DIR", tmp_path),
        ):
            result = train(database_url="unused://mock")

        assert result["best_iteration"] < 200
