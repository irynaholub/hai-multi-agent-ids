from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class AgentOutput:
    name: str
    flags: np.ndarray
    scores: np.ndarray
    variables: list[str]


class BaseAgent:
    def __init__(self, name: str, variables: list[str]):
        self.name = name
        self.variables = variables
        self.available_vars: list[str] = []

    def _select_available(self, df: pd.DataFrame) -> list[str]:
        return [v for v in self.variables if v in df.columns]

    def _select_data(self, df: pd.DataFrame) -> pd.DataFrame:
        available_now = self._select_available(df)

        if not self.available_vars:
            self.available_vars = available_now
        else:
            missing = set(self.available_vars) - set(df.columns)
            if missing:
                raise ValueError(
                    f"{self.name}: variables {sorted(missing)} were used at fit "
                    f"but are missing in this DataFrame"
                )

        if not self.available_vars:
            raise ValueError(f"{self.name}: no available variables in input data")

        return df[self.available_vars].copy()

    def fit(self, train: pd.DataFrame) -> "BaseAgent":
        raise NotImplementedError

    def predict(self, test: pd.DataFrame) -> AgentOutput:
        raise NotImplementedError
