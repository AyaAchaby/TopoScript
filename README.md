# TopoScript

TopoScript is a Python project for automating an optical measurement setup built around a TOPTICA TOPO tunable laser. It supports wavelength and optical power measurements, polarization-based power characterization, and currentâ€“voltage (IV) measurements of photonic power converters.

Developed at SUNLAB, University of Ottawa.

## Main functions

- Set TOPO wavelength points and record measured wavelength and power from the OMH optical meter.
- Measure optical power as a function of rotation angle to characterize polarization-based power control.
- Run dark and illuminated IV measurements using a Keithley 2450 source meter.
- Process IV data and extract parameters such as Isc, Voc, maximum power, and fill factor.
- Provide a graphical dashboard for operating the setup.
- Save measurement data locally for analysis.

## Project layout

| Folder | Contents |
| --- | --- |
| `toposcript/instruments/` | Instrument drivers and interfaces |
| `toposcript/experiments/` | Measurement routines and IV parameters |
| `toposcript/processing/` | Data processing and analysis |
| `toposcript/gui/` | Dashboard interface |
| `scripts/` | Scripts for launching measurements, the dashboard, and processing |
| `config/` | Configuration files |
| `data/` | Local measurement output; excluded from Git |

## Getting started

Use the Python environment configured for the lab setup. Run scripts from the project root.

Main entry points:

- `scripts/run_dashboard.py` â€” measurement dashboard.
- `scripts/run_light_iv.py` â€” illuminated IV measurements.
- `scripts/run_angle_vs_power.py` â€” angle-versus-power measurements.
- `scripts/process_light_iv_run.py` â€” processing of saved light-IV measurements.

Before running a measurement, check the instrument connections and addresses, sample information, wavelength range, voltage range, current limit, and output location in the relevant script or configuration. Follow the lab's laser operating procedures.

## Data

Measurement files are stored locally under `data/`. This folder is excluded by `.gitignore`, so committing and pushing the repository does **not** back up measurement data. Copy it separately to the lab's agreed storage location.