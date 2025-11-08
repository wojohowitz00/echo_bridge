"""Utility tools for polars DataFrame operations.

These tools provide common data manipulation operations optimized for polars.
"""

from typing import Any, Optional

import polars as pl


class PolarsTools:
    """Tools for working with polars DataFrames."""

    @staticmethod
    def detect_duplicates(df: pl.DataFrame, subset: Optional[list[str]] = None) -> pl.DataFrame:
        """Identify duplicate rows in DataFrame.

        Args:
            df: Polars DataFrame
            subset: Column names to check for duplicates (None = all columns)

        Returns:
            DataFrame with duplicate rows

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 1], "b": [4, 5, 4]})
            >>> dupes = PolarsTools.detect_duplicates(df)
            >>> len(dupes) > 0
            True
        """
        if subset is None:
            # Check all columns for duplicates
            return df.filter(pl.struct(df.columns).is_duplicated())
        else:
            # Check specific columns for duplicates
            return df.filter(pl.struct(subset).is_duplicated())

    @staticmethod
    def detect_nulls(df: pl.DataFrame) -> dict[str, int]:
        """Count null values per column.

        Args:
            df: Polars DataFrame

        Returns:
            Dict mapping column names to null counts

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
            >>> nulls = PolarsTools.detect_nulls(df)
            >>> nulls["a"]
            1
        """
        return {col: df[col].null_count() for col in df.columns}

    @staticmethod
    def drop_nulls(df: pl.DataFrame, subset: Optional[list[str]] = None) -> pl.DataFrame:
        """Remove rows with null values.

        Args:
            df: Polars DataFrame
            subset: Columns to check (None = all)

        Returns:
            DataFrame without null rows

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})
            >>> clean = PolarsTools.drop_nulls(df)
            >>> len(clean)
            2
        """
        return df.drop_nulls(subset=subset)

    @staticmethod
    def fill_nulls(
        df: pl.DataFrame, strategy: str = "mean", value: Optional[Any] = None
    ) -> pl.DataFrame:
        """Fill null values.

        Args:
            df: Polars DataFrame
            strategy: "mean", "median", "forward", "backward", or "value"
            value: Value to fill with (if strategy="value")

        Returns:
            DataFrame with nulls filled

        Raises:
            ValueError: If strategy is not recognized

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1.0, None, 3.0]})
            >>> filled = PolarsTools.fill_nulls(df, strategy="mean")
            >>> filled["a"][1]
            2.0
        """
        if strategy == "mean":
            # Fill numeric columns with mean
            return df.with_columns(
                [
                    pl.col(col).fill_null(pl.col(col).mean())
                    for col in df.columns
                    if df[col].dtype
                    in [pl.Float32, pl.Float64, pl.Int8, pl.Int16, pl.Int32, pl.Int64]
                ]
            )
        elif strategy == "median":
            # Fill numeric columns with median
            return df.with_columns(
                [
                    pl.col(col).fill_null(pl.col(col).median())
                    for col in df.columns
                    if df[col].dtype
                    in [pl.Float32, pl.Float64, pl.Int8, pl.Int16, pl.Int32, pl.Int64]
                ]
            )
        elif strategy == "forward":
            return df.fill_null(strategy="forward")
        elif strategy == "backward":
            return df.fill_null(strategy="backward")
        elif strategy == "value":
            if value is None:
                raise ValueError("Must provide value when strategy='value'")
            return df.fill_null(value)
        else:
            raise ValueError(
                f"Unknown strategy: {strategy}. "
                f"Valid options: 'mean', 'median', 'forward', 'backward', 'value'"
            )

    @staticmethod
    def get_summary(df: pl.DataFrame) -> pl.DataFrame:
        """Get descriptive statistics.

        Args:
            df: Polars DataFrame

        Returns:
            Summary statistics DataFrame

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
            >>> summary = PolarsTools.get_summary(df)
            >>> "count" in summary.columns or len(summary) > 0
            True
        """
        return df.describe()

    @staticmethod
    def get_dtypes(df: pl.DataFrame) -> dict[str, str]:
        """Get column data types.

        Args:
            df: Polars DataFrame

        Returns:
            Dict mapping column names to types

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
            >>> dtypes = PolarsTools.get_dtypes(df)
            >>> "Int64" in dtypes["a"] or "Int" in dtypes["a"]
            True
        """
        return {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)}

    @staticmethod
    def standardize_column_names(df: pl.DataFrame) -> pl.DataFrame:
        """Standardize column names (lowercase, replace spaces with underscores).

        Args:
            df: Polars DataFrame

        Returns:
            DataFrame with standardized column names

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"First Name": [1], "Last Name": [2]})
            >>> clean = PolarsTools.standardize_column_names(df)
            >>> clean.columns
            ['first_name', 'last_name']
        """
        return df.rename({col: col.lower().replace(" ", "_") for col in df.columns})

    @staticmethod
    def detect_outliers(
        df: pl.DataFrame, column: str, method: str = "iqr", threshold: float = 1.5
    ) -> pl.DataFrame:
        """Detect outliers in a numeric column.

        Args:
            df: Polars DataFrame
            column: Column name to check
            method: "iqr" (default) or "zscore"
            threshold: IQR multiplier or z-score threshold

        Returns:
            Rows identified as outliers

        Raises:
            ValueError: If method is not recognized

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 100]})
            >>> outliers = PolarsTools.detect_outliers(df, "value", method="iqr")
            >>> 100 in outliers["value"].to_list()
            True
        """
        if method == "iqr":
            q1 = df[column].quantile(0.25)
            q3 = df[column].quantile(0.75)
            iqr = q3 - q1
            lower = q1 - threshold * iqr
            upper = q3 + threshold * iqr
            return df.filter((pl.col(column) < lower) | (pl.col(column) > upper))
        elif method == "zscore":
            mean = df[column].mean()
            std = df[column].std()
            return df.filter((pl.col(column) - mean).abs() > threshold * std)
        else:
            raise ValueError(f"Unknown method: {method}. Valid options: 'iqr', 'zscore'")

    @staticmethod
    def remove_duplicates(df: pl.DataFrame, subset: Optional[list[str]] = None) -> pl.DataFrame:
        """Remove duplicate rows from DataFrame.

        Args:
            df: Polars DataFrame
            subset: Column names to check for duplicates (None = all columns)

        Returns:
            DataFrame without duplicate rows

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 1], "b": [4, 5, 4]})
            >>> unique = PolarsTools.remove_duplicates(df)
            >>> len(unique)
            2
        """
        return df.unique(subset=subset)

    @staticmethod
    def get_column_info(df: pl.DataFrame) -> pl.DataFrame:
        """Get detailed information about DataFrame columns.

        Args:
            df: Polars DataFrame

        Returns:
            DataFrame with column information (name, type, null_count, unique_count)

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
            >>> info = PolarsTools.get_column_info(df)
            >>> "column_name" in info.columns
            True
        """
        column_info = []
        for col in df.columns:
            column_info.append(
                {
                    "column_name": col,
                    "dtype": str(df[col].dtype),
                    "null_count": df[col].null_count(),
                    "unique_count": df[col].n_unique(),
                    "sample_value": df[col][0] if len(df) > 0 else None,
                }
            )
        return pl.DataFrame(column_info)

    @staticmethod
    def get_numeric_columns(df: pl.DataFrame) -> list[str]:
        """Get list of numeric column names.

        Args:
            df: Polars DataFrame

        Returns:
            List of numeric column names

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
            >>> numeric = PolarsTools.get_numeric_columns(df)
            >>> "a" in numeric
            True
        """
        numeric_types = [
            pl.Float32,
            pl.Float64,
            pl.Int8,
            pl.Int16,
            pl.Int32,
            pl.Int64,
            pl.UInt8,
            pl.UInt16,
            pl.UInt32,
            pl.UInt64,
        ]
        return [col for col in df.columns if df[col].dtype in numeric_types]

    @staticmethod
    def get_categorical_columns(df: pl.DataFrame) -> list[str]:
        """Get list of categorical/string column names.

        Args:
            df: Polars DataFrame

        Returns:
            List of categorical/string column names

        Examples:
            >>> import polars as pl
            >>> df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
            >>> categorical = PolarsTools.get_categorical_columns(df)
            >>> "b" in categorical
            True
        """
        categorical_types = [pl.Utf8, pl.Categorical]
        return [col for col in df.columns if df[col].dtype in categorical_types]
