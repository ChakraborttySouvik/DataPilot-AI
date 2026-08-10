from __future__ import annotations

import uuid

import pandas as pd


_DATASETS: dict[str, pd.DataFrame] = {}


def save_dataset(dataframe: pd.DataFrame) -> str:
    """Store a dataset and return its ID."""

    dataset_id = str(uuid.uuid4())

    _DATASETS[dataset_id] = dataframe.copy()

    return dataset_id


def get_dataset(
    dataset_id: str,
) -> pd.DataFrame | None:
    """Retrieve a stored dataset."""

    dataframe = _DATASETS.get(dataset_id)

    if dataframe is None:
        return None

    return dataframe.copy()


def delete_dataset(
    dataset_id: str,
) -> bool:
    """Delete a stored dataset."""

    if dataset_id not in _DATASETS:
        return False

    del _DATASETS[dataset_id]

    return True