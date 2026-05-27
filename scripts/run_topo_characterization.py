import os

from toposcript.experiments.topo_characterization import (
    create_run_folders,
    run_single_wavelength_measurement,
)


# =========================
# OMH / experiment settings
# Change these manually here
# =========================

DURATION_S = 60
INTERVAL_S = 1.0
SETTLE_S = 0

INITIALIZE_OMH = True
ZERO_FIRST = False

MIN_WAVELENGTH_NM = 1500
MAX_WAVELENGTH_NM = 1647
WARNING_WAVELENGTH_NM = 1640


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    run_id, raw_dir, processed_dir, figures_dir = create_run_folders(base_dir)

    print()
    print("Phase 1 TOPO characterization started.")
    print(f"Run ID: {run_id}")
    print(f"Raw folder: {raw_dir}")
    print(f"Processed folder: {processed_dir}")
    print()
    print("Type a target wavelength in nm, for example: 1550")
    print("Type DONE when you want to stop.")
    print()

    while True:
        wavelength_input = input(
            "Enter target wavelength in nm, or DONE to finish: "
        ).strip()

        if wavelength_input.upper() == "DONE":
            print()
            print("TOPO characterization finished.")
            print(f"Summary saved in: {processed_dir}")
            break

        try:
            target_wavelength_nm = float(wavelength_input)
        except ValueError:
            print("ERROR: Invalid input. Enter a wavelength like 1550 or type DONE.")
            continue

        if target_wavelength_nm < MIN_WAVELENGTH_NM:
            print(
                f"ERROR: {target_wavelength_nm} nm is below the allowed range. "
                f"Enter a wavelength between {MIN_WAVELENGTH_NM} and {MAX_WAVELENGTH_NM} nm."
            )
            continue

        if target_wavelength_nm > MAX_WAVELENGTH_NM:
            print(
                f"ERROR: {target_wavelength_nm} nm is too close to the OMH limit. "
                f"Enter a valid wavelength between {MIN_WAVELENGTH_NM} and {MAX_WAVELENGTH_NM} nm."
            )
            continue

        if target_wavelength_nm >= WARNING_WAVELENGTH_NM:
            print(
                f"CAUTION: {target_wavelength_nm} nm is close to the OMH wavelength limit "
                f"(1650 nm)."
            )

        print()
        print(f"Set the TOPO to {target_wavelength_nm} nm.")

        while True:
            confirm = input("Type READY when the TOPO is stable: ").strip()

            if confirm.upper() == "READY":
                break

            print("ERROR: Invalid input. Type READY when stable.")

        run_single_wavelength_measurement(
            run_id=run_id,
            raw_dir=raw_dir,
            processed_dir=processed_dir,
            target_wavelength_nm=target_wavelength_nm,
            duration_s=DURATION_S,
            interval_s=INTERVAL_S,
            settle_s=SETTLE_S,
            initialize=INITIALIZE_OMH,
            zero_first=ZERO_FIRST,
        )


if __name__ == "__main__":
    main()