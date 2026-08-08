from __future__ import annotations

import re
from typing import Any

import pandas as pd


# ======================================================
# Helper Functions
# ======================================================

def find_column(
    dataframe: pd.DataFrame,
    column_name: str,
) -> str | None:
    """
    Find a dataframe column using case-insensitive matching.
    """

    column_name = column_name.strip().lower()

    for column in dataframe.columns:

        if str(column).lower() == column_name:
            return str(column)

    # Partial matching
    for column in dataframe.columns:

        if column_name in str(column).lower():
            return str(column)

    return None


def numeric_columns(
    dataframe: pd.DataFrame,
) -> list[str]:

    return dataframe.select_dtypes(
        include="number"
    ).columns.tolist()


# ======================================================
# Main Query Engine
# ======================================================

def execute_query(
    dataframe: pd.DataFrame,
    query: dict[str, Any],
) -> dict[str, Any]:
    """
    Execute a structured analytical query safely using Pandas.

    Supported operations:
    - count
    - average
    - sum
    - minimum
    - maximum
    - groupby
    - correlation
    - missing
    - unique
    - describe
    """

    operation = str(
        query.get("operation", "")
    ).lower().strip()

    column_name = query.get(
        "column"
    )

    group_column = query.get(
        "group_by"
    )

    # ==================================================
    # COUNT
    # ==================================================

    if operation == "count":

        filters = query.get(
            "filters",
            [],
        )

        filtered = dataframe.copy()

        for condition in filters:

            filter_column = find_column(
                dataframe,
                str(
                    condition.get("column", "")
                ),
            )

            if filter_column is None:
                continue

            value = condition.get(
                "value"
            )

            filtered = filtered[
                filtered[filter_column]
                .astype(str)
                .str.lower()
                == str(value).lower()
            ]

        return {
            "success": True,
            "operation": "count",
            "result": len(filtered),
            "details": (
                f"Found {len(filtered):,} matching row(s)."
            ),
        }

    # ==================================================
    # COLUMN VALIDATION
    # ==================================================

    if column_name:

        actual_column = find_column(
            dataframe,
            str(column_name),
        )

        if actual_column is None:

            return {
                "success": False,
                "error": (
                    f"Column '{column_name}' "
                    "does not exist."
                ),
            }

    else:

        actual_column = None

    # ==================================================
    # AVERAGE
    # ==================================================

    if operation in (
        "average",
        "mean",
    ):

        if actual_column is None:

            return {
                "success": False,
                "error": "No column specified.",
            }

        if not pd.api.types.is_numeric_dtype(
            dataframe[actual_column]
        ):

            return {
                "success": False,
                "error": (
                    f"'{actual_column}' "
                    "is not numeric."
                ),
            }

        value = dataframe[
            actual_column
        ].mean()

        return {
            "success": True,
            "operation": "average",
            "column": actual_column,
            "result": float(value),
        }

    # ==================================================
    # SUM
    # ==================================================

    if operation == "sum":

        if actual_column is None:

            return {
                "success": False,
                "error": "No column specified.",
            }

        if not pd.api.types.is_numeric_dtype(
            dataframe[actual_column]
        ):

            return {
                "success": False,
                "error": (
                    f"'{actual_column}' "
                    "is not numeric."
                ),
            }

        value = dataframe[
            actual_column
        ].sum()

        return {
            "success": True,
            "operation": "sum",
            "column": actual_column,
            "result": float(value),
        }

    # ==================================================
    # MAXIMUM
    # ==================================================

    if operation in (
        "maximum",
        "max",
        "highest",
    ):

        if actual_column is None:

            return {
                "success": False,
                "error": "No column specified.",
            }

        if not pd.api.types.is_numeric_dtype(
            dataframe[actual_column]
        ):

            return {
                "success": False,
                "error": (
                    f"'{actual_column}' "
                    "is not numeric."
                ),
            }

        index = dataframe[
            actual_column
        ].idxmax()

        value = dataframe.loc[
            index,
            actual_column,
        ]

        row = dataframe.loc[index]

        return {
            "success": True,
            "operation": "maximum",
            "column": actual_column,
            "result": float(value),
            "row": row.to_dict(),
        }

    # ==================================================
    # MINIMUM
    # ==================================================

    if operation in (
        "minimum",
        "min",
        "lowest",
    ):

        if actual_column is None:

            return {
                "success": False,
                "error": "No column specified.",
            }

        if not pd.api.types.is_numeric_dtype(
            dataframe[actual_column]
        ):

            return {
                "success": False,
                "error": (
                    f"'{actual_column}' "
                    "is not numeric."
                ),
            }

        index = dataframe[
            actual_column
        ].idxmin()

        value = dataframe.loc[
            index,
            actual_column,
        ]

        row = dataframe.loc[index]

        return {
            "success": True,
            "operation": "minimum",
            "column": actual_column,
            "result": float(value),
            "row": row.to_dict(),
        }

    # ==================================================
    # MISSING VALUES
    # ==================================================

    if operation == "missing":

        if actual_column:

            value = int(
                dataframe[
                    actual_column
                ].isna().sum()
            )

            return {
                "success": True,
                "operation": "missing",
                "column": actual_column,
                "result": value,
            }

        missing = (
            dataframe.isna()
            .sum()
            .sort_values(
                ascending=False
            )
        )

        missing = missing[
            missing > 0
        ]

        return {
            "success": True,
            "operation": "missing",
            "result": missing.to_dict(),
        }

    # ==================================================
    # UNIQUE VALUES
    # ==================================================

    if operation == "unique":

        if actual_column is None:

            return {
                "success": False,
                "error": "No column specified.",
            }

        value = int(
            dataframe[
                actual_column
            ].nunique()
        )

        return {
            "success": True,
            "operation": "unique",
            "column": actual_column,
            "result": value,
        }

    # ==================================================
    # CORRELATION
    # ==================================================

    if operation == "correlation":

        column_1 = find_column(
            dataframe,
            str(
                query.get(
                    "column_1",
                    "",
                )
            ),
        )

        column_2 = find_column(
            dataframe,
            str(
                query.get(
                    "column_2",
                    "",
                )
            ),
        )

        if not column_1 or not column_2:

            return {
                "success": False,
                "error": (
                    "Two numeric columns "
                    "are required."
                ),
            }

        if not (
            pd.api.types.is_numeric_dtype(
                dataframe[column_1]
            )
            and
            pd.api.types.is_numeric_dtype(
                dataframe[column_2]
            )
        ):

            return {
                "success": False,
                "error": (
                    "Both columns must be numeric."
                ),
            }

        value = dataframe[
            column_1
        ].corr(
            dataframe[column_2]
        )

        return {
            "success": True,
            "operation": "correlation",
            "columns": [
                column_1,
                column_2,
            ],
            "result": float(value),
        }

    # ==================================================
    # GROUP BY
    # ==================================================

    if operation == "groupby":

        if not group_column:

            return {
                "success": False,
                "error": (
                    "A group-by column "
                    "is required."
                ),
            }

        actual_group = find_column(
            dataframe,
            str(group_column),
        )

        if actual_group is None:

            return {
                "success": False,
                "error": (
                    f"Column '{group_column}' "
                    "does not exist."
                ),
            }

        aggregation = query.get(
            "aggregation",
            "count",
        )

        if aggregation == "count":

            result = (
                dataframe[
                    actual_group
                ]
                .value_counts()
                .head(20)
            )

            return {
                "success": True,
                "operation": "groupby",
                "group_by": actual_group,
                "result": result.to_dict(),
            }

        target_column = find_column(
            dataframe,
            str(
                query.get(
                    "column",
                    "",
                )
            ),
        )

        if target_column is None:

            return {
                "success": False,
                "error": (
                    "Target column "
                    "does not exist."
                ),
            }

        grouped = (
            dataframe
            .groupby(actual_group)[
                target_column
            ]
            .agg(aggregation)
            .sort_values(
                ascending=False
            )
            .head(20)
        )

        return {
            "success": True,
            "operation": "groupby",
            "group_by": actual_group,
            "column": target_column,
            "aggregation": aggregation,
            "result": grouped.to_dict(),
        }

    # ==================================================
    # DESCRIBE
    # ==================================================

    if operation == "describe":

        description = (
            dataframe.describe(
                include="all"
            )
            .transpose()
            .head(20)
        )

        return {
            "success": True,
            "operation": "describe",
            "result": description.to_dict(
                orient="index"
            ),
        }

    # ==================================================
    # Unsupported Operation
    # ==================================================

    return {
        "success": False,
        "error": (
            "I could not determine a supported "
            "analysis operation for this question."
        ),
    }