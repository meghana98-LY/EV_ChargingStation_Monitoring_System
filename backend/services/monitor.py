"""
Central monitoring service for the EV charging station.

Combines:

    - Voltage sensor
    - Current sensor
    - Power calculation
    - HC-SR04 vehicle detection
    - Charging status
    - Isolation Forest anomaly detection
    - Vehicle-aware protection logic
"""

from __future__ import annotations

from typing import Optional

from backend.hardware.adc import MCP3008
from backend.hardware.voltage_sensor import VoltageSensor
from backend.hardware.current_sensor import CurrentSensor
from backend.hardware.ultrasonic import UltrasonicSensor
from backend.hardware.gpio import GPIOController

from backend.services.vehicle_detector import VehicleDetector
from backend.services.anomaly_detector import AnomalyDetector
from backend.services.protection import ProtectionService


class ChargingMonitor:
    """
    Central service responsible for collecting and combining
    all charging station measurements.
    """

    def __init__(
        self,
        adc: Optional[MCP3008] = None,
        voltage_sensor: Optional[VoltageSensor] = None,
        current_sensor: Optional[CurrentSensor] = None,
        ultrasonic_sensor: Optional[UltrasonicSensor] = None,
        gpio_controller: Optional[GPIOController] = None,
        anomaly_detector: Optional[AnomalyDetector] = None,
        protection_service: Optional[ProtectionService] = None,
    ):
        self.adc = adc or MCP3008()

        self.voltage_sensor = (
            voltage_sensor
            or VoltageSensor(self.adc)
        )

        self.current_sensor = (
            current_sensor
            or CurrentSensor(self.adc)
        )

        self.ultrasonic_sensor = (
            ultrasonic_sensor
            or UltrasonicSensor()
        )

        self.vehicle_detector = VehicleDetector(
            self.ultrasonic_sensor
        )

        self.gpio_controller = (
            gpio_controller
            or GPIOController()
        )

        self.anomaly_detector = (
            anomaly_detector
            or AnomalyDetector()
        )

        self.protection_service = (
            protection_service
            or ProtectionService()
        )

    # ========================================================
    # SENSOR READINGS
    # ========================================================

    def read_voltage(self) -> float:
        return self.voltage_sensor.read_voltage()

    def read_current(self) -> float:
        return self.current_sensor.read_current()

    def calculate_power(
        self,
        voltage: float,
        current: float,
    ) -> float:
        return voltage * current

    # ========================================================
    # MAIN MONITORING FUNCTION
    # ========================================================

    def read_all(self) -> dict:

        # ----------------------------------------------------
        # Electrical measurements
        # ----------------------------------------------------

        voltage = self.read_voltage()
        current = self.read_current()

        power = self.calculate_power(
            voltage,
            current,
        )

        # ----------------------------------------------------
        # Vehicle detection
        # ----------------------------------------------------

        vehicle_status = (
            self.vehicle_detector.get_status()
        )

        vehicle_present = vehicle_status[
            "vehicle_present"
        ]

        # ----------------------------------------------------
        # Charging status
        # ----------------------------------------------------

        charging_status = (
            self.gpio_controller.get_charging_status()
        )

        charging_active = charging_status[
            "charging_active"
        ]

        # ----------------------------------------------------
        # Anomaly detection
        #
        # IMPORTANT:
        # Anomaly detection is performed only when charging
        # is active.
        #
        # When charging is inactive, zero current and zero
        # power are expected and should not be classified
        # as an electrical anomaly.
        # ----------------------------------------------------

        if charging_active:

            anomaly_result = (
                self.anomaly_detector.get_result(
                    voltage,
                    current,
                    power,
                )
            )

        else:

            anomaly_result = {
                "status": "NOT_EVALUATED",
                "is_anomaly": False,
                "anomaly_score": None,
                "model_available": (
                    self.anomaly_detector.is_model_available()
                ),
            }

        is_anomaly = anomaly_result[
            "is_anomaly"
        ]

        # ----------------------------------------------------
        # Protection logic
        # ----------------------------------------------------

        protection_result = (
            self.protection_service.evaluate(
                charging_active=charging_active,
                is_anomaly=is_anomaly,
                vehicle_present=vehicle_present,
            )
        )

        # ----------------------------------------------------
        # Combined monitoring result
        # ----------------------------------------------------

        return {
            "voltage": round(
                voltage,
                2,
            ),

            "current": round(
                current,
                3,
            ),

            "power": round(
                power,
                2,
            ),

            "distance_cm": vehicle_status[
                "distance_cm"
            ],

            "vehicle_present": vehicle_present,

            "vehicle_status": vehicle_status[
                "status"
            ],

            "charging_active": charging_active,

            "charging_status": charging_status[
                "status"
            ],

            "anomaly_status": anomaly_result[
                "status"
            ],

            "is_anomaly": is_anomaly,

            "anomaly_score": anomaly_result[
                "anomaly_score"
            ],

            "model_available": anomaly_result[
                "model_available"
            ],

            "protection_triggered": protection_result[
                "protection_triggered"
            ],

            "protection_status": protection_result[
                "status"
            ],

            "protection_reason": protection_result[
                "reason"
            ],
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self) -> None:

        self.ultrasonic_sensor.cleanup()

        self.gpio_controller.cleanup()

        self.adc.close()