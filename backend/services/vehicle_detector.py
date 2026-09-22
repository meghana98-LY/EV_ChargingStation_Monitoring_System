"""
Vehicle/object detection service.

Uses the HC-SR04 ultrasonic sensor to determine whether
a vehicle/object is present near the charging station.
"""

from backend.config import VEHICLE_DISTANCE_THRESHOLD_CM
from backend.hardware.ultrasonic import UltrasonicSensor


class VehicleDetector:
    """
    Determines vehicle/object presence using HC-SR04 distance.
    """

    def __init__(
        self,
        sensor: UltrasonicSensor,
        threshold_cm: float = VEHICLE_DISTANCE_THRESHOLD_CM,
    ):
        self.sensor = sensor
        self.threshold_cm = threshold_cm

    def get_distance(self) -> float:
        """
        Read the current distance from the ultrasonic sensor.
        """

        return self.sensor.read_distance()

    def is_vehicle_present(self) -> bool:
        """
        Determine whether a vehicle/object is present.

        Returns
        -------
        bool
            True  -> vehicle/object detected
            False -> no vehicle/object detected
        """

        distance = self.get_distance()

        # Invalid sensor reading
        if distance < 0:
            return False

        return distance < self.threshold_cm

    def get_status(self) -> dict:
        """
        Return complete vehicle detection information.
        """

        distance = self.get_distance()

        if distance < 0:
            return {
                "distance_cm": None,
                "vehicle_present": False,
                "status": "SENSOR_ERROR",
            }

        vehicle_present = distance < self.threshold_cm

        return {
            "distance_cm": round(distance, 2),
            "vehicle_present": vehicle_present,
            "status": (
                "VEHICLE_PRESENT"
                if vehicle_present
                else "NO_VEHICLE"
            ),
        }