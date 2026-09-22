"""
Isolation Forest anomaly detection service.

The model uses:
    - Voltage
    - Current
    - Power

The trained model is loaded from:
    backend/models/isolation_forest.pkl
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import joblib

from backend.config import MODEL_PATH


class AnomalyDetector:
    """
    Isolation Forest based anomaly detector.
    """

    FEATURE_NAMES = [
        "voltage",
        "current",
        "power",
    ]

    def __init__(
        self,
        model_path: Path = MODEL_PATH,
    ):
        self.model_path = Path(model_path)
        self.model = None

        self.load_model()

    # ========================================================
    # MODEL LOADING
    # ========================================================

    def load_model(self) -> bool:
        """
        Load the trained Isolation Forest model.

        Returns
        -------
        bool
            True if model was loaded successfully.
            False if model does not exist.
        """

        if not self.model_path.exists():
            self.model = None
            return False

        try:
            self.model = joblib.load(self.model_path)
            return True

        except Exception as exc:
            self.model = None

            print(
                f"Warning: Unable to load anomaly model: {exc}"
            )

            return False

    # ========================================================
    # MODEL STATUS
    # ========================================================

    def is_model_available(self) -> bool:
        """
        Check whether the trained model is available.
        """

        return self.model is not None

    # ========================================================
    # FEATURE PREPARATION
    # ========================================================

    def _prepare_features(
        self,
        voltage: float,
        current: float,
        power: float,
    ) -> np.ndarray:
        """
        Convert sensor values into the feature format expected
        by Isolation Forest.
        """

        return np.array(
            [[
                float(voltage),
                float(current),
                float(power),
            ]],
            dtype=float,
        )

    # ========================================================
    # PREDICTION
    # ========================================================

    def predict(
        self,
        voltage: float,
        current: float,
        power: float,
    ) -> Tuple[str, Optional[float]]:
        """
        Predict whether a charging measurement is normal
        or anomalous.

        Returns
        -------
        tuple
            (
                status,
                anomaly_score
            )

        Possible status values:
            NORMAL
            ANOMALY
            MODEL_UNAVAILABLE
        """

        if self.model is None:
            return "MODEL_UNAVAILABLE", None

        features = self._prepare_features(
            voltage,
            current,
            power,
        )

        prediction = self.model.predict(features)

        score = self.model.decision_function(features)

        anomaly_score = float(score[0])

        if prediction[0] == -1:
            status = "ANOMALY"
        else:
            status = "NORMAL"

        return status, anomaly_score

    # ========================================================
    # COMPLETE RESULT
    # ========================================================

    def get_result(
        self,
        voltage: float,
        current: float,
        power: float,
    ) -> dict:
        """
        Return a complete anomaly detection result.
        """

        status, score = self.predict(
            voltage,
            current,
            power,
        )

        return {
            "status": status,
            "is_anomaly": status == "ANOMALY",
            "anomaly_score": (
                round(score, 6)
                if score is not None
                else None
            ),
            "model_available": self.is_model_available(),
        }