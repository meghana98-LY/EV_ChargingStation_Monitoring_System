"""
Cache manager for fault tolerance.
Saves and loads last-known-good sensor readings with atomic writes.
"""
import json
import os
import tempfile
import time
from datetime import datetime
from typing import Optional, Dict, Any
from config import Config
from logger import get_logger

logger = get_logger('cache_manager')


class CacheManager:
    """Manages persistent cache of last-known-good sensor readings."""
    
    def __init__(self):
        """Initialize cache manager."""
        self.cache_dir = Config.CACHE_DIR
        self.cache_file = Config.CACHE_FILE
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def save_reading(self, timestamp: str, voltage: float, current: float,
                     power: float, prediction: str, anomaly_score: float,
                     severity: str) -> bool:
        """
        Save sensor reading to cache with atomic write.
        
        Args:
            timestamp: ISO format timestamp
            voltage: Voltage reading in volts
            current: Current reading in amps
            power: Power in watts
            prediction: Prediction result (e.g., "Anomaly Detected")
            anomaly_score: Anomaly score from ML model
            severity: Severity level (NORMAL, WARNING, CRITICAL)
        
        Returns:
            True if successful, False otherwise
        """
        try:
            cache_data = {
                'timestamp': timestamp,
                'voltage': round(voltage, 2),
                'current': round(current, 2),
                'power': round(power, 2),
                'prediction': prediction,
                'anomaly_score': round(anomaly_score, 4),
                'severity': severity,
                'cached_at': datetime.now().isoformat(),
                'is_live': True,
                'data_source': 'sensor'
            }
            
            # Write to temporary file first (atomic write)
            fd, temp_path = tempfile.mkstemp(dir=self.cache_dir, suffix='.json')
            try:
                with os.fdopen(fd, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                # Atomic rename
                os.replace(temp_path, self.cache_file)
                logger.debug(f"Cache saved successfully: {self.cache_file}")
                return True
            except Exception as e:
                # Clean up temp file if write failed
                try:
                    os.close(fd)
                except:
                    pass
                try:
                    os.remove(temp_path)
                except:
                    pass
                raise e
        
        except Exception as e:
            logger.error(f"Failed to save cache: {str(e)}")
            return False
    
    def load_cache(self) -> Optional[Dict[str, Any]]:
        """
        Load cached reading if available.
        
        Returns:
            Dictionary with cached data or None if not available/stale
        """
        try:
            if not os.path.exists(self.cache_file):
                logger.warning("Cache file not found")
                return None
            
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            # Check cache age
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            age_seconds = (datetime.now() - cached_at).total_seconds()
            
            if age_seconds > Config.CACHE_MAX_AGE_SECONDS:
                logger.warning(f"Cache is stale (age: {age_seconds:.1f}s)")
                cache_data['is_live'] = False
                cache_data['data_source'] = 'stale_cache'
                return cache_data
            
            logger.debug(f"Cache loaded (age: {age_seconds:.1f}s)")
            return cache_data
        
        except json.JSONDecodeError as e:
            logger.error(f"Cache file corrupted: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Failed to load cache: {str(e)}")
            return None
    
    def clear_cache(self) -> bool:
        """
        Clear the cache file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.cache_file):
                os.remove(self.cache_file)
                logger.info("Cache cleared")
                return True
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {str(e)}")
            return False
    
    def get_cache_status(self) -> Dict[str, Any]:
        """Get cache status information."""
        if not os.path.exists(self.cache_file):
            return {
                'status': 'unavailable',
                'has_cache': False,
                'message': 'No cache available'
            }
        
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
            
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            age_seconds = (datetime.now() - cached_at).total_seconds()
            is_stale = age_seconds > Config.CACHE_MAX_AGE_SECONDS
            
            return {
                'status': 'stale' if is_stale else 'fresh',
                'has_cache': True,
                'age_seconds': age_seconds,
                'cached_at': cache_data['cached_at'],
                'last_voltage': cache_data.get('voltage'),
                'last_current': cache_data.get('current'),
                'last_severity': cache_data.get('severity')
            }
        except Exception as e:
            return {
                'status': 'error',
                'has_cache': False,
                'message': f'Error reading cache: {str(e)}'
            }


# Global cache manager instance
_cache_manager = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


if __name__ == '__main__':
    cache = CacheManager()
    
    # Test save
    cache.save_reading(
        timestamp=datetime.now().isoformat(),
        voltage=12.5,
        current=8.2,
        power=102.5,
        prediction='Anomaly Detected',
        anomaly_score=-0.3,
        severity='WARNING'
    )
    
    # Test load
    data = cache.load_cache()
    if data:
        print(f"Cached data: {json.dumps(data, indent=2)}")
    
    # Test status
    status = cache.get_cache_status()
    print(f"Cache status: {status}")
