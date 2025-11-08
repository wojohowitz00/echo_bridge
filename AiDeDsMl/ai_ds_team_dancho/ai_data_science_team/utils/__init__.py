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
from ai_data_science_team.utils.duckdb_manager import DuckDBManager
from ai_data_science_team.utils.marimo_generator import (
    MarimoCell,
    MarimoNotebook,
    NotebookBuilder,
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
    # Database management
    "DuckDBManager",
    # Notebook generation
    "MarimoCell",
    "MarimoNotebook",
    "NotebookBuilder",
]
