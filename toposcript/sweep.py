from __future__ import annotations

import csv
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean

from toposcript.instruments.omh import OmhReading


@dataclass(frozen=True)
class SweepConfig:
    start_wavelength_nm: float
    end_wavelength_nm: float
    step_nm: float
    settling_time_s: float
    readings_per_point: int
    output_dir: Path


def wavelength_points(start_nm: float, end_nm: float, step_nm: float) -> list[float]:
    if step_nm <= 0:
        raise ValueError("step_nm must be greater than zero")
    if end_nm < start_nm:
        raise ValueError("end wavelength must be greater than or equal to start wavelength")

    points: list[float] = []
    current = start_nm
    while current <= end_nm + (step_nm / 1000.0):
        points.append(round(current, 9))
        current += step_nm
    return points


def average_readings(readings: list[OmhReading]) -> OmhReading:
    if not readings:
        raise ValueError("at least one OMH reading is required")
    return OmhReading(
        wavelength_nm=mean(reading.wavelength_nm for reading in readings),
        power_w=mean(reading.power_w for reading in readings),
    )


def run_wavelength_sweep(topo: object, omh: object, config: SweepConfig) -> Path:
    config.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_path = config.output_dir / f"topo_omh_sweep_{stamp}.csv"

    topo.connect()
    omh.connect()

    if not topo.check_ready():
        raise RuntimeError("TOPO did not report a ready state")

    fieldnames = [
        "timestamp_utc",
        "set_wavelength_nm",
        "omh_wavelength_nm",
        "omh_power_w",
        "omh_power_dbm",
        "readings_per_point",
        "status",
    ]

    try:
        with output_path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
            writer.writeheader()

            for wavelength_nm in wavelength_points(
                config.start_wavelength_nm,
                config.end_wavelength_nm,
                config.step_nm,
            ):
                topo.set_wavelength_nm(wavelength_nm)
                time.sleep(config.settling_time_s)

                readings = [omh.read() for _ in range(config.readings_per_point)]
                reading = average_readings(readings)

                writer.writerow(
                    {
                        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                        "set_wavelength_nm": wavelength_nm,
                        "omh_wavelength_nm": reading.wavelength_nm,
                        "omh_power_w": reading.power_w,
                        "omh_power_dbm": reading.power_dbm,
                        "readings_per_point": config.readings_per_point,
                        "status": "ok",
                    }
                )
    finally:
        omh.close()
        topo.close()

    return output_path
