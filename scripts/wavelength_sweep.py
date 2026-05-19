from __future__ import annotations

import argparse
import sys
import tomllib
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from toposcript.instruments.omh import OmhClient, OmhConfig, SimulatedOmhClient
from toposcript.instruments.topo import SimulatedTopoClient, TopoClient, TopoConfig
from toposcript.sweep import SweepConfig, run_wavelength_sweep


def load_config(path: Path) -> tuple[TopoConfig, OmhConfig, SweepConfig]:
    with path.open("rb") as config_file:
        data = tomllib.load(config_file)

    topo_config = TopoConfig(
        host=data["topo"]["host"],
        port=int(data["topo"].get("port", 5025)),
    )
    omh_config = OmhConfig(resource=data["omh"]["resource"])
    sweep_config = SweepConfig(
        start_wavelength_nm=float(data["sweep"]["start_wavelength_nm"]),
        end_wavelength_nm=float(data["sweep"]["end_wavelength_nm"]),
        step_nm=float(data["sweep"]["step_nm"]),
        settling_time_s=float(data["sweep"]["settling_time_s"]),
        readings_per_point=int(data["sweep"]["readings_per_point"]),
        output_dir=Path(data["sweep"].get("output_dir", "data")),
    )
    return topo_config, omh_config, sweep_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a TOPO/OMH wavelength sweep.")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/example_sweep.toml"),
        help="Path to sweep configuration TOML file.",
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Use simulated TOPO and OMH instruments.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    topo_config, omh_config, sweep_config = load_config(args.config)

    if args.simulate:
        topo = SimulatedTopoClient()
        omh = SimulatedOmhClient(topo)
    else:
        topo = TopoClient(topo_config)
        omh = OmhClient(omh_config)

    output_path = run_wavelength_sweep(topo, omh, sweep_config)
    print(f"Wrote sweep data to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
