from toposcript.instruments.keithley_2450 import Keithley2450
from toposcript.experiments.dark_iv import run_dark_iv

RESOURCE = "TCPIP0::169.254.81.187::5025::SOCKET"

path = "data/dark_iv"
scan_type = "DarkIV_step"
sample_source = "SUNLAB"
sample_name = "TestSample"
user = "Aya"
notes = "No beam"

start = -3
stop = 1.4
step = 0.01

current_limit = 0.02
nplc = 1


smu = Keithley2450(resource=RESOURCE).connect()

try:
    print(smu.identify())

    run_dark_iv(
        smu=smu,
        path=path,
        scan_type=scan_type,
        sample_source=sample_source,
        sample_name=sample_name,
        user=user,
        notes=notes,
        start=start,
        stop=stop,
        step=step,
        current_limit=current_limit,
        nplc=nplc,
    )

    print("Dark IV complete.")
    print("Keithley error check:", smu.get_error())

finally:
    smu.output_off()
    smu.close()