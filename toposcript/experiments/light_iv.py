import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from toposcript.experiments.iv_params import calculate_light_iv_params


def run_light_iv(
    smu,
    path,
    scan_type,
    sample_source,
    sample_name,
    user,
    notes,
    wavelength_list_nm,
    lens_position,
    filter_name,
    start,
    stop,
    step,
    current_limit,
    nplc,
    varied_step,
    mid,
    step2,
):
    times_run = 1
    legend_time_list = []
    legend_wavelength_list = []
    list_dic = {}

    source_voltage = start

    smu.reset()
    time.sleep(1)

    smu.configure_light_iv(
        source_voltage=source_voltage,
        current_limit=current_limit,
        nplc=nplc,
    )

    print("Keithley error check:", smu.get_error())

    if start < stop:
        direction = "Forward"
    elif stop < start:
        direction = "Reverse"
    else:
        raise ValueError("Start and Stop cannot be equal.")

    for i in range(len(wavelength_list_nm)):
        wavelength_nm = wavelength_list_nm[i]

        set_voltage = []
        measured_voltage = []
        measured_current = []
        elapsed_time = []

        print(f"\nSet TOPO wavelength to {wavelength_nm} nm.")
        input("Press Enter when the laser is ready to run this IV sweep...")

        source_voltage = start
        smu.set_voltage(source_voltage)
        time.sleep(0.2)

        smu.output_on()
        start_time = time.time()

        if direction == "Forward":
            if varied_step:
                while source_voltage <= mid:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage += step
                    smu.set_voltage(source_voltage)

                while source_voltage <= stop:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage += step2
                    smu.set_voltage(source_voltage)

            else:
                while source_voltage <= stop:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage += step
                    smu.set_voltage(source_voltage)

        if direction == "Reverse":
            if varied_step:
                while source_voltage >= mid:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage -= step
                    smu.set_voltage(source_voltage)

                while source_voltage >= stop:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage -= step2
                    smu.set_voltage(source_voltage)

            else:
                while source_voltage >= stop:
                    v_read, i_read = smu.read_voltage_current()

                    set_voltage.append(source_voltage)
                    measured_voltage.append(v_read)
                    measured_current.append(i_read)
                    elapsed_time.append(time.time() - start_time)

                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )

                    source_voltage -= step
                    smu.set_voltage(source_voltage)

        smu.output_off()

        stop_time = time.time()
        duration = stop_time - start_time

        params = calculate_light_iv_params(
            measured_voltage,
            measured_current,
        )

        print("\nIV parameters:")
        for key, value in params.items():
            print(f"{key}: {value}")

        list_dic[f"set_volt_{times_run}"] = set_voltage
        list_dic[f"volt_{times_run}"] = measured_voltage
        list_dic[f"curr_{times_run}"] = measured_current

        current_time = datetime.now().strftime("%H:%M:%S")

        legend_time_list.append(current_time)
        legend_wavelength_list.append(str(wavelength_nm))

        for x in range(times_run):
            plt.plot(
                list_dic[f"volt_{x + 1}"],
                list_dic[f"curr_{x + 1}"],
                linewidth=1,
                marker="+",
                label=legend_wavelength_list[x] + " nm, " + legend_time_list[x],
            )

        plt.xlabel("Voltage (V)")
        plt.ylabel("Current (A)")
        plt.legend().set_draggable(True)
        plt.show()

        save_light_iv_sciv(
            path=path,
            scan_type=scan_type,
            sample_source=sample_source,
            sample_name=sample_name,
            user=user,
            notes=notes,
            wavelength_nm=wavelength_nm,
            lens_position=lens_position,
            filter_name=filter_name,
            duration=duration,
            set_voltage=set_voltage,
            measured_voltage=measured_voltage,
            measured_current=measured_current,
            elapsed_time=elapsed_time,
            params=params,
        )

        print("Measurement complete, press Enter to continue to the next wavelength.")
        input(" ")

        times_run += 1
        source_voltage = start
        smu.set_voltage(source_voltage)

    return list_dic

def save_light_iv_sciv(
    path,
    scan_type,
    sample_source,
    sample_name,
    user,
    notes,
    wavelength_nm,
    lens_position,
    filter_name,
    duration,
    set_voltage,
    measured_voltage,
    measured_current,
    elapsed_time,
    params,
    laser_current=None,
):
    output_folder = Path(path)
    output_folder.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    filename = (
        output_folder
        / f"{timestamp}_{sample_name}_{scan_type}_{wavelength_nm}_{filter_name}.sciv"
    )

    with open(filename, "w", encoding="ISO-8859-1", newline="") as f:
        f.write("%SUNLAB Data from OptiInstrument\t \n")
        f.write("%\t\n")

        f.write(f"Date\t{datetime.now().strftime('%Y-%m-%d')}\n")
        f.write(f"Time\t{datetime.now().strftime('%H:%M:%S')}\n")
        f.write(f"Scan Type\t{scan_type}\n")
        f.write(f"Sample Source\t{sample_source}\n")
        f.write(f"Sample Name\t{sample_name}\n")
        f.write(f"User\t{user}\n")
        f.write(f"Laser Wavelenth\t{wavelength_nm} nm\n")  #typo

        if laser_current is not None:
            f.write(f"Laser Current(A)\t{laser_current}\n")

        f.write(f"Filter\t{filter_name}\n")
        f.write(f"Lens Position\t{lens_position}\n")
        f.write(f"Duration (s)\t{duration}\n")
        f.write(f"Notes\t{notes}\n")

        f.write("%\t\n")
        f.write(f"Isc (A)\t{params['Isc_A']}\n")
        f.write(f"Voc (V)\t{params['Voc_V']}\n")
        f.write(f"Pmax (I)\t{params['Pmax_W']}\n")  # old file says Pmax (I)
        f.write(f"Imp (A)\t{params['Imp_A']}\n")
        f.write(f"Vmp (V)\t{params['Vmp_V']}\n")
        f.write(f"FF\t{params['FF']}\n")

        f.write("%\t\n")
        f.write("Voltage (V)\tCurrent (A)\n")

        for v, i in zip(measured_voltage, measured_current):
            f.write(f"{v}\t{i}\n")

    print(f"Saved data to: {filename}")