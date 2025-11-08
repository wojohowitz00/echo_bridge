"""DataFrame compatibility layer for pandas → polars migration.

This module provides utilities to work with both pandas and polars DataFrames
during the gradual migration from pandas to polars.

Usage:
    from ai_data_science_team.utils.dataframe_compat import to_polars, to_pandas

    # Accept any DataFrame, convert to polars
    df = to_polars(user_data)

    # Convert back to pandas if needed
    df_pandas = to_pandas(df)
"""

from typing import Any, Union

import polars as pl

try:
    import pandas as pd

    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False
    pd = None  # type: ignore


def to_polars(
    data: Union[
        pl.DataFrame, "pd.DataFrame", dict[str, list[Any]], list[dict[str, Any]], list[list[Any]]
    ],
) -> pl.DataFrame:
    """Convert input data to polars DataFrame.

    Args:
        data: Input data (polars DataFrame, pandas DataFrame, dict, or list)

    Returns:
        Polars DataFrame

    Raises:
        TypeError: If data type is not supported
        ValueError: If data is empty or invalid

    Examples:
        >>> import pandas as pd
        >>> import polars as pl
        >>> pdf = pd.DataFrame({"a": [1, 2, 3]})
        >>> plf = to_polars(pdf)
        >>> isinstance(plf, pl.DataFrame)
        True
    """
    # Already polars
    if isinstance(data, pl.DataFrame):
        return data

    # Convert from pandas
    if HAS_PANDAS and pd is not None and isinstance(data, pd.DataFrame):
        return pl.from_pandas(data)

    # Convert from dict
    if isinstance(data, dict):
        return pl.DataFrame(data)

    # Convert from list
    if isinstance(data, list):
        if len(data) == 0:
            raise TypeError("Cannot convert empty list to polars DataFrame")

        # List of dicts
        if isinstance(data[0], dict):
            return pl.DataFrame(data)

        # List of lists
        if isinstance(data[0], list):
            return pl.DataFrame(data)

        # Single list (assume single column)
        return pl.DataFrame({"column_0": data})

    raise TypeError(
        f"Cannot convert {type(data)} to polars DataFrame. "
        f"Supported types: pl.DataFrame, pd.DataFrame, dict, list"
    )


def to_pandas(data: Union[pl.DataFrame, "pd.DataFrame"]) -> "pd.DataFrame":
    """Convert polars DataFrame to pandas DataFrame.

    Args:
        data: Polars or pandas DataFrame

    Returns:
        Pandas DataFrame

    Raises:
        ImportError: If pandas is not installed
        TypeError: If data is not a DataFrame
    """
    if not HAS_PANDAS or pd is None:
        raise ImportError("pandas is required to convert to pandas DataFrame")

    # Already pandas
    if isinstance(data, pd.DataFrame):
        return data

    # Convert from polars
    if isinstance(data, pl.DataFrame):
        return data.to_pandas()

    raise TypeError(f"Cannot convert {type(data)} to pandas DataFrame")


def is_polars(data: Any) -> bool:
    """Check if data is a polars DataFrame.

    Args:
        data: Any data to check

    Returns:
        True if data is a polars DataFrame, False otherwise
    """
    return isinstance(data, pl.DataFrame)


def is_pandas(data: Any) -> bool:
    """Check if data is a pandas DataFrame.

    Args:
        data: Any data to check

    Returns:
        True if data is a pandas DataFrame, False otherwise
    """
    if not HAS_PANDAS or pd is None:
        return False
    return isinstance(data, pd.DataFrame)


def is_dataframe(data: Any) -> bool:
    """Check if data is any type of DataFrame (pandas or polars).

    Args:
        data: Any data to check

    Returns:
        True if data is a DataFrame (polars or pandas), False otherwise
    """
    return is_polars(data) or is_pandas(data)


def get_shape(data: Union[pl.DataFrame, "pd.DataFrame"]) -> tuple[int, int]:
    """Get shape (rows, cols) of DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame

    Returns:
        Tuple of (rows, columns)

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.shape
    elif is_pandas(data):
        return data.shape  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def get_columns(data: Union[pl.DataFrame, "pd.DataFrame"]) -> list[str]:
    """Get column names from DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame

    Returns:
        List of column names

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.columns
    elif is_pandas(data):
        return data.columns.tolist()  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def get_dtypes(data: Union[pl.DataFrame, "pd.DataFrame"]) -> dict[str, str]:
    """Get column types from DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame

    Returns:
        Dict mapping column names to type strings

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return {col: str(dtype) for col, dtype in zip(data.columns, data.dtypes)}
    elif is_pandas(data):
        return {col: str(dtype) for col, dtype in data.dtypes.items()}  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def sample(
    data: Union[pl.DataFrame, "pd.DataFrame"], n: int = 5
) -> Union[pl.DataFrame, "pd.DataFrame"]:
    """Get sample of DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame
        n: Number of rows to sample (default: 5)

    Returns:
        Sampled DataFrame (same type as input)

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.sample(n=min(n, len(data)))
    elif is_pandas(data):
        return data.sample(n=min(n, len(data)))  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def head(
    data: Union[pl.DataFrame, "pd.DataFrame"], n: int = 5
) -> Union[pl.DataFrame, "pd.DataFrame"]:
    """Get first n rows of DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame
        n: Number of rows to return (default: 5)

    Returns:
        First n rows of DataFrame (same type as input)

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.head(n)
    elif is_pandas(data):
        return data.head(n)  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def tail(
    data: Union[pl.DataFrame, "pd.DataFrame"], n: int = 5
) -> Union[pl.DataFrame, "pd.DataFrame"]:
    """Get last n rows of DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame
        n: Number of rows to return (default: 5)

    Returns:
        Last n rows of DataFrame (same type as input)

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.tail(n)
    elif is_pandas(data):
        return data.tail(n)  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")


def describe(data: Union[pl.DataFrame, "pd.DataFrame"]) -> Union[pl.DataFrame, "pd.DataFrame"]:
    """Get descriptive statistics of DataFrame (polars or pandas).

    Args:
        data: Polars or pandas DataFrame

    Returns:
        Descriptive statistics DataFrame (same type as input)

    Raises:
        TypeError: If data is not a DataFrame
    """
    if is_polars(data):
        return data.describe()
    elif is_pandas(data):
        return data.describe()  # type: ignore
    else:
        raise TypeError(f"Expected DataFrame, got {type(data)}")
