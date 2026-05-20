import time
import pyvisa


class OMM6810B:
    def __init__(self, resource_name="GPIB0::2::INSTR", timeout_ms=10000):
        self.resource_name = resource_name
        self.timeout_ms = timeout_ms
        self.rm = None
        self.inst = None

    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(self.resource_name)

        self.inst.timeout = self.timeout_ms
        self.inst.write_termination = "\n"
        self.inst.read_termination = "\n"

        return self

    def close(self):
        if self.inst is not None:
            self.inst.close()
        if self.rm is not None:
            self.rm.close()

    def write(self, command: str):
        self.inst.write(command)

    def query(self, command: str) -> str:
        return self.inst.query(command).strip()

    def initialize(self):
        self.write("*CLS")
        self.enable_power_autorange()
        self.enable_wavelength_auto()

    def identify_instrument(self) -> str:
        return self.query("*IDN?")

    def identify_head(self) -> str:
        return self.query("HEAD:IDN?")

    def enable_power_autorange(self):
        self.write("RANGE:AUTO ON")

    def disable_power_autorange(self):
        self.write("RANGE:AUTO OFF")

    def enable_wavelength_auto(self):
        self.write("WAVE:AUTO ON")

    def disable_wavelength_auto(self):
        self.write("WAVE:AUTO OFF")

    def get_power_w(self) -> float:
        return float(self.query("POWER?"))

    def get_wavelength_nm(self) -> float:
        return float(self.query("WAVE?"))

    def zero(self, wait=True, poll_interval_s=1.0, timeout_s=30):
        self.write("ZERO")

        if not wait:
            return

        start = time.time()

        while True:
            if self.is_zero_done():
                return

            if time.time() - start > timeout_s:
                raise TimeoutError("OMM zeroing did not finish within timeout.")

            time.sleep(poll_interval_s)

    def is_zero_done(self) -> bool:
        return self.query("ZERO?") == "1"

    def read_measurement(self) -> dict:
        return {
            "power_w": self.get_power_w(),
            "wavelength_nm": self.get_wavelength_nm(),
        }