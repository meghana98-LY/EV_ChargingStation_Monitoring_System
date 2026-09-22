"""
Train the Isolation Forest anomaly detection model.

Features:
    - voltage
    - current
    - power

The trained model is saved to:
    backend/models/isolation_forest.pkl
"""

from __future__ import annotations

from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import IsolationForest

from backend.config import (
    MODEL_DIR,
    MODEL_PATH,
    ISOLATION_FOREST_ESTIMATORS,
    ISOLATION_FOREST_CONTAMINATION,
    ISOLATION_FOREST_RANDOM_STATE,
)


# ============================================================
# TRAINING DATA
# ============================================================

def generate_training_data(
    samples: int = 500,
) -> np.ndarray:
    """
    Generate representative normal EV charging measurements.

    Columns:
        0 -> voltage
        1 -> current
        2 -> power

    Power is calculated from voltage × current.
    """

    rng = np.random.default_rng(42)

    # Normal operating voltage around 230 V.
    voltage = rng.normal(
        loc=230.0,
        scale=5.0,
        size=samples,
    )

    # Normal charging current.
    current = rng.normal(
        loc=10.0,
        scale=1.5,
        size=samples,
    )

    # Prevent negative current values.
    current = np.clip(
        current,
        0.5,
        None,
    )

    # Power calculated from voltage and current.
    power = voltage * current

    training_data = np.column_stack(
        (
            voltage,
            current,
            power,
        )
    )

    return training_data


# ============================================================
# MODEL TRAINING
# ============================================================

def train_model() -> IsolationForest:
    """
    Train the Isolation Forest model.
    """

    print("=" * 60)
    print("ISOLATION FOREST MODEL TRAINING")
    print("=" * 60)

    # Generate representative normal charging data.
    training_data = generate_training_data()

    print(
        f"Training samples : {len(training_data)}"
    )

    print(
        f"Features         : voltage, current, power"
    )

    # Create Isolation Forest.
    model = IsolationForest(
        n_estimators=ISOLATION_FOREST_ESTIMATORS,
        contamination=ISOLATION_FOREST_CONTAMINATION,
        random_state=ISOLATION_FOREST_RANDOM_STATE,
    )

    # Train model.
    model.fit(training_data)

    print("Model training completed.")

    return model


# ============================================================
# MODEL SAVING
# ============================================================

def save_model(
    model: IsolationForest,
) -> None:
    """
    Save trained model to backend/models.
    """

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    print(
        f"Model saved to:\n{MODEL_PATH}"
    )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    model = train_model()

    save_model(model)

    print("=" * 60)
    print("MODEL TRAINING SUCCESSFUL")
    print("=" * 60)