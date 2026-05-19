from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class OmhConfig:
    resource: str


@dataclass(frozen=True)
class OmhReading:
    wavelength_nm: float
    power_w: float

    @property
    def power_dbm(self) -> float:
        if self.power_w <= 0:
            return float("-inf")
        return 10.0 * math.log10(self.power_w / 0.001)


class OmhClient:
    """Minimal OMH interface.

    The real GPIB command set should be added once the exact OMH model/manual is known.
    """

    def __init__(self, config: OmhConfig) -> None:
        self.config = config

    def connect(self) -> None:
        raise NotImplementedError("Real OMH GPIB commands are not implemented yet.")

    def read(self) -> OmhReading:
        raise NotImplementedError("Real OMH read command is not implemented yet.")

    def close(self) -> None:
        return None


class SimulatedOmhClient:
    def __init__(self, topo: object) -> None:
        self._topo = topo

    def connect(self) -> None:
        return None

    def read(self) -> OmhReading:
        setpoint = getattr(self._topo, "current_wavelength_nm", None)
        wavelength_nm = 1500.0 if setpoint is None else float(setpoint)
        measured_wavelength = wavelength_nm + random.uniform(-0.03, 0.03)
        measured_power = 1.2e-3 * (1.0 + random.uniform(-0.04, 0.04))
        return OmhReading(wavelength_nm=measured_wavelength, power_w=measured_power)

    def close(self) -> None:
        return None
