from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ProjectConfig:
    root: Path
    tools: tuple[str, ...] = ("c1", "c4", "c6")
    random_seed: int = 42
    bundle_csv: Path = field(default_factory=lambda: Path("data/external/phm2010_bundle_high_resolution.csv"))
    wear_dir: Path = field(default_factory=lambda: Path("data/raw/phm2010_wear"))
    default_threshold_um: float = 300.0
    sensitivity_thresholds_um: tuple[float, ...] = (150.0, 200.0, 250.0, 300.0)
    sensor_columns: tuple[str, ...] = (
        "force_x",
        "force_y",
        "force_z",
        "vibration_x",
        "vibration_y",
        "vibration_z",
        "acoustic_emission_rms",
    )
    results_dir: Path = field(default_factory=lambda: Path("results"))
    figures_dir: Path = field(default_factory=lambda: Path("results/figures"))
    tables_dir: Path = field(default_factory=lambda: Path("results/tables"))
    metrics_dir: Path = field(default_factory=lambda: Path("results/metrics"))

    def resolve(self, p: Path) -> Path:
        if p.is_absolute():
            return p
        return self.root / p


def load_config(root: Path, config_name: str = "default.yaml") -> ProjectConfig:
    path = root / "configs" / config_name
    raw: dict[str, Any] = {}
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}

    proj = raw.get("project", {})
    data = raw.get("data", {})
    wear = raw.get("wear", {})
    feats = raw.get("features", {})
    paths = raw.get("paths", {})

    cfg = ProjectConfig(
        root=root,
        tools=tuple(proj.get("tools", ("c1", "c4", "c6"))),
        random_seed=int(proj.get("random_seed", 42)),
        bundle_csv=Path(data.get("bundle_csv", "data/external/phm2010_bundle_high_resolution.csv")),
        wear_dir=Path(data.get("wear_dir", "data/raw/phm2010_wear")),
        default_threshold_um=float(wear.get("default_threshold_um", 300.0)),
        sensitivity_thresholds_um=tuple(wear.get("sensitivity_thresholds_um", (150, 200, 250, 300))),
        sensor_columns=tuple(
            feats.get(
                "sensor_columns",
                (
                    "force_x",
                    "force_y",
                    "force_z",
                    "vibration_x",
                    "vibration_y",
                    "vibration_z",
                    "acoustic_emission_rms",
                ),
            )
        ),
        results_dir=Path(paths.get("results_dir", "results")),
        figures_dir=Path(paths.get("figures_dir", "results/figures")),
        tables_dir=Path(paths.get("tables_dir", "results/tables")),
        metrics_dir=Path(paths.get("metrics_dir", "results/metrics")),
    )
    return cfg