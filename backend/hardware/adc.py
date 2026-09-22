"""
MCP3008 ADC interface.

Provides a common interface for reading analog values from
the MCP3008.

Raspberry Pi:
    Uses SPI through spidev.

Windows/development:
    Uses configurable simulated ADC voltages.

Environment variables for simulation:

    SIMULATED_ADC_CH0_VOLTAGE
    SIMULATED_ADC_CH1_VOLTAGE

Example:

    $env:SIMULATED_ADC_CH0_VOLTAGE="2.3"
    $env:SIMULATED_ADC_CH1_VOLTAGE="2.5"
"""

from __future__ import annotations

import os
import platform
from typing import Optional

from backend.config import SPI_BUS, SPI_DEVICE


class MCP3008:
    """
    Interface for the MCP3008 8-channel ADC.
    """

    REFERENCE_VOLTAGE = 3.3
    MAX_ADC_VALUE = 1023

    def __init__(
        self,
        bus: int = SPI_BUS,
        device: int = SPI_DEVICE,
        simulate: Optional[bool] = None,
    ):
        self.bus = bus
        self.device = device
        self.spi = None

        # Automatically select simulation mode on
        # non-Raspberry-Pi development systems.
        if simulate is None:
            simulate = platform.system() != "Linux"

        self.simulate = simulate

        if not self.simulate:
            self._initialize_spi()

    # ========================================================
    # SPI INITIALIZATION
    # ========================================================

    def _initialize_spi(self) -> None:
        """
        Initialize SPI communication with MCP3008.
        """

        try:
            import spidev

        except ImportError as exc:

            raise RuntimeError(
                "spidev is required when running on "
                "Raspberry Pi. Install it using: "
                "pip install spidev"
            ) from exc

        self.spi = spidev.SpiDev()

        self.spi.open(
            self.bus,
            self.device,
        )

        self.spi.max_speed_hz = 1350000
        self.spi.mode = 0

    # ========================================================
    # SIMULATION
    # ========================================================

    def _get_simulated_voltage(
        self,
        channel: int,
    ) -> float:
        """
        Get a simulated ADC input voltage.

        Channel 0:
            Voltage sensor

        Channel 1:
            ACS712 current sensor
        """

        default_values = {
            0: 2.3,
            1: 2.5,
        }

        environment_names = {
            0: "SIMULATED_ADC_CH0_VOLTAGE",
            1: "SIMULATED_ADC_CH1_VOLTAGE",
        }

        environment_name = environment_names[channel]

        raw_value = os.getenv(
            environment_name
        )

        if raw_value is None:
            voltage = default_values[channel]

        else:

            try:
                voltage = float(raw_value)

            except ValueError as exc:

                raise ValueError(
                    f"Invalid simulated ADC voltage "
                    f"for channel {channel}: {raw_value}"
                ) from exc

        # MCP3008 input must remain within
        # the ADC reference range.
        if not 0.0 <= voltage <= self.REFERENCE_VOLTAGE:

            raise ValueError(
                f"Simulated ADC voltage for channel "
                f"{channel} must be between 0 and "
                f"{self.REFERENCE_VOLTAGE} V."
            )

        return voltage

    # ========================================================
    # ADC READING
    # ========================================================

    def read_channel(
        self,
        channel: int,
    ) -> int:
        """
        Read a raw 10-bit ADC value.

        Parameters
        ----------
        channel : int
            MCP3008 channel from 0 to 7.

        Returns
        -------
        int
            ADC value between 0 and 1023.
        """

        if not 0 <= channel <= 7:

            raise ValueError(
                f"Invalid MCP3008 channel: {channel}. "
                "Channel must be between 0 and 7."
            )

        # ----------------------------------------------------
        # Windows / development simulation
        # ----------------------------------------------------

        if self.simulate:

            simulated_voltage = (
                self._get_simulated_voltage(
                    channel
                )
            )

            simulated_raw = round(
                (
                    simulated_voltage
                    / self.REFERENCE_VOLTAGE
                )
                * self.MAX_ADC_VALUE
            )

            return simulated_raw

        # ----------------------------------------------------
        # Raspberry Pi SPI
        # ----------------------------------------------------

        if self.spi is None:

            raise RuntimeError(
                "SPI interface has not been initialized."
            )

        adc = self.spi.xfer2(
            [
                1,
                (8 + channel) << 4,
                0,
            ]
        )

        value = (
            ((adc[1] & 3) << 8)
            | adc[2]
        )

        return value

    # ========================================================
    # ADC VOLTAGE
    # ========================================================

    def read_voltage(
        self,
        channel: int,
    ) -> float:
        """
        Convert the raw ADC reading into voltage.
        """

        raw_value = self.read_channel(
            channel
        )

        voltage = (
            raw_value
            / self.MAX_ADC_VALUE
        ) * self.REFERENCE_VOLTAGE

        return round(
            voltage,
            4,
        )

    # ========================================================
    # CLEANUP
    # ========================================================

    def close(self) -> None:
        """
        Close the SPI connection.
        """

        if self.spi is not None:

            self.spi.close()
            self.spi = None

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        self.close()