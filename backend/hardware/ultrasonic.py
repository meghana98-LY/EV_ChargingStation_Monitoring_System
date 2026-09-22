"""
HC-SR04 ultrasonic sensor interface.

Raspberry Pi:
    Uses GPIO trigger/echo timing.

Windows/development:
    Uses SIMULATED_DISTANCE for controlled testing.

Examples:

    $env:SIMULATED_DISTANCE="20"
    $env:SIMULATED_DISTANCE="50"
"""

from __future__ import annotations

import os
import platform
import time
from typing import Optional

from backend.config import (
    ULTRASONIC_TRIGGER_PIN,
    ULTRASONIC_ECHO_PIN,
)


class UltrasonicSensor:
    """
    Interface for the HC-SR04 ultrasonic sensor.
    """

    def __init__(
        self,
        trigger_pin: int = ULTRASONIC_TRIGGER_PIN,
        echo_pin: int = ULTRASONIC_ECHO_PIN,
        simulate: Optional[bool] = None,
    ):
        self.trigger_pin = trigger_pin
        self.echo_pin = echo_pin
        self.GPIO = None

        if simulate is None:
            simulate = platform.system() != "Linux"

        self.simulate = simulate

        if not self.simulate:
            self._initialize_gpio()

    # ========================================================
    # GPIO INITIALIZATION
    # ========================================================

    def _initialize_gpio(self) -> None:
        """
        Initialize Raspberry Pi GPIO.
        """

        try:
            import RPi.GPIO as GPIO

        except ImportError as exc:
            raise RuntimeError(
                "RPi.GPIO is required when running "
                "on Raspberry Pi."
            ) from exc

        self.GPIO = GPIO

        self.GPIO.setmode(GPIO.BCM)

        self.GPIO.setup(
            self.trigger_pin,
            GPIO.OUT,
        )

        self.GPIO.setup(
            self.echo_pin,
            GPIO.IN,
        )

        self.GPIO.output(
            self.trigger_pin,
            GPIO.LOW,
        )

        time.sleep(0.1)

    # ========================================================
    # SIMULATION
    # ========================================================

    def _get_simulated_distance(self) -> float:
        """
        Get simulated HC-SR04 distance.

        Environment variable:

            SIMULATED_DISTANCE

        Default:

            20 cm
        """

        value = os.getenv(
            "SIMULATED_DISTANCE",
            "20",
        )

        try:
            distance = float(value)

        except ValueError as exc:
            raise ValueError(
                "SIMULATED_DISTANCE must be a "
                "numeric value."
            ) from exc

        if distance <= 0:
            raise ValueError(
                "SIMULATED_DISTANCE must be greater "
                "than 0 cm."
            )

        return distance

    # ========================================================
    # DISTANCE READING
    # ========================================================

    def read_distance(self) -> float:
        """
        Measure distance in centimetres.
        """

        if self.simulate:
            return self._get_simulated_distance()

        if self.GPIO is None:
            raise RuntimeError(
                "GPIO has not been initialized."
            )

        # Send 10 microsecond trigger pulse.
        self.GPIO.output(
            self.trigger_pin,
            GPIO.HIGH,
        )

        time.sleep(0.00001)

        self.GPIO.output(
            self.trigger_pin,
            GPIO.LOW,
        )

        timeout = time.time() + 0.05

        pulse_start = time.time()

        while self.GPIO.input(
            self.echo_pin
        ) == GPIO.LOW:

            pulse_start = time.time()

            if pulse_start > timeout:
                return -1.0

        timeout = time.time() + 0.05

        pulse_end = time.time()

        while self.GPIO.input(
            self.echo_pin
        ) == GPIO.HIGH:

            pulse_end = time.time()

            if pulse_end > timeout:
                return -1.0

        pulse_duration = (
            pulse_end - pulse_start
        )

        # Speed of sound ≈ 343 m/s.
        # Divide by 2 because the sound travels
        # to the object and back.
        distance = (
            pulse_duration * 34300
        ) / 2

        return round(
            distance,
            2,
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self) -> None:
        """
        Release Raspberry Pi GPIO resources.
        """

        if self.GPIO is not None:
            self.GPIO.cleanup(
                [
                    self.trigger_pin,
                    self.echo_pin,
                ]
            )