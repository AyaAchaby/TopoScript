import time
import pyvisa


class Keithley2450:
    def __init__(self, resource="TCPIP0::169.254.81.187::inst0::INSTR"):
        self.resource = resource
        self.rm = None
        self.inst = None
        
    def connect(self):
        self.rm = pyvisa.ResourceManager()
        self.inst = self.rm.open_resource(self.resource)
        self.inst.timeout = 5000
        self.inst.write_termination = "\n"
        self.inst.read_termination = "\n"
        return self

    def close(self):
        if self.inst is not None:
            try:
                self.output_off()
            except Exception:
                pass
            self.inst.close()

    def write(self, command):
        self.inst.write(command)

    def query(self, command):
        return self.inst.query(command).strip()

    def identify(self):
        return self.query("*IDN?")

    def reset(self):
        self.write("*RST")
        time.sleep(1)

    def get_error(self):
        return self.query(":SYST:ERR?")

    def output_on(self):
        self.write(":OUTP ON")

    def output_off(self):
        self.write(":OUTP OFF")

    def set_voltage(self, voltage):
        self.write(f":SOUR:VOLT {voltage}")

    def configure_light_iv(self, source_voltage, current_limit, nplc):
        self.write(":OUTP OFF")
        self.write("*CLS")

        self.write('SENS:FUNC "CURR"')
        self.write("SENS:CURR:RANG:AUTO ON")
        self.write("SENS:CURR:RSEN ON")

        self.write("SOUR:FUNC VOLT")
        self.write("SOUR:VOLT:RANG 2")
        self.write(f"SOUR:VOLT:ILIM {current_limit}")
        self.write(f"SOUR:VOLT {source_voltage}")

        self.write(f"SENS:CURR:NPLC {nplc}")

    def read_voltage_current(self):
        data = self.query('READ? "defbuffer1", SOUR, READ')
        answer = data.split(",")

        voltage = float(answer[0])
        current = float(answer[1])

        return voltage, current