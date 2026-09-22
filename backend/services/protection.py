"""
Vehicle-aware protection logic.

Protection is triggered only when:

1. Charging is active
2. An electrical anomaly is detected
3. A vehicle/object is present

This module currently provides a software protection state.
It does not physically disconnect the charging supply because
no relay/contactor is currently installed.
"""

from __future__ import annotations

from typing import Any, Dict


class ProtectionService:
    """
    Determines whether the charging system should enter
    a protection state.
    """

    def __init__(
        self,
        require_vehicle: bool = True,
    ):
        self.require_vehicle = require_vehicle

    def evaluate(
        self,
        charging_active: bool,
        is_anomaly: bool,
        vehicle_present: bool,
    ) -> Dict[str, Any]:
        """
        Evaluate the protection conditions.

        Parameters
        ----------
        charging_active:
            Whether charging is currently active.

        is_anomaly:
            Whether the ML model detected abnormal
            electrical behavior.

        vehicle_present:
            Whether HC-SR04 detected a vehicle/object.

        Returns
        -------
        dict
            Protection decision and explanation.
        """

        # ----------------------------------------------------
        # CHARGING IS NOT ACTIVE
        # ----------------------------------------------------

        if not charging_active:
            return {
                "protection_triggered": False,
                "status": "SAFE",
                "reason": "CHARGING_INACTIVE",
            }

        # ----------------------------------------------------
        # CHARGING ACTIVE BUT NO ANOMALY
        # ----------------------------------------------------

        if not is_anomaly:
            return {
                "protection_triggered": False,
                "status": "SAFE",
                "reason": "NO_ANOMALY",
            }

        # ----------------------------------------------------
        # ANOMALY DETECTED
        # ----------------------------------------------------

        if self.require_vehicle and not vehicle_present:
            return {
                "protection_triggered": False,
                "status": "WARNING",
                "reason": "ANOMALY_WITHOUT_VEHICLE",
            }

        # ----------------------------------------------------
        # ALL PROTECTION CONDITIONS SATISFIED
        # ----------------------------------------------------

        return {
            "protection_triggered": True,
            "status": "PROTECTION_TRIGGERED",
            "reason": "ANOMALY_DURING_ACTIVE_CHARGING_WITH_VEHICLE",
        }