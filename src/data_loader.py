from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass
class LoadedData:
    train_raw: pd.DataFrame
    test_raw: pd.DataFrame
    train: pd.DataFrame
    test: pd.DataFrame
    labels: np.ndarray
    available_vars: list[str]
    missing_vars: list[str]


def _clean_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(c).strip() for c in df.columns]
    return df


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return _clean_columns(pd.read_csv(path))


def _prepare_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    out = df[columns].copy()
    out = out.apply(pd.to_numeric, errors="coerce")
    out = out.replace([np.inf, -np.inf], np.nan)
    out = out.ffill().bfill().fillna(0)
    return out


def _extract_labels(labels_df: pd.DataFrame, n: int) -> np.ndarray:
    if "label" in labels_df.columns:
        y = labels_df["label"].values
    else:
        y = labels_df.iloc[:, -1].values

    y = pd.to_numeric(pd.Series(y), errors="coerce").fillna(0).astype(int).values

    if len(y) < n:
        raise ValueError(
            f"Label file is shorter than test data: labels={len(y)}, test={n}"
        )

    return y[:n]


def _as_path_list(files) -> list[Path]:
    """Turn a single path or a list of paths into a list of Path objects"""
    if files is None:
        return []

    if isinstance(files, (str, Path)):
        return [Path(files)]

    return [Path(f) for f in files]


def load_hai_data(
    train_file,
    test_file,
    label_file,
    selected_vars: Iterable[str],
) -> LoadedData:
    """Load HAI train/test data and test labels (one path or a list for each)"""
    train_files = _as_path_list(train_file)
    test_files = _as_path_list(test_file)
    label_files = _as_path_list(label_file)

    if not train_files:
        raise ValueError("At least one train file must be provided")
    if not test_files:
        raise ValueError("At least one test file must be provided")
    if not label_files:
        raise ValueError("At least one label file must be provided")

    if len(test_files) != len(label_files):
        raise ValueError(
            f"Number of test files ({len(test_files)}) must match "
            f"number of label files ({len(label_files)})."
        )

    selected_vars = list(dict.fromkeys(selected_vars))

    train_raw = pd.concat(
        [_read_csv(f) for f in train_files], axis=0, ignore_index=True
    )

    test_parts = []
    label_parts = []

    for test_path, label_path in zip(test_files, label_files):
        test_part = _read_csv(test_path)
        label_part = _read_csv(label_path)

        test_parts.append(test_part)
        label_parts.append(_extract_labels(label_part, len(test_part)))

    test_raw = pd.concat(test_parts, axis=0, ignore_index=True)
    labels = np.concatenate(label_parts, axis=0).astype(int)

    available_vars = [
        v for v in selected_vars
        if v in train_raw.columns and v in test_raw.columns
    ]
    missing_vars = [
        v for v in selected_vars
        if v not in train_raw.columns or v not in test_raw.columns
    ]

    if not available_vars:
        raise ValueError(
            "None of the selected variables are available in both train and test files"
        )

    train = _prepare_numeric(train_raw, available_vars)
    test = _prepare_numeric(test_raw, available_vars)

    return LoadedData(
        train_raw=train_raw,
        test_raw=test_raw,
        train=train,
        test=test,
        labels=labels,
        available_vars=available_vars,
        missing_vars=missing_vars,
    )
