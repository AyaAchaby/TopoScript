import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def run_dark_iv(
    smu,
    path,
    scan_type,
    sample_source,
    sample_name,
    user,
    notes,
    start,
    stop,
    step,
    current_limit,
    nplc,
):
    smu.reset()
    time.sleep(1)

    smu.configure_light_iv(
        source_voltage=0.0,
        current_limit=current_limit,
        nplc=nplc,
    )

    print("Keithley error check:", smu.get_error())

    voltage = []
    current = []
    abs_current = []

    smu.output_on()

    try:
        # Sweep from 0 to stop
        v = 0.0
        while v <= stop:
            smu.set_voltage(v)
            time.sleep(0.05)

            v_read, i_read = smu.read_voltage_current()

            voltage.append(v_read)
            current.append(i_read)
            abs_current.append(abs(i_read))

            print(f"{v_read:.4f} V | I = {i_read:.6e} A")

            v += step

        # Sweep from stop down to start
        v = stop
        while v >= start:
            smu.set_voltage(v)
            time.sleep(0.05)

            v_read, i_read = smu.read_voltage_current()

            voltage.append(v_read)
            current.append(i_read)
            abs_current.append(abs(i_read))

            print(f"{v_read:.4f} V | I = {i_read:.6e} A")

            v -= step

        # Sweep from start back to 0
        v = start
        while v <= 0:
            smu.set_voltage(v)
            time.sleep(0.05)

            v_read, i_read = smu.read_voltage_current()

            voltage.append(v_read)
            current.append(i_read)
            abs_current.append(abs(i_read))

            print(f"{v_read:.4f} V | I = {i_read:.6e} A")

            v += step

    finally:
        smu.output_off()

    plt.semilogy(voltage, abs_current, linewidth=1, marker="+")
    plt.xlabel("Voltage (V)")
    plt.ylabel("Current (A)")
    plt.show()

    save_dark_iv_sciv(
        path=path,
        scan_type=scan_type,
        sample_source=sample_source,
        sample_name=sample_name,
        user=user,
        notes=notes,
        voltage=voltage,
        current=abs_current,
    )


def save_dark_iv_sciv(
    path,
    scan_type,
    sample_source,
    sample_name,
    user,
    notes,
    voltage,
    current,
):
    output_folder = Path(path)
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    filename = output_folder / f"{timestamp}_{sample_name}_{scan_type}.sciv"

    df = pd.DataFrame(
        {
            "Voltage (V)": voltage,
            "Current (A)": current,
        }
    )

    with open(filename, "w", encoding="ISO-8859-1", newline="") as f:
        f.write("%SUNLAB Data from TopoScript\n")
        f.write("%\n")
        f.write(f"Date\t{datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Time\t{datetime.now().strftime('%H:%M:%S')}\n")
        f.write(f"Scan Type\t{scan_type}\n")
        f.write(f"Sample Source\t{sample_source}\n")
        f.write(f"Sample Name\t{sample_name}\n")
        f.write(f"User\t{user}\n")
        f.write(f"Notes\t{notes}\n")
        f.write("%\n")

        df.to_csv(f, sep="\t", index=False)

    print(f"Saved data to: {filename}")