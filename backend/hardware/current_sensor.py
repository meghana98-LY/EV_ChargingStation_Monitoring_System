"""
ACS712 current sensor interface.

Raspberry Pi:
    Reads the ACS712 analog output through MCP3008
    and calculates current using the sensor sensitivity.

Windows/development:
    Allows controlled current simulation using:

        SIMULATED_CURRENT=0
        SIMULATED_CURRENT=10
        SIMULATED_CURRENT=25

The simulation does not affect the real hardware path.
"""

from __future__ import annotations

import os
import platform

from backend.hardware.adc import MCP3008
from backend.config import CURRENT_CHANNEL


class CurrentSensor:
    """
    Interface for an ACS712 current sensor connected
    to the MCP3008.
    """

    def __init__(
        self,
        adc: MCP3008,
        channel: int = CURRENT_CHANNEL,
        sensitivity: float = 0.185,
        zero_current_voltage: float = 2.5,
    ):
        self.adc = adc
        self.channel = channel

        # ACS712-5A typical sensitivity:
        # 185 mV/A = 0.185 V/A
        #
        # Change this according to the actual ACS712
        # version being used.
        self.sensitivity = sensitivity

        # ACS712 output voltage at approximately zero current.
        # This value must be calibrated on the real hardware.
        self.zero_current_voltage = (
            zero_current_voltage
        )

        # Windows/development simulation.
        self.simulate = (
            platform.system() != "Linux"
        )

    # ========================================================
    # SIMULATION
    # ========================================================

    def _get_simulated_current(self) -> float:
        """
        Return the simulated current from the environment.

        Example:

            $env:SIMULATED_CURRENT="10"

        Returns:
            Current in amperes.
        """

        value = os.getenv(
            "SIMULATED_CURRENT",
            "0",
        )

        try:
            current = float(value)

        except ValueError as exc:

            raise ValueError(
                "SIMULATED_CURRENT must be a "
                "numeric value."
            ) from exc

        if current < 0:

            raise ValueError(
                "SIMULATED_CURRENT cannot be negative."
            )

        return current

    # ========================================================
    # ADC READING
    # ========================================================

    def read_adc_voltage(self) -> float:
        """
        Read the ACS712 output voltage from MCP3008.

        This method always reads the actual ADC interface.
        """

        return self.adc.read_voltage(
            self.channel
        )

    # ========================================================
    # CURRENT READING
    # ========================================================

    def read_current(self) -> float:
        """
        Read current in amperes.

        Windows:
            Uses SIMULATED_CURRENT.

        Raspberry Pi:
            Calculates current from the ACS712
            output voltage.
        """

        if self.simulate:

            return self._get_simulated_current()

        sensor_voltage = (
            self.read_adc_voltage()
        )

        current = (
            sensor_voltage
            - self.zero_current_voltage
        ) / self.sensitivity

        # Small values around zero are treated as zero.
        if abs(current) < 0.05:
            current = 0.0

        return abs(current)

    # ========================================================
    # COMPLETE READING
    # ========================================================

    def get_reading(self) -> dict:
        """
        Return the current measurement and
        corresponding sensor information.
        """

        if self.simulate:

            current = (
                self._get_simulated_current()
            )

            return {
                "sensor_voltage": None,
                "current": round(
                    current,
                    3,
                ),
            }

        sensor_voltage = (
            self.read_adc_voltage()
        )

        current = (
            sensor_voltage
            - self.zero_current_voltage
        ) / self.sensitivity

        if abs(current) < 0.05:
            current = 0.0

        return {
            "sensor_voltage": round(
                sensor_voltage,
                3,
            ),
            "current": round(
                abs(current),
                3,
            ),
        }