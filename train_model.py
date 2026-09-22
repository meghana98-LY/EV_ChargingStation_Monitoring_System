"""
Script to train the Isolation Forest anomaly detection model.
Generates normal charging data and trains the model.
"""
import random
from ml_model import get_model
from config import Config
from logger import get_logger

logger = get_logger('train_model')


def generate_normal_charging_data(num_samples: int = 200):
    """
    Generate simulated normal EV charging data for training.
    
    Args:
        num_samples: Number of training samples to generate
    
    Returns:
        Tuple of (voltages, currents)
    """
    logger.info(f"Generating {num_samples} normal charging samples...")
    
    voltages = []
    currents = []
    
    for i in range(num_samples):
        # Normal charging: stable voltage around 12V, stable current around 7A
        # with small random variations
        voltage = Config.SIMULATION_VOLTAGE_BASE + random.gauss(0, 0.2)
        current = Config.SIMULATION_CURRENT_BASE + random.gauss(0, 0.15)
        
        # Clamp to realistic ranges
        voltage = max(11.5, min(12.5, voltage))
        current = max(6.0, min(8.0, current))
        
        voltages.append(voltage)
        currents.append(current)
    
    logger.info(f"Generated data - Voltage range: {min(voltages):.2f}-{max(voltages):.2f}V, "
                f"Current range: {min(currents):.2f}-{max(currents):.2f}A")
    
    return voltages, currents


def train_model():
    """Train the anomaly detection model."""
    logger.info("Starting model training...")
    
    # Generate normal charging data
    voltages, currents = generate_normal_charging_data(num_samples=200)
    
    # Get model and train
    model = get_model()
    
    if model.train(voltages, currents):
        logger.info("Model training completed successfully")
        
        # Test predictions on normal data
        logger.info("Testing predictions on normal data...")
        test_voltage = Config.SIMULATION_VOLTAGE_BASE
        test_current = Config.SIMULATION_CURRENT_BASE
        
        try:
            prediction, score = model.predict(test_voltage, test_current)
            logger.info(f"Normal prediction: {prediction} (score: {score:.4f})")
        except Exception as e:
            logger.error(f"Prediction test failed: {e}")
        
        # Test predictions on anomalous data
        logger.info("Testing predictions on anomalous data...")
        anomaly_cases = [
            (15.0, 12.0, "High voltage and current"),
            (10.0, 3.0, "Low values"),
            (14.5, 11.0, "Elevated readings"),
        ]
        
        for v, i, desc in anomaly_cases:
            try:
                prediction, score = model.predict(v, i)
                logger.info(f"  {desc}: {prediction} (score: {score:.4f})")
            except Exception as e:
                logger.error(f"Prediction failed: {e}")
    
    else:
        logger.error("Model training failed")
        return False
    
    return True


if __name__ == '__main__':
    import sys
    
    logger.info("=" * 60)
    logger.info("EV Charging Station - Anomaly Model Training")
    logger.info("=" * 60)
    
    success = train_model()
    
    logger.info("=" * 60)
    if success:
        logger.info("Training completed successfully!")
        logger.info(f"Model saved to: {Config.ML_MODEL_PATH}")
        sys.exit(0)
    else:
        logger.error("Training failed!")
        sys.exit(1)
