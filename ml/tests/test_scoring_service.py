"""Unit tests for the real-time scoring service (CONV-25)."""

from __future__ import annotations

import pickle

import numpy as np
import pytest
import shap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from xgboost import XGBClassifier

from src.data.loader import FEATURE_COLS
from src.scoring.service import ScoringResult, ScoringService

# ---------------------------------------------------------------------------
# Helpers: build a tmp artifacts directory with small trained models
# ---------------------------------------------------------------------------

def _make_data(n=300, rng_seed=42):
    rng = np.random.default_rng(rng_seed)
    X = np.abs(rng.standard_normal((n, len(FEATURE_COLS))))
    y_bin = (X[:, 0] + X[:, 1] > 1.0).astype(int)
    y_multi = np.digitize(X[:, 0], bins=[0.3, 0.7, 1.2]) % 4
    return X, y_bin, y_multi


def _train_and_save(tmp_path):
    X, y_bin, y_multi = _make_data()
    X_tr, X_te, yb_tr, yb_te = train_test_split(X, y_bin, test_size=0.2, random_state=42)
    _, _, ym_tr, ym_te = train_test_split(X, y_multi, test_size=0.2, random_state=42)

    # Predictor (binary)
    pred = XGBClassifier(n_estimators=20, max_depth=3, random_state=42, tree_method="hist")
    pred.fit(X_tr, yb_tr, eval_set=[(X_te, yb_te)], verbose=False)

    # Friction (binary)
    fric = XGBClassifier(n_estimators=20, max_depth=3, random_state=42, tree_method="hist")
    fric.fit(X_tr, yb_tr, eval_set=[(X_te, yb_te)], verbose=False)

    # Intent (multi-class)
    intent = XGBClassifier(
        n_estimators=20, max_depth=3, random_state=42, tree_method="hist",
        objective="multi:softmax", num_class=4,
    )
    intent.fit(X_tr, ym_tr, eval_set=[(X_te, ym_te)], verbose=False)

    le = LabelEncoder()
    intent_classes = ["browsing", "comparing", "deciding", "exiting"]
    le.fit(intent_classes)

    # Save all artifacts
    for name, model in [("predictor_v1", pred), ("intent_v1", intent), ("friction_v1", fric)]:
        with open(tmp_path / f"{name}.pkl", "wb") as f:
            pickle.dump(model, f)
        with open(tmp_path / f"{name}_shap.pkl", "wb") as f:
            pickle.dump(shap.TreeExplainer(model), f)

    # Metadata
    with open(tmp_path / "predictor_v1_meta.pkl", "wb") as f:
        pickle.dump({"feature_cols": list(FEATURE_COLS), "version": "v1"}, f)
    with open(tmp_path / "friction_v1_meta.pkl", "wb") as f:
        pickle.dump({"feature_cols": list(FEATURE_COLS), "version": "v1"}, f)
    with open(tmp_path / "intent_v1_meta.pkl", "wb") as f:
        pickle.dump({
            "feature_cols": list(FEATURE_COLS),
            "label_encoder": le,
            "intent_classes": intent_classes,
            "version": "v1",
        }, f)

    return tmp_path


@pytest.fixture()
def service(tmp_path):
    artifacts = _train_and_save(tmp_path)
    ScoringService.reset_instance()
    return ScoringService(artifacts_dir=artifacts)


@pytest.fixture()
def sample_features():
    return {
        "hesitation_score": 0.4,
        "price_dwell_time_s": 12.0,
        "rage_click_score": 0.1,
        "scroll_retreat_count": 3,
        "exit_intent_count": 1,
        "checkout_hesitation_s": 18.0,
        "velocity_variance": 50000.0,
        "session_duration_s": 200.0,
    }


class TestScoreSession:
    def test_returns_scoring_result(self, service, sample_features):
        result = service.score_session(sample_features)
        assert isinstance(result, ScoringResult)

    def test_session_score_bounded(self, service, sample_features):
        result = service.score_session(sample_features)
        assert 0.0 <= result.session_score <= 1.0

    def test_conversion_prob_bounded(self, service, sample_features):
        result = service.score_session(sample_features)
        assert 0.0 <= result.conversion_prob <= 1.0

    def test_friction_prob_bounded(self, service, sample_features):
        result = service.score_session(sample_features)
        assert 0.0 <= result.friction_prob <= 1.0

    def test_intent_label_valid(self, service, sample_features):
        result = service.score_session(sample_features)
        assert result.intent_label in ("browsing", "comparing", "deciding", "exiting")

    def test_intent_probs_sum_to_one(self, service, sample_features):
        result = service.score_session(sample_features)
        total = sum(result.intent_probs.values())
        assert abs(total - 1.0) < 0.01

    def test_action_is_valid(self, service, sample_features):
        result = service.score_session(sample_features)
        assert result.recommended_action in ("monitor", "nudge", "intervene", "urgent")

    def test_shap_populated_when_explain_true(self, service, sample_features):
        result = service.score_session(sample_features, explain=True)
        assert len(result.top_shap_features) > 0

    def test_shap_empty_when_explain_false(self, service, sample_features):
        result = service.score_session(sample_features, explain=False)
        assert len(result.top_shap_features) == 0

    def test_latency_recorded(self, service, sample_features):
        result = service.score_session(sample_features)
        assert result.latency_ms > 0

    def test_feature_reordering(self, service):
        """Features passed in wrong order should still work."""
        features = {
            "session_duration_s": 200.0,
            "velocity_variance": 50000.0,
            "checkout_hesitation_s": 18.0,
            "exit_intent_count": 1,
            "scroll_retreat_count": 3,
            "rage_click_score": 0.1,
            "price_dwell_time_s": 12.0,
            "hesitation_score": 0.4,
        }
        result = service.score_session(features)
        assert isinstance(result, ScoringResult)


class TestScoreBatch:
    def test_batch_returns_list(self, service, sample_features):
        results = service.score_batch([sample_features, sample_features])
        assert len(results) == 2
        assert all(isinstance(r, ScoringResult) for r in results)

    def test_batch_empty_list(self, service):
        results = service.score_batch([])
        assert results == []


class TestHealthCheck:
    def test_healthy(self, service):
        status = service.health_check()
        assert status["status"] == "healthy"
        assert len(status["models_loaded"]) == 3


class TestSingleton:
    def test_get_instance(self, tmp_path):
        artifacts = _train_and_save(tmp_path)
        ScoringService.reset_instance()
        s1 = ScoringService.get_instance(artifacts_dir=artifacts)
        s2 = ScoringService.get_instance()
        assert s1 is s2
        ScoringService.reset_instance()
