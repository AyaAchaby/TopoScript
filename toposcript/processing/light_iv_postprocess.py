import re
from pathlib import Path
import matplotlib.pyplot as plt
import pandas as pd


def extract_wavelength_from_metadata(metadata):
    for key, value in metadata.items():
        key_clean = key.lower().strip()

        # Handles both correct and old typo:
        # "Laser Wavelength" and "Laser Wavelenth"
        if "laser" in key_clean and ("wavelength" in key_clean or "wavelenth" in key_clean):
            match = re.search(r"(\d+\.?\d*)", value)
            if match:
                return float(match.group(1))

    return None

def extract_light_iv_metrics(sciv_path, cell_area_cm2=0.054):
    metrics = {
        "Voc": None,
        "Isc": None,
        "Vmp": None,
        "Imp": None,
        "Pmax": None,
        "FF": None,
    }

    metadata = {}

    with open(sciv_path, "r", encoding="ISO-8859-1", errors="ignore") as f:
        for line in f:
            line = line.strip().lstrip("%").strip()

            if "\t" in line:
                parts = line.split("\t", 1)
                key = parts[0].strip()
                value = parts[1].strip()
                metadata[key] = value

            for key in metrics:
                if line.startswith(key):
                    parts = line.split("\t")
                    if len(parts) >= 2:
                        try:
                            metrics[key] = float(parts[1])
                        except ValueError:
                            pass

    wavelength_nm = extract_wavelength_from_metadata(metadata)

    if metrics["Voc"] is None or metrics["Isc"] is None:
        return None

    jsc = metrics["Isc"] / cell_area_cm2

    return {
        "File": sciv_path.name,
        "Wavelength_nm": wavelength_nm,
        "Voc": metrics["Voc"],
        "Isc": metrics["Isc"],
        "Jsc": jsc,
        "Vmp": metrics["Vmp"],
        "Imp": metrics["Imp"],
        "Pmax": metrics["Pmax"],
        "FF": metrics["FF"],
        "Path": str(sciv_path),
    }


def add_power_calibration(
    df,
    power_calibration_csv,
    power_wavelength_col="target_wavelength_nm",
    power_col="mean_power_mw",
    power_match_tolerance_nm=1.0,
    cell_area_cm2=0.054,
):
    power = pd.read_csv(power_calibration_csv)

    df["Wavelength_nm"] = pd.to_numeric(df["Wavelength_nm"], errors="coerce")
    power[power_wavelength_col] = pd.to_numeric(power[power_wavelength_col], errors="coerce")
    power[power_col] = pd.to_numeric(power[power_col], errors="coerce")

    df = df.sort_values("Wavelength_nm")
    power = power.dropna(subset=[power_wavelength_col, power_col]).sort_values(power_wavelength_col)

    merged = pd.merge_asof(
        df,
        power[[power_wavelength_col, power_col]],
        left_on="Wavelength_nm",
        right_on=power_wavelength_col,
        direction="nearest",
    )

    merged["Power_match_error_nm"] = (
        merged["Wavelength_nm"] - merged[power_wavelength_col]
    ).abs()

    bad = merged["Power_match_error_nm"] > power_match_tolerance_nm

    merged["mean_power_mw"] = merged[power_col]
    merged.loc[bad, "mean_power_mw"] = pd.NA

    merged["Pin_W"] = merged["mean_power_mw"] / 1000
    merged["Irradiance_W_cm2"] = merged["Pin_W"] / cell_area_cm2
    merged["Pmax_mW"] = merged["Pmax"] * 1000
    merged["Efficiency_percent"] = 100 * merged["Pmax"] / merged["Pin_W"]
    merged["Responsivity_A_W"] = merged["Isc"].abs() / merged["Pin_W"]

    return merged

def process_light_iv_run(
    input_folder,
    output_csv=None,
    cell_area_cm2=0.054,
    processed_folder=None,
    make_plots=True,
    use_power_calibration=False,
    power_calibration_csv=None,
    power_wavelength_col="target_wavelength_nm",
    power_col="mean_power_mw",
    power_match_tolerance_nm=1.0,
):
    input_folder = Path(input_folder)

    if not input_folder.exists():
        raise FileNotFoundError(f"Input folder not found: {input_folder}")

    results = []

    for sciv_path in sorted(input_folder.glob("*.sciv")):
        data = extract_light_iv_metrics(
            sciv_path=sciv_path,
            cell_area_cm2=cell_area_cm2,
        )

        if data is None:
            print(f"Skipped {sciv_path.name}: missing Voc or Isc")
            continue

        results.append(data)
        print(f"Extracted {sciv_path.name}")

    df = pd.DataFrame(results)

    if df.empty:
        raise RuntimeError("No data extracted. CSV not created.")

    df = df.sort_values("Wavelength_nm")

    if use_power_calibration and power_calibration_csv is not None:
        df = add_power_calibration(
            df=df,
            power_calibration_csv=power_calibration_csv,
            power_wavelength_col=power_wavelength_col,
            power_col=power_col,
            power_match_tolerance_nm=power_match_tolerance_nm,
            cell_area_cm2=cell_area_cm2,
        )

    if output_csv is not None:
        output_csv = Path(output_csv)
        output_csv.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_csv, index=False)
        print(f"Summary saved to: {output_csv}")

    if make_plots:
        if processed_folder is None:
            if output_csv is None:
                raise ValueError("processed_folder or output_csv must be provided if make_plots is True.")
            processed_folder = Path(output_csv).parent

        figures_folder = Path(processed_folder) / "figures"
        figures_folder.mkdir(parents=True, exist_ok=True)

        plot_iv_curves(
            input_folder=input_folder,
            output_path=figures_folder / "iv_curves.png",
            cell_area_cm2=cell_area_cm2,
        )
        plot_summary_metrics(
            df=df,
            figures_folder=figures_folder,
        )

    return df


def read_sciv_curve(sciv_path):
    metadata = {}
    voltage = []
    current = []

    with open(sciv_path, "r", encoding="ISO-8859-1", errors="ignore") as f:
        lines = f.readlines()

    data_started = False

    for line in lines:
        line = line.strip()

        if not line:
            continue

        clean =line.lstrip("%").strip()

        if "Voltage" in clean and "Current" in clean:
            data_started = True
            continue

        if not data_started:
            if "\t" in clean:
                key, value = clean.split("\t", 1)
                metadata[key.strip()] = value.strip()
            continue

        if data_started:
            parts = clean.split()
            if len(parts) >= 2:
                try:
                    voltage.append(float(parts[0]))
                    current.append(float(parts[1]))
                except ValueError:
                    pass
           

    return metadata, voltage, current


def plot_iv_curves(
    input_folder,
    output_path,
    cell_area_cm2=0.054,
    plot_current_density=True,
):
    input_folder = Path(input_folder)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    curves = []

    for sciv_path in sorted(input_folder.glob("*.sciv")):
        metadata, voltage, current = read_sciv_curve(sciv_path)

        if not voltage:
            print(f"Skipped plot for {sciv_path.name}: no IV data")
            continue

        wavelength = extract_wavelength_from_metadata(metadata)

        if wavelength is None:
            print(f"Skipped plot for {sciv_path.name}: no wavelength")
            continue

        if plot_current_density:
            y = [-i / cell_area_cm2 for i in current]
        else:
            y = [-i for i in current]

        curves.append(
            {
                "wavelength": wavelength,
                "voltage": voltage,
                "y": y,
            }
        )

    if not curves:
        print("No IV curves plotted.")
        return

    curves = sorted(curves, key=lambda x: x["wavelength"])

    plt.figure(figsize=(9, 6))

    for curve in curves:
        plt.plot(
            curve["voltage"],
            curve["y"],
            linewidth=1.5,
            marker="+",
            markersize=4,
            label=f"{curve['wavelength']:g} nm",
        )

    plt.xlabel("Voltage (V)")
    if plot_current_density:
        plt.ylabel("Current Density (A/cm²)")
    else:
        plt.ylabel("Current (A)")

    plt.title("Light IV Curves by Wavelength")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(title="Wavelength", fontsize=8)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved IV curve plot to: {output_path}")


def plot_xy(df, x_col, y_col, ylabel, title, output_path):
    if x_col not in df.columns or y_col not in df.columns:
        return

    plot_df = df[[x_col, y_col]].dropna()

    if plot_df.empty:
        return

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    plt.figure(figsize=(7, 5))
    plt.plot(plot_df[x_col], plot_df[y_col], marker="o", linewidth=1.5)
    plt.xlabel("Wavelength (nm)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"Saved plot to: {output_path}")


def plot_summary_metrics(df, figures_folder):
    figures_folder = Path(figures_folder)
    figures_folder.mkdir(parents=True, exist_ok=True)

    plot_df = df.copy()
    plot_df["Abs_Isc"] = plot_df["Isc"].abs()
    plot_df["Abs_Jsc"] = plot_df["Jsc"].abs()

    plot_xy(
        plot_df,
        "Wavelength_nm",
        "Abs_Isc",
        "|Isc| (A)",
        "Short-Circuit Current vs Wavelength",
        figures_folder / "isc_vs_wavelength.png",
    )

    plot_xy(
        plot_df,
        "Wavelength_nm",
        "Abs_Jsc",
        "|Jsc| (A/cm²)",
        "Short-Circuit Current Density vs Wavelength",
        figures_folder / "jsc_vs_wavelength.png",
    )

    plot_xy(
        plot_df,
        "Wavelength_nm",
        "Voc",
        "Voc (V)",
        "Open-Circuit Voltage vs Wavelength",
        figures_folder / "voc_vs_wavelength.png",
    )

    plot_xy(
        plot_df,
        "Wavelength_nm",
        "FF",
        "Fill Factor",
        "Fill Factor vs Wavelength",
        figures_folder / "ff_vs_wavelength.png",
    )

    plot_xy(
        plot_df,
        "Wavelength_nm",
        "Pmax_mW" if "Pmax_mW" in plot_df.columns else "Pmax",
        "Pmax (mW)" if "Pmax_mW" in plot_df.columns else "Pmax (W)",
        "Maximum Power vs Wavelength",
        figures_folder / "pmax_vs_wavelength.png",
    )

    if "mean_power_mw" in plot_df.columns:
        plot_xy(
            plot_df,
            "Wavelength_nm",
            "mean_power_mw",
            "Pin (mW)",
            "Input Power vs Wavelength",
            figures_folder / "pin_vs_wavelength.png",
        )

    if "Irradiance_W_cm2" in plot_df.columns:
        plot_xy(
            plot_df,
            "Wavelength_nm",
            "Irradiance_W_cm2",
            "Irradiance (W/cm²)",
            "Irradiance vs Wavelength",
            figures_folder / "irradiance_vs_wavelength.png",
        )

    if "Efficiency_percent" in plot_df.columns:
        plot_xy(
            plot_df,
            "Wavelength_nm",
            "Efficiency_percent",
            "Efficiency (%)",
            "Efficiency vs Wavelength",
            figures_folder / "efficiency_vs_wavelength.png",
        )

    if "Responsivity_A_W" in plot_df.columns:
        plot_xy(
            plot_df,
            "Wavelength_nm",
            "Responsivity_A_W",
            "Responsivity (A/W)",
            "Responsivity vs Wavelength",
            figures_folder / "responsivity_vs_wavelength.png",
        )