import os
import time
from datetime import datetime

import pandas as pd

from toposcript.instruments.omh import OMM6810B
from toposcript.experiments.omh_logger import log_omh_measurements


def create_run_folders(base_dir):
    run_id = datetime.now().strftime("run_%Y%m%d_%H%M%S")

    raw_dir = os.path.join(
        base_dir, "data", "raw", "phase1_topo_characterization", run_id
    )

    processed_dir = os.path.join(
        base_dir, "data", "processed", "phase1_topo_characterization", run_id
    )

    figures_dir = os.path.join(
        base_dir, "data", "figures", "phase1_topo_characterization", run_id
    )

    os.makedirs(raw_dir, exist_ok=True)
    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(figures_dir, exist_ok=True)

    return run_id, raw_dir, processed_dir, figures_dir


def summarize_omh_file(
    raw_csv,
    run_id,
    target_wavelength_nm,
    duration_s,
    interval_s,
    notes="",
):
    df = pd.read_csv(raw_csv)

    power_col = "power_mw"

    mean_power_mw = df[power_col].mean()
    std_power_mw = df[power_col].std()
    min_power_mw = df[power_col].min()
    max_power_mw = df[power_col].max()

    stability_percent = (
        std_power_mw / mean_power_mw * 100
        if mean_power_mw != 0
        else None
    )

    return {
        "run_id": run_id,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "target_wavelength_nm": target_wavelength_nm,
        "omh_mean_wavelength_nm": df["wavelength_nm"].mean(),
        "duration_s": duration_s,
        "interval_s": interval_s,
        "n_samples": len(df),
        "mean_power_mw": mean_power_mw,
        "std_power_mw": std_power_mw,
        "min_power_mw": min_power_mw,
        "max_power_mw": max_power_mw,
        "stability_percent": stability_percent,
        "raw_file": raw_csv,
        "notes": notes,
    }


def update_summary(processed_dir, summary_row):
    summary_csv = os.path.join(processed_dir, "summary.csv")
    summary_xlsx = os.path.join(processed_dir, "summary.xlsx")

    new_row = pd.DataFrame([summary_row])

    if os.path.exists(summary_csv):
        old = pd.read_csv(summary_csv)
        summary = pd.concat([old, new_row], ignore_index=True)
    else:
        summary = new_row

    summary.to_csv(summary_csv, index=False)
    summary.to_excel(summary_xlsx, index=False)

    return summary_csv, summary_xlsx


def run_single_wavelength_measurement(
    run_id,
    raw_dir,
    processed_dir,
    target_wavelength_nm,
    duration_s,
    interval_s,
    settle_s,
    initialize=True,
    zero_first=False,
    notes="",
):
    target_label = str(target_wavelength_nm).replace(".", "p")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    raw_csv = os.path.join(
        raw_dir,
        f"{target_label}nm_raw_{timestamp}.csv"
    )

    print()
    print(f"Target wavelength: {target_wavelength_nm} nm")
    print(f"Waiting {settle_s} s before recording...")
    time.sleep(settle_s)

    omm = OMM6810B().connect()

    try:
        print(omm.identify_instrument())
        print(omm.identify_head())

        log_omh_measurements(
            omm=omm,
            output_csv=raw_csv,
            duration_s=duration_s,
            interval_s=interval_s,
            initialize=initialize,
            zero_first=zero_first,
        )

    finally:
        omm.close()

    summary_row = summarize_omh_file(
        raw_csv=raw_csv,
        run_id=run_id,
        target_wavelength_nm=target_wavelength_nm,
        duration_s=duration_s,
        interval_s=interval_s,
        notes=notes,
    )

    summary_csv, summary_xlsx = update_summary(processed_dir, summary_row)

    print()
    print(f"Saved raw data to: {raw_csv}")
    print(f"Updated summary CSV: {summary_csv}")
    print(f"Updated summary Excel: {summary_xlsx}")