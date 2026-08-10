from __future__ import annotations

import requests


API_BASE_URL = "http://127.0.0.1:8000"

def get_dataset_overview(dataset_id: str) -> dict:
    """Get dataset overview from FastAPI."""

    response = requests.post(
        f"{API_BASE_URL}/api/analysis/overview",
        json={
            "dataset_id": dataset_id,
        },
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


def upload_dataset(file) -> dict:
    """Upload a dataset to the FastAPI backend."""

    response = requests.post(
        f"{API_BASE_URL}/api/dataset/upload",
        files={
            "file": (
                file.name,
                file.getvalue(),
                file.type,
            )
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


def get_analysis(dataset_id: str) -> dict:
    """Get dataset overview from FastAPI."""

    response = requests.post(
        f"{API_BASE_URL}/api/analysis/overview",
        json={
            "dataset_id": dataset_id,
        },
        timeout=60,
    )

    response.raise_for_status()

    return response.json()


def get_forecast(
    dataset_id: str,
    date_column: str,
    target_column: str,
    periods: int,
    method: str,
) -> dict:
    """Generate a forecast through FastAPI."""

    response = requests.post(
        f"{API_BASE_URL}/api/forecast",
        json={
            "dataset_id": dataset_id,
            "date_column": date_column,
            "target_column": target_column,
            "periods": periods,
            "method": method,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()


def ask_ai(
    dataset_id: str,
    question: str,
) -> dict:
    """Ask Gemini through FastAPI."""

    response = requests.post(
        f"{API_BASE_URL}/api/ai/chat",
        json={
            "dataset_id": dataset_id,
            "question": question,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()