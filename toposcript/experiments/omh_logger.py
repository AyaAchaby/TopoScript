import csv
import time
from datetime import datetime


def log_omh_measurements(
    omm,
    output_csv,
    duration_s=60,
    interval_s=1.0,
    initialize=True,
    zero_first=False,
):
    if initialize:
        omm.initialize()

    if zero_first:
        input("Block the beam at the source, then press Enter to zero...")
        omm.zero(wait=True)

    start_time = time.time()

    with open(output_csv, "w", newline="") as file:
        writer = csv.writer(file)

        writer.writerow([
            "timestamp",
            "elapsed_s",
            "power_w",
            "power_mw",
            "wavelength_nm",
        ])

        while time.time() - start_time <= duration_s:
            elapsed_s = time.time() - start_time

            measurement = omm.read_measurement()
            power_w = measurement["power_w"]
            wavelength_nm = measurement["wavelength_nm"]

            writer.writerow([
                datetime.now().isoformat(timespec="seconds"),
                round(elapsed_s, 3),
                power_w,
                power_w * 1000,
                wavelength_nm,
            ])

            file.flush()

            print(
                f"{elapsed_s:.1f}s | "
                f"P = {power_w * 1000:.3f} mW | "
                f"λ = {wavelength_nm:.2f} nm"
            )

            time.sleep(interval_s)