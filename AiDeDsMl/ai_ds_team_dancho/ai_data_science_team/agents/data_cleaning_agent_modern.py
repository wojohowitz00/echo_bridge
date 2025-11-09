"""Modern Data Cleaning Agent using polars and marimo.

This module provides a data cleaning agent that:
- Uses polars for efficient data processing
- Extends BaseAgentModern for marimo integration
- Provides automatic null/outlier/duplicate detection
- Generates interactive analysis notebooks
- Integrates with DuckDB for persistence
"""

import logging
from typing import Any, Dict, List, Optional, Union

import polars as pl

from ai_data_science_team.agents.base_agent_modern import BaseAgentModern
from ai_data_science_team.utils import DuckDBManager, to_polars


logger = logging.getLogger(__name__)


class DataCleaningAgentModern(BaseAgentModern):
    """Modern data cleaning agent using polars and marimo.

    Performs comprehensive data cleaning including:
    - Null value detection and handling
    - Outlier detection and removal
    - Duplicate row detection
    - Data type inference and conversion
    - Missing value strategies (drop, fill, interpolate)

    Example:
        >>> agent = DataCleaningAgentModern("DataCleaner")
        >>> df = pl.DataFrame({"x": [1, 2, None, 4], "y": [10, 20, 30, 40]})
        >>> results = agent.run(df)
        >>> print(results["notebook_path"])
    """

    def __init__(
        self,
        name: str = "DataCleaningAgent",
        description: str = "Advanced data cleaning with polars",
        db_path: str = ":memory:",
        null_threshold: float = 0.5,
        outlier_method: str = "iqr",
        remove_duplicates: bool = True,
    ) -> None:
        """Initialize data cleaning agent.

        Args:
            name: Agent name
            description: Agent description
            db_path: DuckDB database path
            null_threshold: Proportion threshold for removing columns (0.0-1.0)
            outlier_method: Method for outlier detection ("iqr" or "zscore")
            remove_duplicates: Whether to remove duplicate rows
        """
        super().__init__(name, description, db_path)
        self.null_threshold = null_threshold
        self.outlier_method = outlier_method
        self.remove_duplicates = remove_duplicates
        self.config = {
            "null_threshold": null_threshold,
            "outlier_method": outlier_method,
            "remove_duplicates": remove_duplicates,
        }

    def execute(self, data: Any) -> Dict[str, Any]:
        """Execute data cleaning workflow.

        Args:
            data: Input data (DataFrame, dict, or other formats)

        Returns:
            Dictionary containing:
            - cleaned_data: Cleaned polars DataFrame
            - null_report: Null value statistics
            - outliers_removed: Count of outlier rows removed
            - duplicates_removed: Count of duplicate rows removed
        """
        # Convert to polars
        df = to_polars(data)
        original_shape = df.shape

        logger.info(f"Starting data cleaning: shape={original_shape}")

        # Step 1: Detect nulls
        null_report = self._analyze_nulls(df)

        # Step 2: Remove high-null columns
        df = self._remove_high_null_columns(df, null_report)

        # Step 3: Remove outliers
        outliers_removed, df = self._remove_outliers(df)

        # Step 4: Remove duplicates
        duplicates_removed = 0
        if self.remove_duplicates:
            duplicates_removed, df = self._remove_duplicates(df)

        # Step 5: Handle remaining nulls
        df = self._handle_remaining_nulls(df)

        # Persist original and cleaned data
        self.persist_to_duckdb("original_data", to_polars(data))
        self.persist_to_duckdb("cleaned_data", df)

        logger.info(
            f"Cleaning complete: "
            f"original={original_shape}, "
            f"cleaned={df.shape}, "
            f"outliers_removed={outliers_removed}, "
            f"duplicates_removed={duplicates_removed}"
        )

        return {
            "cleaned_data": df,
            "original_shape": original_shape,
            "cleaned_shape": df.shape,
            "null_report": null_report,
            "outliers_removed": outliers_removed,
            "duplicates_removed": duplicates_removed,
        }

    def _analyze_nulls(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Analyze null values in DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with null statistics
        """
        null_counts = df.null_count()

        # Handle empty DataFrames
        if df.height == 0:
            null_proportions = {col: 0.0 for col in df.columns}
        else:
            null_proportions = {
                col: null_counts[col][0] / df.height
                for col in df.columns
            }

        return {
            "null_counts": dict(null_counts.row(0, named=True)) if df.height > 0 else {},
            "null_proportions": null_proportions,
            "columns_exceeding_threshold": [
                col for col, prop in null_proportions.items()
                if prop > self.null_threshold
            ],
        }

    def _remove_high_null_columns(
        self,
        df: pl.DataFrame,
        null_report: Dict[str, Any],
    ) -> pl.DataFrame:
        """Remove columns with excessive nulls.

        Args:
            df: Input DataFrame
            null_report: Output from _analyze_nulls()

        Returns:
            DataFrame with high-null columns removed
        """
        cols_to_drop = null_report["columns_exceeding_threshold"]

        if cols_to_drop:
            logger.info(f"Removing high-null columns: {cols_to_drop}")
            df = df.drop(cols_to_drop)

        return df

    def _remove_outliers(
        self,
        df: pl.DataFrame,
    ) -> tuple[int, pl.DataFrame]:
        """Remove outlier rows based on numeric columns.

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (outliers_removed, cleaned_df)
        """
        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Float64]
        ]

        if not numeric_cols:
            return 0, df

        rows_before = df.height

        if self.outlier_method == "iqr":
            df = self._remove_outliers_iqr(df, numeric_cols)
        elif self.outlier_method == "zscore":
            df = self._remove_outliers_zscore(df, numeric_cols)

        outliers_removed = rows_before - df.height
        logger.info(f"Outliers removed: {outliers_removed}")

        return outliers_removed, df

    def _remove_outliers_iqr(
        self,
        df: pl.DataFrame,
        numeric_cols: List[str],
    ) -> pl.DataFrame:
        """Remove outliers using IQR method.

        Args:
            df: Input DataFrame
            numeric_cols: Columns to check for outliers

        Returns:
            DataFrame with outliers removed
        """
        for col in numeric_cols:
            q1 = df[col].quantile(0.25)
            q3 = df[col].quantile(0.75)
            iqr = q3 - q1

            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr

            df = df.filter(
                (pl.col(col) >= lower_bound) & (pl.col(col) <= upper_bound)
            )

        return df

    def _remove_outliers_zscore(
        self,
        df: pl.DataFrame,
        numeric_cols: List[str],
    ) -> pl.DataFrame:
        """Remove outliers using z-score method.

        Args:
            df: Input DataFrame
            numeric_cols: Columns to check for outliers

        Returns:
            DataFrame with outliers removed
        """
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()

            if std == 0:
                continue

            df = df.with_columns([
                (pl.col(col) - mean).abs().truediv(std).alias(f"{col}_zscore")
            ])

            df = df.filter(pl.col(f"{col}_zscore") <= 3)
            df = df.drop(f"{col}_zscore")

        return df

    def _remove_duplicates(self, df: pl.DataFrame) -> tuple[int, pl.DataFrame]:
        """Remove duplicate rows.

        Args:
            df: Input DataFrame

        Returns:
            Tuple of (duplicates_removed, cleaned_df)
        """
        rows_before = df.height
        df = df.unique(maintain_order=True)
        duplicates_removed = rows_before - df.height

        if duplicates_removed > 0:
            logger.info(f"Duplicates removed: {duplicates_removed}")

        return duplicates_removed, df

    def _handle_remaining_nulls(self, df: pl.DataFrame) -> pl.DataFrame:
        """Fill remaining null values.

        Uses mean for numeric columns, mode for categorical columns.

        Args:
            df: Input DataFrame

        Returns:
            DataFrame with nulls filled
        """
        for col in df.columns:
            if df[col].null_count() == 0:
                continue

            if df[col].dtype in [pl.Int64, pl.Float64]:
                # Fill numeric with mean
                fill_value = df[col].mean()
                if fill_value is not None:
                    df = df.with_columns([
                        pl.col(col).fill_null(fill_value)
                    ])
            else:
                # Fill categorical with mode (first most common value)
                try:
                    # mode() returns a Series, get the first value
                    mode_series = df[col].mode()
                    if len(mode_series) > 0:
                        fill_value = mode_series[0]
                        df = df.with_columns([
                            pl.col(col).fill_null(fill_value)
                        ])
                    else:
                        # If no mode, fill with placeholder
                        df = df.with_columns([
                            pl.col(col).fill_null("UNKNOWN")
                        ])
                except Exception:
                    # Fallback to placeholder
                    df = df.with_columns([
                        pl.col(col).fill_null("UNKNOWN")
                    ])

        return df

    def generate_notebook(self) -> str:
        """Generate marimo notebook with cleaning analysis.

        Returns:
            Path to saved notebook
        """
        if not self.notebook:
            self.setup_notebook(
                title=f"{self.name} - Data Cleaning Report",
                description="Interactive data cleaning analysis and results"
            )

        # Add cleaning summary
        self.notebook.add_markdown("## Data Cleaning Summary")
        self.notebook.add_code("""
# Load cleaned data
original_df = duckdb.query('SELECT * FROM original_data').pl()
cleaned_df = duckdb.query('SELECT * FROM cleaned_data').pl()

print(f"Original shape: {original_df.shape}")
print(f"Cleaned shape: {cleaned_df.shape}")
print(f"Rows removed: {original_df.height - cleaned_df.height}")
""")

        # Add null analysis
        self.notebook.add_markdown("## Null Value Analysis")
        self.notebook.add_code("""
print("Original null counts:")
print(original_df.null_count())

print("\\nCleaned null counts:")
print(cleaned_df.null_count())
""")

        # Add data comparison visualization
        self.notebook.add_markdown("## Column Comparison")
        self.notebook.add_code("""
# Show column names and types
print("Columns in cleaned data:")
for col, dtype in zip(cleaned_df.columns, cleaned_df.dtypes):
    print(f"  {col}: {dtype}")
""")

        # Add conclusions
        self.notebook.add_markdown("## Data Quality Improvements")
        self.notebook.add_code("""
# Summary statistics
print("Cleaned Data Summary:")
print(cleaned_df.describe())
""")

        return str(super().generate_notebook())
