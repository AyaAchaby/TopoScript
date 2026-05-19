# TopoScript

TopoScript is a small measurement-automation project for an optical setup built around a TOPO wavelength source and an OMH optical meter.

The Phase 1 goal is intentionally simple:

- set TOPO wavelength points
- read measured wavelength and power from the OMH
- save timestamped sweep data to CSV
- keep instrument drivers separated so future devices can be added cleanly

## Phase 1 Workflow

```text
TOPO over IP -> set wavelength
OMH over GPIB -> read wavelength and power
TopoScript -> save setpoint, measured values, timestamp, and status
```

## Project Layout

```text
toposcript/
  instruments/
    topo.py        # TOPO interface and simulator
    omh.py         # OMH interface and simulator
  sweep.py         # sweep logic
scripts/
  wavelength_sweep.py
config/
  example_sweep.toml
data/
  .gitkeep
```

## Quick Dry Run

The first version can run without instruments using simulated readings:

```powershell
python scripts/wavelength_sweep.py --config config/example_sweep.toml --simulate
```

The output CSV will be written under `data/`.

## Future Modules

Later phases can add:

- optical power control
- multimeter IV sweeps
- temperature controller/probe logging
- sample metadata
- GUI or web dashboard
