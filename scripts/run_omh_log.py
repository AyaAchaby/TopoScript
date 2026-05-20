import os
from datetime import datetime

from toposcript.instruments.omh import OMM6810B
from toposcript.experiments.omh_logger import log_omh_measurements


os.makedirs("data/omh_logs", exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_csv = f"data/omh_logs/omh_log_{timestamp}.csv"

omm = OMM6810B().connect()

try:
    print(omm.identify_instrument())
    print(omm.identify_head())

    log_omh_measurements(
        omm=omm,
        output_csv=output_csv,
        duration_s=120,
        interval_s=1.0,
        initialize=True,
        zero_first=False,
    )

finally:
    omm.close()

print(f"Saved data to: {output_csv}")