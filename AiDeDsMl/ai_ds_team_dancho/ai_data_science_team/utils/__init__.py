"""Utilities module for ai_data_science_team."""

from ai_data_science_team.utils.dataframe_compat import (
    describe,
    get_columns,
    get_dtypes,
    get_shape,
    head,
    is_dataframe,
    is_pandas,
    is_polars,
    sample,
    tail,
    to_pandas,
    to_polars,
)

__all__ = [
    "describe",
    "get_columns",
    "get_dtypes",
    "get_shape",
    "head",
    "is_dataframe",
    "is_pandas",
    "is_polars",
    "sample",
    "tail",
    "to_pandas",
    # DataFrame compatibility functions
    "to_polars",
]
