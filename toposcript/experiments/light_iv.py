import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from toposcript.experiments.iv_params import calculate_light_iv_params
from toposcript.experiments import iv_params
from toposcript.processing.light_iv_postprocess import process_light_iv_run


# ============================================================
# LIGHT IV
# ============================================================

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
    measurement_callback=None,
    wait_callback=None,
    show_plots=True,
):

    times_run = 1

    run_id = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    run_folder = (
        Path(path)
        / "raw"
        / f"{run_id}_{sample_name}"
    )

    run_folder.mkdir(
        parents=True,
        exist_ok=True
    )

    legend_time_list = []
    legend_wavelength_list = []

    list_dic = {}

    source_voltage = start


    # ========================================================
    # CONFIGURE KEITHLEY
    # ========================================================

    smu.reset()

    time.sleep(1)

    smu.configure_light_iv(
        source_voltage=source_voltage,
        current_limit=current_limit,
        nplc=nplc,
    )

    print(
        "Keithley error check:",
        smu.get_error()
    )


    # ========================================================
    # DETERMINE SWEEP DIRECTION
    # ========================================================

    if start < stop:

        direction = "Forward"

    elif stop < start:

        direction = "Reverse"

    else:

        raise ValueError(
            "Start and Stop cannot be equal."
        )


    # ========================================================
    # LOOP THROUGH WAVELENGTHS
    # ========================================================

    for i in range(
        len(wavelength_list_nm)
    ):

        wavelength_nm = (
            wavelength_list_nm[i]
        )


        set_voltage = []
        measured_voltage = []
        measured_current = []
        elapsed_time = []


        # ====================================================
        # WAIT FOR USER TO SET WAVELENGTH
        # ====================================================

        print(
            f"\nSet TOPO wavelength to "
            f"{wavelength_nm} nm."
        )


        message = (
            f"Set TOPO wavelength to "
            f"{wavelength_nm} nm, "
            f"then click CONTINUE."
        )


        if wait_callback is not None:

            wait_callback(
                message
            )

        else:

            input(
                "Press Enter when the laser "
                "is ready to run this IV sweep..."
            )


        # ====================================================
        # PREPARE SWEEP
        # ====================================================

        source_voltage = start

        smu.set_voltage(
            source_voltage
        )

        time.sleep(
            0.2
        )

        smu.output_on()

        start_time = time.time()


        # ====================================================
        # FORWARD SWEEP
        # ====================================================

        if direction == "Forward":

            # ------------------------------------------------
            # VARIED STEP
            # ------------------------------------------------

            if varied_step:

                # ============================================
                # REGION 1
                # start -> mid using step
                # ============================================

                while source_voltage <= mid:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage += step

                    smu.set_voltage(
                        source_voltage
                    )


                # ============================================
                # REGION 2
                # mid -> stop using step2
                # ============================================

                while source_voltage <= stop:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage += step2

                    smu.set_voltage(
                        source_voltage
                    )


            # ------------------------------------------------
            # CONSTANT STEP
            # ------------------------------------------------

            else:

                while source_voltage <= stop:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage += step

                    smu.set_voltage(
                        source_voltage
                    )


        # ====================================================
        # REVERSE SWEEP
        # ====================================================

        if direction == "Reverse":

            # ------------------------------------------------
            # VARIED STEP
            # ------------------------------------------------

            if varied_step:

                # ============================================
                # REGION 1
                # start -> mid using step
                # ============================================

                while source_voltage >= mid:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage -= step

                    smu.set_voltage(
                        source_voltage
                    )


                # ============================================
                # REGION 2
                # mid -> stop using step2
                # ============================================

                while source_voltage >= stop:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage -= step2

                    smu.set_voltage(
                        source_voltage
                    )


            # ------------------------------------------------
            # CONSTANT STEP
            # ------------------------------------------------

            else:

                while source_voltage >= stop:

                    v_read, i_read = (
                        smu.read_voltage_current()
                    )


                    # ----------------------------------------
                    # DASHBOARD CALLBACK
                    # ----------------------------------------

                    if measurement_callback is not None:

                        measurement_callback(
                            v_read,
                            i_read,
                        )


                    set_voltage.append(
                        source_voltage
                    )

                    measured_voltage.append(
                        v_read
                    )

                    measured_current.append(
                        i_read
                    )

                    elapsed_time.append(
                        time.time()
                        - start_time
                    )


                    print(
                        f"Set {source_voltage:.4f} V | "
                        f"Read {v_read:.4f} V | "
                        f"I = {i_read:.6e} A"
                    )


                    source_voltage -= step

                    smu.set_voltage(
                        source_voltage
                    )


        # ====================================================
        # SWEEP COMPLETE
        # ====================================================

        smu.output_off()


        stop_time = time.time()

        duration = (
            stop_time
            - start_time
        )


        # ====================================================
        # CALCULATE IV PARAMETERS
        # ====================================================

        params = calculate_light_iv_params(
            measured_voltage,
            measured_current,
        )


        print(
            "\nIV parameters:"
        )


        for key, value in params.items():

            print(
                f"{key}: {value}"
            )


        # ====================================================
        # STORE RUN
        # ====================================================

        list_dic[
            f"set_volt_{times_run}"
        ] = set_voltage


        list_dic[
            f"volt_{times_run}"
        ] = measured_voltage


        list_dic[
            f"curr_{times_run}"
        ] = measured_current


        current_time = (
            datetime.now().strftime(
                "%H:%M:%S"
            )
        )


        legend_time_list.append(
            current_time
        )


        legend_wavelength_list.append(
            str(
                wavelength_nm
            )
        )


        # ====================================================
        # PLOT
        # ====================================================

        if show_plots:

            plt.figure()

            for x in range(
                times_run
            ):

                plt.plot(
                    list_dic[
                        f"volt_{x + 1}"
                    ],
                    list_dic[
                        f"curr_{x + 1}"
                    ],
                    linewidth=1,
                    marker="+",
                    label=(
                        legend_wavelength_list[x]
                        + " nm, "
                        + legend_time_list[x]
                    ),
                )

            plt.xlabel(
                "Voltage (V)"
            )

            plt.ylabel(
                "Current (A)"
            )

            plt.legend().set_draggable(
                True
            )

            plt.show()





        # ====================================================
        # SAVE SCIV FILE
        # ====================================================

        save_light_iv_sciv(
            path=run_folder,
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


        # ====================================================
        # WAIT BEFORE NEXT WAVELENGTH
        # ====================================================

        print(
            "Measurement complete."
        )


        if i < (
            len(wavelength_list_nm)
            - 1
        ):

            next_wavelength = (
                wavelength_list_nm[
                    i + 1
                ]
            )


            message = (
                f"Measurement at "
                f"{wavelength_nm} nm complete. "
                f"Prepare {next_wavelength} nm, "
                f"then click CONTINUE."
            )


            if wait_callback is not None:

                wait_callback(
                    message
                )

            else:

                input(
                    "Press Enter to continue "
                    "to the next wavelength..."
                )


        # ====================================================
        # PREPARE NEXT RUN
        # ====================================================

        times_run += 1

        source_voltage = start

        smu.set_voltage(
            source_voltage
        )


    # ========================================================
    # POST PROCESSING
    # ========================================================

    processed_folder = (
        Path(path)
        / "processed"
        / f"{run_id}_{sample_name}"
    )


    processed_folder.mkdir(
        parents=True,
        exist_ok=True
    )


    summary_csv = (
        processed_folder
        / "light_iv_summary.csv"
    )


    if iv_params.PROCESS_AFTER_RUN:

        process_light_iv_run(
            input_folder=run_folder,
            output_csv=summary_csv,
            processed_folder=processed_folder,
            cell_area_cm2=iv_params.CELL_AREA_CM2,
            make_plots=iv_params.MAKE_PLOTS_AFTER_RUN,
            use_power_calibration=iv_params.USE_POWER_CALIBRATION,
            power_calibration_csv=iv_params.POWER_CALIBRATION_CSV,
            power_wavelength_col=iv_params.POWER_WAVELENGTH_COL,
            power_col=iv_params.POWER_COL,
            power_match_tolerance_nm=iv_params.POWER_MATCH_TOLERANCE_NM,
        )


    return list_dic


# ============================================================
# SAVE LIGHT IV SCIV
# ============================================================

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

    output_folder = Path(
        path
    )

    output_folder.mkdir(
        parents=True,
        exist_ok=True
    )


    timestamp = (
        datetime.now().strftime(
            "%Y-%m-%d_%H%M%S"
        )
    )


    filename = (
        output_folder
        / (
            f"{timestamp}_"
            f"{sample_name}_"
            f"{scan_type}_"
            f"{wavelength_nm}_"
            f"{filter_name}.sciv"
        )
    )


    with open(
        filename,
        "w",
        encoding="ISO-8859-1",
        newline=""
    ) as f:

        f.write(
            "%SUNLAB Data from OptiInstrument\t \n"
        )

        f.write(
            "%\t\n"
        )


        f.write(
            f"Date\t"
            f"{datetime.now().strftime('%Y-%m-%d')}\n"
        )

        f.write(
            f"Time\t"
            f"{datetime.now().strftime('%H:%M:%S')}\n"
        )

        f.write(
            f"Scan Type\t"
            f"{scan_type}\n"
        )

        f.write(
            f"Sample Source\t"
            f"{sample_source}\n"
        )

        f.write(
            f"Sample Name\t"
            f"{sample_name}\n"
        )

        f.write(
            f"User\t"
            f"{user}\n"
        )

        f.write(
            f"Laser Wavelength\t"
            f"{wavelength_nm} nm\n"
        )


        if laser_current is not None:

            f.write(
                f"Laser Current(A)\t"
                f"{laser_current}\n"
            )


        f.write(
            f"Filter\t"
            f"{filter_name}\n"
        )

        f.write(
            f"Lens Position\t"
            f"{lens_position}\n"
        )

        f.write(
            f"Duration (s)\t"
            f"{duration}\n"
        )

        f.write(
            f"Notes\t"
            f"{notes}\n"
        )


        f.write(
            "%\t\n"
        )


        f.write(
            f"Isc (A)\t"
            f"{params['Isc_A']}\n"
        )

        f.write(
            f"Voc (V)\t"
            f"{params['Voc_V']}\n"
        )

        f.write(
            f"Pmax (W)\t"
            f"{params['Pmax_W']}\n"
        )

        f.write(
            f"Imp (A)\t"
            f"{params['Imp_A']}\n"
        )

        f.write(
            f"Vmp (V)\t"
            f"{params['Vmp_V']}\n"
        )

        f.write(
            f"FF\t"
            f"{params['FF']}\n"
        )


        f.write(
            "%\t\n"
        )


        f.write(
            "Voltage (V)\tCurrent (A)\n"
        )


        for v, i in zip(
            measured_voltage,
            measured_current
        ):

            f.write(
                f"{v}\t{i}\n"
            )


    print(
        f"Saved data to: {filename}"
    )