"""
GPIO interface for the EV charging station.

Currently used for:
    - Charging status toggle switch

GPIO numbering:
    BCM mode

Development:
    On Windows, charging status can be controlled using:

        SIMULATED_CHARGING=true

    or:

        SIMULATED_CHARGING=false

Raspberry Pi:
    The actual GPIO switch on CHARGING_SWITCH_PIN is used.
"""

from __future__ import annotations

import os
import platform
from typing import Optional

from backend.config import CHARGING_SWITCH_PIN


class GPIOController:
    """
    Handles GPIO inputs related to charging status.
    """

    def __init__(
        self,
        charging_pin: int = CHARGING_SWITCH_PIN,
        simulate: Optional[bool] = None,
        simulated_charging: Optional[bool] = None,
    ):
        self.charging_pin = charging_pin

        # Automatically use simulation on non-Linux systems.
        if simulate is None:
            simulate = platform.system() != "Linux"

        self.simulate = simulate

        self.GPIO = None

        # ----------------------------------------------------
        # Simulation configuration
        # ----------------------------------------------------

        if self.simulate:

            if simulated_charging is not None:

                self.simulated_charging = (
                    simulated_charging
                )

            else:

                simulated_value = os.getenv(
                    "SIMULATED_CHARGING",
                    "false",
                ).strip().lower()

                self.simulated_charging = (
                    simulated_value
                    in {
                        "true",
                        "1",
                        "yes",
                        "on",
                    }
                )

        else:

            self.simulated_charging = False

            self._initialize_gpio()

    # ========================================================
    # RASPBERRY PI GPIO INITIALIZATION
    # ========================================================

    def _initialize_gpio(self) -> None:
        """
        Initialize the physical Raspberry Pi GPIO.
        """

        try:

            import RPi.GPIO as GPIO

        except ImportError as exc:

            raise RuntimeError(
                "RPi.GPIO is required when running "
                "on Raspberry Pi."
            ) from exc

        self.GPIO = GPIO

        self.GPIO.setmode(
            GPIO.BCM
        )

        self.GPIO.setup(
            self.charging_pin,
            GPIO.IN,
            pull_up_down=GPIO.PUD_DOWN,
        )

    # ========================================================
    # CHARGING STATUS
    # ========================================================

    def is_charging_active(self) -> bool:
        """
        Return whether charging is currently active.

        Windows/development:
            Uses SIMULATED_CHARGING.

        Raspberry Pi:
            Reads the physical GPIO switch.
        """

        if self.simulate:

            return self.simulated_charging

        if self.GPIO is None:

            raise RuntimeError(
                "GPIO has not been initialized."
            )

        return bool(
            self.GPIO.input(
                self.charging_pin
            )
        )

    # ========================================================
    # STATUS INFORMATION
    # ========================================================

    def get_charging_status(self) -> dict:
        """
        Return the charging state in a structured format.
        """

        active = (
            self.is_charging_active()
        )

        return {
            "charging_active": active,

            "status": (
                "CHARGING"
                if active
                else "NOT_CHARGING"
            ),
        }

    # ========================================================
    # CLEANUP
    # ========================================================

    def cleanup(self) -> None:
        """
        Release GPIO resources.
        """

        if self.GPIO is not None:

            self.GPIO.cleanup(
                self.charging_pin
            )