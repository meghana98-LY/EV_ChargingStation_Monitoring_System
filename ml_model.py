"""
ML model management for anomaly detection.
Uses Isolation Forest to detect anomalous charging patterns.
"""
import pickle
import os
from typing import Tuple, Optional
from sklearn.ensemble import IsolationForest
import numpy as np
from config import Config
from logger import get_logger

logger = get_logger('ml_model')


class AnomalyModel:
    """Manages Isolation Forest anomaly detection model."""
    
    def __init__(self, model_path: Optional[str] = None):
        """
        Initialize anomaly model.
        
        Args:
            model_path: Path to saved model. If not provided, uses Config.ML_MODEL_PATH
        """
        self.model_path = model_path or Config.ML_MODEL_PATH
        self.model = None
        self.is_trained = False
        self.threshold = Config.ANOMALY_THRESHOLD
        
        # Try to load existing model
        if self.load_model():
            self.is_trained = True
        else:
            logger.warning("No trained model found. Use train() before predictions.")
    
    def load_model(self) -> bool:
        """
        Load saved model from disk.
        
        Returns:
            True if successful, False otherwise
        """
        if not os.path.exists(self.model_path):
            logger.debug(f"Model file not found at {self.model_path}")
            return False
        
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            logger.info(f"Model loaded from {self.model_path}")
            self.is_trained = True
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            return False
    
    def save_model(self) -> bool:
        """
        Save trained model to disk.
        
        Returns:
            True if successful, False otherwise
        """
        if self.model is None:
            logger.error("No model to save")
            return False
        
        try:
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            logger.info(f"Model saved to {self.model_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {str(e)}")
            return False
    
    def train(self, voltage_readings: list, current_readings: list) -> bool:
        """
        Train Isolation Forest model on normal data.
        
        Args:
            voltage_readings: List of voltage values
            current_readings: List of current values
        
        Returns:
            True if training successful, False otherwise
        """
        try:
            if len(voltage_readings) < 10:
                logger.warning("Need at least 10 samples for training")
                return False
            
            # Prepare training data (features: voltage and current)
            X = np.column_stack([voltage_readings, current_readings])
            
            # Train Isolation Forest
            # contamination is the expected proportion of anomalies
            self.model = IsolationForest(
                contamination=0.1,  # Expect ~10% anomalies
                random_state=42,
                n_estimators=100
            )
            self.model.fit(X)
            self.is_trained = True
            
            # Save model
            self.save_model()
            logger.info(f"Model trained on {len(voltage_readings)} samples")
            return True
        
        except Exception as e:
            logger.error(f"Model training failed: {str(e)}")
            return False
    
    def predict(self, voltage: float, current: float) -> Tuple[str, float]:
        """
        Predict if reading is anomalous.
        
        Args:
            voltage: Voltage reading in volts
            current: Current reading in amps
        
        Returns:
            Tuple of (prediction, anomaly_score)
            prediction: 'Normal' or 'Anomaly Detected'
            anomaly_score: Anomaly score (-1.0 to 1.0, higher = more anomalous)
        
        Raises:
            RuntimeError if model not trained
        """
        if not self.is_trained or self.model is None:
            raise RuntimeError("Model not trained. Cannot make predictions.")
        
        try:
            # Prepare input
            X = np.array([[voltage, current]])
            
            # Get prediction (-1 for anomaly, 1 for normal)
            prediction_value = self.model.predict(X)[0]
            
            # Get anomaly score
            anomaly_score = self.model.score_samples(X)[0]
            
            # Interpret result
            prediction = 'Normal' if prediction_value == 1 else 'Anomaly Detected'
            
            return (prediction, float(anomaly_score))
        
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            raise RuntimeError(f"ML prediction error: {str(e)}")
    
    def get_status(self) -> dict:
        """Get model status information."""
        return {
            'is_trained': self.is_trained,
            'model_path': self.model_path,
            'threshold': self.threshold,
            'model_type': 'Isolation Forest'
        }


# Global model instance
_model = None


def get_model() -> AnomalyModel:
    """Get or create global anomaly model instance."""
    global _model
    if _model is None:
        _model = AnomalyModel()
    return _model


if __name__ == '__main__':
    model = get_model()
    print(f"Model status: {model.get_status()}")
    
    if not model.is_trained:
        # Generate normal training data
        import random
        voltages = [12.0 + random.gauss(0, 0.3) for _ in range(100)]
        currents = [7.0 + random.gauss(0, 0.2) for _ in range(100)]
        
        print("Training model on simulated normal data...")
        if model.train(voltages, currents):
            print("Model trained successfully")
    
    # Test predictions
    if model.is_trained:
        test_cases = [
            (12.0, 7.0, "Normal case"),
            (11.5, 6.8, "Normal case"),
            (16.0, 15.0, "Anomaly case - high voltage and current"),
            (8.0, 2.0, "Anomaly case - low values"),
        ]
        
        for voltage, current, description in test_cases:
            try:
                pred, score = model.predict(voltage, current)
                print(f"{description}: {pred} (score: {score:.4f})")
            except Exception as e:
                print(f"Prediction error: {e}")
