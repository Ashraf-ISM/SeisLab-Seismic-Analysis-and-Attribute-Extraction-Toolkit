from dataclasses import dataclass, field
from typing import Dict, Optional

import pandas as pd


@dataclass
class WellDataset:
    name: str
    filename: str
    df: pd.DataFrame
    depth_col: str
    curves: Dict[str, Dict[str, str]] = field(default_factory=dict)
    header: Dict[str, Dict[str, str]] = field(default_factory=dict)

    @property
    def curve_names(self):
        return [col for col in self.df.columns if col != self.depth_col]

    @property
    def depth_min(self) -> Optional[float]:
        if self.depth_col not in self.df:
            return None
        s = self.df[self.depth_col].dropna()
        return float(s.min()) if not s.empty else None

    @property
    def depth_max(self) -> Optional[float]:
        if self.depth_col not in self.df:
            return None
        s = self.df[self.depth_col].dropna()
        return float(s.max()) if not s.empty else None
