"""Verify emotion model works correctly with 4-emotion system."""

import sys
sys.path.insert(0, '/app')

import pickle
import numpy as np
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import json

# Import the bootstrap to generate fresh data
from app.services.emotion_model_bootstrap import generate_synthetic_features, EMOTIONS

ARTIFACTS_DIR = Path("/app/ml_artifacts")

print("=" * 60)
print("EMOTION MODEL VERIFICATION")
print("=" * 60)

# Check if model files exist
print("\n1. Checking model files...")
model_files = {
    "emotion_v1.pkl": ARTIFACTS_DIR / "emotion_v1.pkl",
    "emotion_v1_scaler.pkl": ARTIFACTS_DIR / "emotion_v1_scaler.pkl",
    "emotion_v1_encoder.pkl": ARTIFACTS_DIR / "emotion_v1_encoder.pkl",
}

for name, path in model_files.items():
    if path.exists():
        print(f"   ✓ {name} exists")
    else:
        print(f"   ✗ {name} MISSING - model needs to be trained")
        print("\n   Run: docker-compose exec backend python -c 'from app.services.emotion_model_bootstrap import bootstrap_emotion_model; bootstrap_emotion_model()'")
        sys.exit(1)

# Load the model
print("\n2. Loading model artifacts...")
with open(model_files["emotion_v1.pkl"], 'rb') as f:
    model = pickle.load(f)
with open(model_files["emotion_v1_scaler.pkl"], 'rb') as f:
    scaler = pickle.load(f)
with open(model_files["emotion_v1_encoder.pkl"], 'rb') as f:
    encoder = pickle.load(f)

print(f"   Model type: {type(model).__name__}")
print(f"   Model classes: {encoder.classes_}")
print(f"   Expected classes: {EMOTIONS}")

if list(encoder.classes_) != EMOTIONS:
    print(f"   ✗ MISMATCH! Model was trained with wrong emotions")
    sys.exit(1)

# Generate fresh data for testing
print("\n3. Generating test data...")
X, y = generate_synthetic_features(n=2000)
print(f"   Generated {len(X)} samples across {len(EMOTIONS)} emotions")

# Check class distribution
unique, counts = np.unique(y, return_counts=True)
print("\n4. Class distribution:")
for emotion, count in zip(unique, counts):
    print(f"   {emotion}: {count} samples ({count/len(y)*100:.1f}%)")

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Scale features
X_test_scaled = scaler.transform(X_test)

# Predictions
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

# Convert to label space for metrics
y_test_labels = encoder.transform(y_test)
y_pred_labels = y_pred

# Classification report
print("\n5. Model Performance (test set):")
print("=" * 60)
report = classification_report(
    y_test_labels, y_pred_labels,
    target_names=EMOTIONS,
    output_dict=True
)
for emotion in EMOTIONS:
    metrics = report[emotion]
    print(f"   {emotion:12s} precision={metrics['precision']:.2f} recall={metrics['recall']:.2f} f1={metrics['f1-score']:.2f}")
print(f"   {'accuracy':12s} {report['accuracy']:.2f}")

# Confusion matrix
print("\n6. Confusion Matrix:")
print("=" * 60)
cm = confusion_matrix(y_test_labels, y_pred_labels)
print("                  Predicted →")
print("                  " + "  ".join([e[:8].ljust(10) for e in EMOTIONS]))
for i, emotion in enumerate(EMOTIONS):
    print(f"{emotion:10s} Actual →  " + "  ".join([f"{cm[i,j]:4d}" for j in range(len(EMOTIONS))]))

# Sanity test with crafted feature sets
print("\n7. Sanity Tests (crafted feature sets):")
print("=" * 60)

# Feature order: ['hesitation_score', 'price_dwell_time_s', 'rage_click_score',
#                 'scroll_retreat_count', 'exit_intent_count', 'checkout_hesitation_s',
#                 'velocity_variance', 'session_duration_s']

test_cases = [
    {
        "name": "High rage + high velocity + short (should be frustrated)",
        "features": {
            'hesitation_score': 0.7,
            'price_dwell_time_s': 2.0,
            'rage_click_score': 0.6,
            'scroll_retreat_count': 1,
            'exit_intent_count': 0,
            'checkout_hesitation_s': 5.0,
            'velocity_variance': 60000,
            'session_duration_s': 45,
        },
        "expected": "frustrated"
    },
    {
        "name": "High scroll retreats + high hesitation (should be confused)",
        "features": {
            'hesitation_score': 0.6,
            'price_dwell_time_s': 3.0,
            'rage_click_score': 0.1,
            'scroll_retreat_count': 6,
            'exit_intent_count': 2,
            'checkout_hesitation_s': 15.0,
            'velocity_variance': 8000,
            'session_duration_s': 90,
        },
        "expected": "confused"
    },
    {
        "name": "Long session + steady velocity + low rage (should be engaged)",
        "features": {
            'hesitation_score': 0.1,
            'price_dwell_time_s': 15.0,
            'rage_click_score': 0.05,
            'scroll_retreat_count': 1,
            'exit_intent_count': 0,
            'checkout_hesitation_s': 2.0,
            'velocity_variance': 12000,
            'session_duration_s': 300,
        },
        "expected": "engaged"
    },
    {
        "name": "Very short + minimal events (should be disengaged)",
        "features": {
            'hesitation_score': 0.05,
            'price_dwell_time_s': 1.0,
            'rage_click_score': 0.0,
            'scroll_retreat_count': 0,
            'exit_intent_count': 0,
            'checkout_hesitation_s': 0.5,
            'velocity_variance': 800,
            'session_duration_s': 8,
        },
        "expected": "disengaged"
    },
]

for test in test_cases:
    # Create feature vector in correct order
    from app.services.emotion_model import FEATURE_NAMES
    X = np.array([[test['features'].get(f, 0) for f in FEATURE_NAMES]])
    X_scaled = scaler.transform(X)
    proba = model.predict_proba(X_scaled)[0]

    # Get all predictions sorted by probability
    predictions = [(emotion, prob) for emotion, prob in zip(EMOTIONS, proba)]
    predictions.sort(key=lambda x: x[1], reverse=True)

    primary = predictions[0][0]
    confidence = predictions[0][1]

    status = "✓" if primary == test['expected'] else "✗"

    print(f"\n{status} {test['name']}")
    print(f"  Predicted: {primary} ({confidence*100:.1f}%)")
    print(f"  Expected:  {test['expected']}")
    print(f"  All probabilities:")
    for emotion, prob in predictions:
        bar = "█" * int(prob * 40)
        print(f"    {emotion:10s} {prob*100:5.1f}% {bar}")

# Check confidence spread
print("\n8. Confidence Spread Analysis:")
print("=" * 60)
confidence_scores = []
for proba in y_pred_proba:
    max_prob = proba.max()
    second_max = sorted(proba)[-2]
    confidence_scores.append((max_prob, second_max))

avg_confidence = np.mean([c[0] for c in confidence_scores])
avg_second = np.mean([c[1] for c in confidence_scores])
avg_gap = np.mean([c[0] - c[1] for c in confidence_scores])

print(f"   Average winner confidence:  {avg_confidence*100:.1f}%")
print(f"   Average runner-up:          {avg_second*100:.1f}%")
print(f"   Average gap:                {avg_gap*100:.1f}%")

if avg_confidence > 0.95:
    print(f"\n   ⚠ WARNING: Model is OVERCONFIDENT ({avg_confidence*100:.1f}% avg)")
    print(f"   This suggests training profiles are too distinct.")
    print(f"   Consider adding more overlap between emotion profiles.")
elif avg_confidence < 0.60:
    print(f"\n   ⚠ WARNING: Model is UNDERCONFIDENT ({avg_confidence*100:.1f}% avg)")
    print(f"   This suggests profiles are too similar.")
else:
    print(f"\n   ✓ Confidence spread looks HEALTHY")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
