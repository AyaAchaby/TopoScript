from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TopoConfig:
    host: str
    port: int = 5025


class TopoClient:
    """Minimal TOPO interface.

    The real IP command set should be added once the exact TOPO model/manual is known.
    """

    def __init__(self, config: TopoConfig) -> None:
        self.config = config

    def connect(self) -> None:
        raise NotImplementedError("Real TOPO IP commands are not implemented yet.")

    def check_ready(self) -> bool:
        raise NotImplementedError("Real TOPO status query is not implemented yet.")

    def set_wavelength_nm(self, wavelength_nm: float) -> None:
        raise NotImplementedError("Real TOPO wavelength command is not implemented yet.")

    def close(self) -> None:
        return None


class SimulatedTopoClient:
    def __init__(self) -> None:
        self.current_wavelength_nm: float | None = None

    def connect(self) -> None:
        return None

    def check_ready(self) -> bool:
        return True

    def set_wavelength_nm(self, wavelength_nm: float) -> None:
        self.current_wavelength_nm = wavelength_nm

    def close(self) -> None:
        return None
