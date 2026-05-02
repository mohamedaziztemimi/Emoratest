import json
import pickle
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    classification_report,
)
from sklearn.model_selection import (
    StratifiedKFold,
    cross_val_score,
    train_test_split,
)
from sklearn.preprocessing import LabelEncoder, StandardScaler

try:
    import xgboost as xgb
    HAS_XGB = True
except ImportError:
    HAS_XGB = False

ARTIFACTS_DIR = Path(__file__).parent.parent.parent / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)

FEATURE_NAMES = [
    'hesitation_score',
    'price_dwell_time_s',
    'rage_click_score',
    'scroll_retreat_count',
    'exit_intent_count',
    'checkout_hesitation_s',
    'velocity_variance',
    'session_duration_s',
]

EMOTIONS = [
    'frustrated', 'confused', 'engaged', 'disengaged'
]

def train():
    print("Generating synthetic training data...")
    import sys
    # Add both ml/src and ml directories to path
    ml_dir = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(ml_dir / "src"))
    sys.path.insert(0, str(ml_dir))
    from data.synthetic_emotions import generate_all

    df = generate_all(n_per_class=1000, seed=42)
    print(f"Total samples: {len(df)}")
    print(df['emotion'].value_counts())

    X = df[FEATURE_NAMES].values
    y = df['emotion'].values

    # Encode labels
    le = LabelEncoder()
    le.fit(EMOTIONS)
    y_encoded = le.transform(y)

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded,
        test_size=0.2,
        random_state=42,
        stratify=y_encoded
    )

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    print("\nTraining XGBoost emotion classifier...")

    if HAS_XGB:
        model = xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            min_child_weight=3,
            gamma=0.1,
            reg_alpha=0.1,
            reg_lambda=1.0,
            objective='multi:softprob',
            num_class=len(EMOTIONS),
            eval_metric='mlogloss',
            random_state=42,
            n_jobs=-1,
        )
        model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=50,
        )
    else:
        print("XGBoost not available, using GradientBoosting")
        from sklearn.ensemble import GradientBoostingClassifier
        model = GradientBoostingClassifier(
            n_estimators=200,
            max_depth=5,
            learning_rate=0.1,
            random_state=42,
        )
        model.fit(X_train_scaled, y_train)

    # Evaluate
    y_pred = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"\n{'='*50}")
    print(f"TEST ACCURACY: {accuracy:.4f} ({accuracy*100:.1f}%)")
    print(f"{'='*50}")
    print("\nPer-class report:")
    print(classification_report(
        y_test, y_pred,
        target_names=le.classes_
    ))

    # Cross-validation
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    cv_scores = cross_val_score(
        model,
        scaler.transform(X),
        le.transform(y),
        cv=cv,
        scoring='accuracy'
    )
    print(f"\nCross-validation: {cv_scores.mean():.4f} (+/- {cv_scores.std()*2:.4f})")

    # Sanity checks
    print("\nSanity checks:")
    test_cases = [
        ("Frustrated user", {
            'hesitation_score': 0.5,
            'price_dwell_time_s': 4,
            'rage_click_score': 0.8,
            'scroll_retreat_count': 2,
            'exit_intent_count': 4,
            'checkout_hesitation_s': 5,
            'velocity_variance': 900,
            'session_duration_s': 35,
        }, 'frustrated'),
        ("Confused user", {
            'hesitation_score': 0.75,
            'price_dwell_time_s': 28,
            'rage_click_score': 0.08,
            'scroll_retreat_count': 7,
            'exit_intent_count': 1,
            'checkout_hesitation_s': 22,
            'velocity_variance': 380,
            'session_duration_s': 130,
        }, 'confused'),
        ("Engaged user", {
            'hesitation_score': 0.06,
            'price_dwell_time_s': 9,
            'rage_click_score': 0.00,
            'scroll_retreat_count': 1,
            'exit_intent_count': 0,
            'checkout_hesitation_s': 2,
            'velocity_variance': 170,
            'session_duration_s': 260,
        }, 'engaged'),
        ("Disengaged user", {
            'hesitation_score': 0.3,
            'price_dwell_time_s': 2,
            'rage_click_score': 0.05,
            'scroll_retreat_count': 1,
            'exit_intent_count': 0,
            'checkout_hesitation_s': 1,
            'velocity_variance': 100,
            'session_duration_s': 5,
        }, 'disengaged'),
    ]

    all_passed = True
    for name, features, expected in test_cases:
        X_test_case = np.array([[
            features[f] for f in FEATURE_NAMES
        ]])
        X_scaled = scaler.transform(X_test_case)
        pred_idx = model.predict(X_scaled)[0]
        pred_emotion = le.inverse_transform([pred_idx])[0]
        proba = model.predict_proba(X_scaled)[0]
        confidence = proba.max()
        status = "[PASS]" if pred_emotion == expected else "[FAIL]"
        if pred_emotion != expected:
            all_passed = False
        print(f"  {status} {name}: predicted={pred_emotion} "
              f"(expected={expected}, confidence={confidence:.2f})")

    if not all_passed:
        print("\n[WARNING] Some sanity checks failed.")
        print("Consider adjusting training data distributions.")
    else:
        print("\n[SUCCESS] All sanity checks passed!")

    # Save artifacts
    print("\nSaving model artifacts...")

    with open(ARTIFACTS_DIR / "emotion_v1.pkl", "wb") as f:
        pickle.dump(model, f)

    with open(ARTIFACTS_DIR / "emotion_v1_scaler.pkl", "wb") as f:
        pickle.dump(scaler, f)

    with open(ARTIFACTS_DIR / "emotion_v1_encoder.pkl", "wb") as f:
        pickle.dump(le, f)

    meta = {
        'version': 'v1',
        'feature_names': FEATURE_NAMES,
        'emotion_labels': EMOTIONS,
        'accuracy': float(accuracy),
        'cv_mean': float(cv_scores.mean()),
        'cv_std': float(cv_scores.std()),
        'n_samples': len(df),
        'n_per_class': 1000,
        'model_type': 'XGBoost' if HAS_XGB else 'GradientBoosting',
    }

    with open(ARTIFACTS_DIR / "emotion_v1_meta.pkl", "wb") as f:
        pickle.dump(meta, f)

    with open(ARTIFACTS_DIR / "emotion_v1_meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    print(f"\n[SUCCESS] Model saved to {ARTIFACTS_DIR}")
    print("   emotion_v1.pkl")
    print("   emotion_v1_scaler.pkl")
    print("   emotion_v1_encoder.pkl")
    print("   emotion_v1_meta.json")

    return accuracy

if __name__ == '__main__':
    accuracy = train()
    if accuracy < 0.70:
        print("\n[WARNING] Accuracy below 70% - review training data")
    elif accuracy < 0.80:
        print("\n[WARNING] Accuracy acceptable but could be improved")
    else:
        print("\n[SUCCESS] Good accuracy - model ready for production")
