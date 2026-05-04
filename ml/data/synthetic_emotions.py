import numpy as np
import pandas as pd


def generate_emotion_samples(emotion, n=1000, seed=None):
    rng = np.random.default_rng(seed)

    # UPDATED PROFILES to fix model bias:
    # - 'engaged' is now the DEFAULT for normal browsing (wider range: 20-300s)
    # - 'disengaged' is ONLY for very short sessions (3-15s, minimal interaction)
    # This matches real-world distribution where most tracked users are engaged
    profiles = {
        'confused': {
            'hesitation_score': (0.70, 0.10, 0, 1),
            'price_dwell_time_s': (25.0, 10.0, 0, 120),
            'rage_click_score': (0.10, 0.05, 0, 1),
            'scroll_retreat_count': (6.0, 2.0, 0, 20),
            'exit_intent_count': (1.0, 0.8, 0, 5),
            'checkout_hesitation_s': (20.0, 10.0, 0, 120),
            'velocity_variance': (400.0, 100.0, 0, 2000),
            'session_duration_s': (120.0, 40.0, 10, 600),
        },
        'frustrated': {
            'hesitation_score': (0.50, 0.15, 0, 1),
            'price_dwell_time_s': (5.0, 3.0, 0, 30),
            'rage_click_score': (0.75, 0.15, 0, 1),
            'scroll_retreat_count': (3.0, 2.0, 0, 15),
            'exit_intent_count': (3.5, 1.0, 0, 10),
            'checkout_hesitation_s': (5.0, 3.0, 0, 30),
            'velocity_variance': (850.0, 200.0, 0, 2000),
            'session_duration_s': (40.0, 20.0, 5, 180),
        },
        # ENGAGED: Normal browsing behavior - should be the DEFAULT classification
        # Broad range to capture most real users: 20-300s, moderate interaction
        'engaged': {
            'hesitation_score': (0.12, 0.08, 0, 0.4),  # Slightly higher variance
            'price_dwell_time_s': (10.0, 5.0, 0, 45),  # Wider range
            'rage_click_score': (0.02, 0.03, 0, 0.2),   # Allow some rage clicks
            'scroll_retreat_count': (1.5, 1.5, 0, 8),  # More variation
            'exit_intent_count': (0.2, 0.4, 0, 2),     # Low but can happen
            'checkout_hesitation_s': (3.0, 2.0, 0, 20), # Wider range
            'velocity_variance': (220.0, 80.0, 0, 800), # Higher variance
            'session_duration_s': (80.0, 50.0, 20, 300), # 20-300s range - THIS IS KEY
        },
        # DISENGAGED: ONLY for very short sessions with minimal interaction
        # Lands and immediately leaves - NOT normal browsing
        'disengaged': {
            'hesitation_score': (0.35, 0.15, 0, 0.8),  # Higher hesitation (confused then leaves)
            'price_dwell_time_s': (1.5, 1.0, 0, 5),    # Very quick glance
            'rage_click_score': (0.02, 0.02, 0, 0.1),  # Minimal interaction
            'scroll_retreat_count': (0.5, 0.8, 0, 3),  # Little to no scrolling
            'exit_intent_count': (2.0, 1.0, 0, 5),     # High exit intent
            'checkout_hesitation_s': (0.5, 0.5, 0, 3), # No consideration
            'velocity_variance': (30.0, 15.0, 0, 100), # Low activity
            'session_duration_s': (8.0, 5.0, 3, 15),   # 3-15s ONLY - KEY CHANGE
        },
    }

    p = profiles[emotion]
    samples = {}
    for feature, (mean, std, low, high) in p.items():
        values = rng.normal(mean, std, n)
        samples[feature] = np.clip(values, low, high)

    df = pd.DataFrame(samples)
    df['emotion'] = emotion
    return df

def generate_all(n_total=10000, seed=42):
    # REBALANCED distribution to fix model bias:
    # - engaged: 40% (most users who stay on a site are engaged)
    # - confused: 25%
    # - frustrated: 20%
    # - disengaged: 15% (only bounce visitors)
    # This reflects real-world distribution better than equal classes
    emotions = [
        ('engaged', 0.40),      # 4000 samples
        ('confused', 0.25),     # 2500 samples
        ('frustrated', 0.20),   # 2000 samples
        ('disengaged', 0.15),   # 1500 samples
    ]

    rng = np.random.default_rng(seed)
    dfs = []

    for emotion, ratio in emotions:
        n_samples = int(n_total * ratio)
        dfs.append(generate_emotion_samples(emotion, n_samples, seed=seed+len(dfs)))

    df = pd.concat(dfs, ignore_index=True)

    # Add 10% noise — swap emotion labels randomly (reduced from 15%)
    n_noise = int(len(df) * 0.10)
    noise_rows = rng.choice(len(df), n_noise, replace=False)
    df.loc[noise_rows, 'emotion'] = rng.choice(
        [e for e, _ in emotions], n_noise
    )

    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df

if __name__ == '__main__':
    df = generate_all()
    print(f'Generated {len(df)} samples')
    print('\nEmotion distribution:')
    print(df['emotion'].value_counts())
    print('\nPercentage distribution:')
    print(df['emotion'].value_counts(normalize=True) * 100)
    df.to_csv('ml/data/synthetic_emotions.csv', index=False)
    print('\nSaved to ml/data/synthetic_emotions.csv')
    print('\nKEY CHANGES:')
    print('- engaged: 40% (was 25%) - broader range 20-300s duration')
    print('- disengaged: 15% (was 25%) - ONLY 3-15s, minimal interaction')
    print('- confused: 25% (was 25%)')
    print('- frustrated: 20% (was 25%)')
