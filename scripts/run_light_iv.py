from toposcript.instruments.keithley_2450 import Keithley2450
from toposcript.experiments.light_iv import run_light_iv

RESOURCE = "TCPIP0::169.254.81.187::5025::SOCKET"

path = "data/light_iv"
scan_type = "LightIV"
sample_source = "SUNLAB"
sample_name = "TestSample"
user = "Aya"
notes = ""
lens_position = ""
filter_name = "None"

wavelength_list_nm = [1515,1525,1530,1550,1545,1570,1590]

start = -0.1
stop = 1.3
step = 0.02
current_limit = 0.02
nplc = 1

varied_step = True
mid = 0.5
step2 = 0.01


smu = Keithley2450(resource=RESOURCE).connect()

try:
    print(smu.identify())

    run_light_iv(
        smu=smu,
        path=path,
        scan_type=scan_type,
        sample_source=sample_source,
        sample_name=sample_name,
        user=user,
        notes=notes,
        wavelength_list_nm=wavelength_list_nm,
        lens_position=lens_position,
        filter_name=filter_name,
        start=start,
        stop=stop,
        step=step,
        current_limit=current_limit,
        nplc=nplc,
        varied_step=varied_step,
        mid=mid,
        step2=step2,
    )

    print("Sweep complete.")
    print("Keithley error check:", smu.get_error())

finally:
    smu.output_off()
    smu.close()