import numpy as np
import pandas as pd


def generate_emotion_samples(emotion, n=1000, seed=None):
    rng = np.random.default_rng(seed)

    profiles = {
        'confusion': {
            'hesitation_score': (0.70, 0.10, 0, 1),
            'price_dwell_time_s': (25.0, 10.0, 0, 120),
            'rage_click_score': (0.10, 0.05, 0, 1),
            'scroll_retreat_count': (6.0, 2.0, 0, 20),
            'exit_intent_count': (1.0, 0.8, 0, 5),
            'checkout_hesitation_s': (20.0, 10.0, 0, 120),
            'velocity_variance': (400.0, 100.0, 0, 2000),
            'session_duration_s': (120.0, 40.0, 10, 600),
        },
        'frustration': {
            'hesitation_score': (0.50, 0.15, 0, 1),
            'price_dwell_time_s': (5.0, 3.0, 0, 30),
            'rage_click_score': (0.75, 0.15, 0, 1),
            'scroll_retreat_count': (3.0, 2.0, 0, 15),
            'exit_intent_count': (3.5, 1.0, 0, 10),
            'checkout_hesitation_s': (5.0, 3.0, 0, 30),
            'velocity_variance': (850.0, 200.0, 0, 2000),
            'session_duration_s': (40.0, 20.0, 5, 180),
        },
        'delight': {
            'hesitation_score': (0.08, 0.05, 0, 0.3),
            'price_dwell_time_s': (8.0, 3.0, 0, 30),
            'rage_click_score': (0.00, 0.02, 0, 0.1),
            'scroll_retreat_count': (1.0, 1.0, 0, 5),
            'exit_intent_count': (0.1, 0.3, 0, 2),
            'checkout_hesitation_s': (2.0, 1.0, 0, 10),
            'velocity_variance': (180.0, 60.0, 0, 600),
            'session_duration_s': (250.0, 60.0, 60, 900),
        },
        'anxiety': {
            'hesitation_score': (0.60, 0.15, 0, 1),
            'price_dwell_time_s': (40.0, 15.0, 5, 180),
            'rage_click_score': (0.15, 0.10, 0, 0.5),
            'scroll_retreat_count': (5.0, 2.0, 0, 20),
            'exit_intent_count': (4.0, 1.5, 0, 12),
            'checkout_hesitation_s': (50.0, 15.0, 10, 180),
            'velocity_variance': (600.0, 150.0, 0, 2000),
            'session_duration_s': (180.0, 60.0, 30, 600),
        },
        'hesitation': {
            'hesitation_score': (0.82, 0.08, 0.5, 1),
            'price_dwell_time_s': (55.0, 20.0, 10, 240),
            'rage_click_score': (0.04, 0.03, 0, 0.2),
            'scroll_retreat_count': (5.0, 2.0, 0, 15),
            'exit_intent_count': (2.0, 1.0, 0, 6),
            'checkout_hesitation_s': (60.0, 20.0, 10, 180),
            'velocity_variance': (140.0, 50.0, 0, 500),
            'session_duration_s': (210.0, 70.0, 60, 800),
        },
        'focus': {
            'hesitation_score': (0.12, 0.06, 0, 0.3),
            'price_dwell_time_s': (15.0, 5.0, 0, 40),
            'rage_click_score': (0.01, 0.01, 0, 0.05),
            'scroll_retreat_count': (1.0, 1.0, 0, 4),
            'exit_intent_count': (0.1, 0.3, 0, 1),
            'checkout_hesitation_s': (3.0, 2.0, 0, 15),
            'velocity_variance': (95.0, 35.0, 0, 300),
            'session_duration_s': (320.0, 80.0, 90, 900),
        },
        'boredom': {
            'hesitation_score': (0.28, 0.10, 0, 0.6),
            'price_dwell_time_s': (2.0, 1.0, 0, 10),
            'rage_click_score': (0.04, 0.03, 0, 0.2),
            'scroll_retreat_count': (2.0, 1.0, 0, 8),
            'exit_intent_count': (1.0, 0.8, 0, 4),
            'checkout_hesitation_s': (1.0, 1.0, 0, 8),
            'velocity_variance': (45.0, 20.0, 0, 150),
            'session_duration_s': (28.0, 12.0, 5, 80),
        },
        'satisfaction': {
            'hesitation_score': (0.05, 0.03, 0, 0.15),
            'price_dwell_time_s': (10.0, 4.0, 0, 30),
            'rage_click_score': (0.00, 0.01, 0, 0.05),
            'scroll_retreat_count': (0.5, 0.5, 0, 3),
            'exit_intent_count': (0.0, 0.2, 0, 1),
            'checkout_hesitation_s': (1.5, 1.0, 0, 8),
            'velocity_variance': (160.0, 50.0, 0, 400),
            'session_duration_s': (290.0, 70.0, 90, 900),
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

def generate_all(n_per_class=1000, seed=42):
    emotions = [
        'confusion', 'frustration', 'delight',
        'anxiety', 'hesitation', 'focus',
        'boredom', 'satisfaction'
    ]
    dfs = [
        generate_emotion_samples(e, n_per_class, seed=seed+i)
        for i, e in enumerate(emotions)
    ]
    df = pd.concat(dfs, ignore_index=True)

    # Add 15% noise — swap emotion labels randomly
    noise_idx = rng = np.random.default_rng(seed)
    n_noise = int(len(df) * 0.15)
    noise_rows = rng.choice(len(df), n_noise, replace=False)
    df.loc[noise_rows, 'emotion'] = rng.choice(
        emotions, n_noise
    )

    # Shuffle
    df = df.sample(frac=1, random_state=seed).reset_index(drop=True)
    return df

if __name__ == '__main__':
    df = generate_all()
    print(f'Generated {len(df)} samples')
    print(df['emotion'].value_counts())
    df.to_csv('ml/data/synthetic_emotions.csv', index=False)
    print('Saved to ml/data/synthetic_emotions.csv')
