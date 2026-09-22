"""
Voltage sensor interface.

Reads the analog output of the voltage sensor through MCP3008
and converts it into the measured AC voltage.

Important:
The voltage sensor module connected to the ADC must provide a
safe analog output within the MCP3008 input range.
"""


from backend.hardware.adc import MCP3008
from backend.config import VOLTAGE_CHANNEL


class VoltageSensor:
    """
    Interface for the voltage sensor connected to MCP3008.
    """

    def __init__(
        self,
        adc: MCP3008,
        channel: int = VOLTAGE_CHANNEL,
        sensor_ratio: float = 100.0,
    ):
        self.adc = adc
        self.channel = channel

        # Conversion factor between the sensor's ADC-side voltage
        # and the actual AC voltage being measured.
        #
        # This value MUST be calibrated according to the actual
        # voltage sensor module being used.
        self.sensor_ratio = sensor_ratio

    def read_adc_voltage(self) -> float:
        """
        Read the voltage appearing at the MCP3008 input.

        Returns
        -------
        float
            ADC-side voltage in volts.
        """

        return self.adc.read_voltage(self.channel)

    def read_voltage(self) -> float:
        """
        Read and calculate the actual AC voltage.

        Returns
        -------
        float
            Estimated AC voltage in volts.
        """

        adc_voltage = self.read_adc_voltage()

        actual_voltage = adc_voltage * self.sensor_ratio

        return actual_voltage

    def get_reading(self) -> dict:
        """
        Return both ADC-side and calculated voltage values.
        """

        adc_voltage = self.read_adc_voltage()
        actual_voltage = adc_voltage * self.sensor_ratio

        return {
            "adc_voltage": round(adc_voltage, 3),
            "voltage": round(actual_voltage, 2),
        }