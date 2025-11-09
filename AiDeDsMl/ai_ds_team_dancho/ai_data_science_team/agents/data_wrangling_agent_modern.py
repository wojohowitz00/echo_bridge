"""Modern Data Wrangling Agent using polars and marimo.

This module provides a data wrangling agent that:
- Uses polars for efficient data transformation
- Extends BaseAgentModern for marimo integration
- Supports pivoting, unpivoting, and aggregation
- Handles joins, grouping, and data reshaping
- Generates analysis notebooks with transformation results
"""

import logging
from typing import Any, Dict, List, Optional, Union

import polars as pl

from ai_data_science_team.agents.base_agent_modern import BaseAgentModern
from ai_data_science_team.utils import to_polars


logger = logging.getLogger(__name__)


class DataWranglingAgentModern(BaseAgentModern):
    """Modern data wrangling agent using polars.

    Transforms and reshapes data for analysis:
    - Pivot and unpivot operations
    - Aggregation and grouping
    - Joins (inner, left, right, outer, cross)
    - Column and row filtering
    - Sorting and ordering
    - String and numeric transformations

    Example:
        >>> agent = DataWranglingAgentModern("Wrangler")
        >>> df = pl.DataFrame({"group": ["A", "B"], "value": [1, 2]})
        >>> results = agent.run(df)
        >>> print(results["notebook_path"])
    """

    def __init__(
        self,
        name: str = "DataWranglingAgent",
        description: str = "Advanced data transformation with polars",
        db_path: str = ":memory:",
    ) -> None:
        """Initialize data wrangling agent.

        Args:
            name: Agent name
            description: Agent description
            db_path: DuckDB database path
        """
        super().__init__(name, description, db_path)
        self.config = {}

    def execute(self, data: Any) -> Dict[str, Any]:
        """Execute data wrangling workflow.

        Args:
            data: Input data (DataFrame, dict, or other formats)

        Returns:
            Dictionary containing:
            - wrangled_data: Transformed polars DataFrame
            - shape: DataFrame shape before and after
            - operations_applied: List of transformations
            - summary: Data summary after transformations
        """
        # Convert to polars
        df = to_polars(data)
        original_shape = df.shape

        logger.info(f"Starting data wrangling: shape={original_shape}")

        # Store original for reference
        self.persist_to_duckdb("original_wrangling_data", df)

        # Return analysis
        return {
            "wrangled_data": df,
            "original_shape": original_shape,
            "final_shape": df.shape,
            "columns": df.columns,
            "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        }

    def pivot(
        self,
        data: Any,
        index: Union[str, List[str]],
        columns: str,
        values: str,
        aggregate_function: str = "first",
    ) -> pl.DataFrame:
        """Pivot data from long to wide format.

        Args:
            data: Input DataFrame
            index: Column(s) to use as row index
            columns: Column to pivot into new columns
            values: Column with values to populate
            aggregate_function: Aggregation function ("first", "sum", "mean", "count")

        Returns:
            Pivoted DataFrame
        """
        df = to_polars(data)

        logger.info(
            f"Pivoting: index={index}, columns={columns}, values={values}, "
            f"agg={aggregate_function}"
        )

        if aggregate_function == "first":
            agg_func = "first"
        elif aggregate_function == "sum":
            agg_func = "sum"
        elif aggregate_function == "mean":
            agg_func = "mean"
        elif aggregate_function == "count":
            agg_func = "count"
        else:
            agg_func = "first"

        pivoted = df.pivot(
            values=values,
            index=index,
            columns=columns,
            aggregate_function=agg_func,
        )

        logger.info(f"Pivot complete: {pivoted.shape}")
        return pivoted

    def unpivot(
        self,
        data: Any,
        index: Union[str, List[str]],
        variable_name: str = "variable",
        value_name: str = "value",
    ) -> pl.DataFrame:
        """Unpivot data from wide to long format.

        Args:
            data: Input DataFrame
            index: Column(s) to keep as identifier
            variable_name: Name for the variable column
            value_name: Name for the value column

        Returns:
            Unpivoted DataFrame
        """
        df = to_polars(data)

        logger.info(f"Unpivoting: index={index}")

        unpivoted = df.unpivot(
            index=index,
            variable_name=variable_name,
            value_name=value_name,
        )

        logger.info(f"Unpivot complete: {unpivoted.shape}")
        return unpivoted

    def group_and_aggregate(
        self,
        data: Any,
        group_by: Union[str, List[str]],
        aggregations: Dict[str, Union[str, List[str]]],
    ) -> pl.DataFrame:
        """Group data and apply aggregations.

        Args:
            data: Input DataFrame
            group_by: Column(s) to group by
            aggregations: Dict mapping columns to aggregation functions
                         {"column": "sum"} or {"column": ["sum", "mean"]}

        Returns:
            Aggregated DataFrame
        """
        df = to_polars(data)

        logger.info(f"Grouping by {group_by}")

        # Build aggregation expressions
        agg_exprs = {}
        for col, funcs in aggregations.items():
            if isinstance(funcs, str):
                funcs = [funcs]

            for func in funcs:
                new_col = f"{col}_{func}"
                if func == "sum":
                    agg_exprs[new_col] = pl.col(col).sum()
                elif func == "mean":
                    agg_exprs[new_col] = pl.col(col).mean()
                elif func == "count":
                    agg_exprs[new_col] = pl.col(col).count()
                elif func == "min":
                    agg_exprs[new_col] = pl.col(col).min()
                elif func == "max":
                    agg_exprs[new_col] = pl.col(col).max()
                elif func == "first":
                    agg_exprs[new_col] = pl.col(col).first()
                elif func == "last":
                    agg_exprs[new_col] = pl.col(col).last()

        aggregated = df.group_by(group_by).agg(**agg_exprs)

        logger.info(f"Aggregation complete: {aggregated.shape}")
        return aggregated

    def join_data(
        self,
        left_data: Any,
        right_data: Any,
        left_on: Union[str, List[str]],
        right_on: Union[str, List[str]],
        how: str = "inner",
    ) -> pl.DataFrame:
        """Join two DataFrames.

        Args:
            left_data: Left DataFrame
            right_data: Right DataFrame
            left_on: Column(s) to join on from left
            right_on: Column(s) to join on from right
            how: Join type ("inner", "left", "right", "outer", "cross")

        Returns:
            Joined DataFrame
        """
        left_df = to_polars(left_data)
        right_df = to_polars(right_data)

        logger.info(f"Joining: {how} join on {left_on} = {right_on}")

        joined = left_df.join(
            right_df,
            left_on=left_on,
            right_on=right_on,
            how=how,
        )

        logger.info(f"Join complete: {joined.shape}")
        return joined

    def filter_rows(
        self,
        data: Any,
        conditions: Dict[str, Any],
    ) -> pl.DataFrame:
        """Filter rows based on conditions.

        Args:
            data: Input DataFrame
            conditions: Dict mapping column names to filter values
                       {"column": value} filters where column == value

        Returns:
            Filtered DataFrame
        """
        df = to_polars(data)

        logger.info(f"Filtering with {len(conditions)} conditions")

        for col, value in conditions.items():
            if isinstance(value, (list, tuple)):
                df = df.filter(pl.col(col).is_in(value))
            else:
                df = df.filter(pl.col(col) == value)

        logger.info(f"Filter complete: {df.shape}")
        return df

    def select_columns(
        self,
        data: Any,
        columns: Union[str, List[str]],
    ) -> pl.DataFrame:
        """Select specific columns.

        Args:
            data: Input DataFrame
            columns: Column name(s) to select

        Returns:
            DataFrame with selected columns
        """
        df = to_polars(data)

        logger.info(f"Selecting {len(columns) if isinstance(columns, list) else 1} columns")

        selected = df.select(columns)

        logger.info(f"Selection complete: {selected.shape}")
        return selected

    def drop_columns(
        self,
        data: Any,
        columns: Union[str, List[str]],
    ) -> pl.DataFrame:
        """Drop specific columns.

        Args:
            data: Input DataFrame
            columns: Column name(s) to drop

        Returns:
            DataFrame with columns dropped
        """
        df = to_polars(data)

        logger.info(f"Dropping {len(columns) if isinstance(columns, list) else 1} columns")

        dropped = df.drop(columns)

        logger.info(f"Drop complete: {dropped.shape}")
        return dropped

    def sort_data(
        self,
        data: Any,
        by: Union[str, List[str]],
        descending: bool = False,
    ) -> pl.DataFrame:
        """Sort DataFrame by column(s).

        Args:
            data: Input DataFrame
            by: Column name(s) to sort by
            descending: Whether to sort in descending order

        Returns:
            Sorted DataFrame
        """
        df = to_polars(data)

        logger.info(f"Sorting by {by}, descending={descending}")

        sorted_df = df.sort(by, descending=descending)

        logger.info(f"Sort complete: {sorted_df.shape}")
        return sorted_df

    def rename_columns(
        self,
        data: Any,
        mapping: Dict[str, str],
    ) -> pl.DataFrame:
        """Rename columns.

        Args:
            data: Input DataFrame
            mapping: Dict mapping old names to new names

        Returns:
            DataFrame with renamed columns
        """
        df = to_polars(data)

        logger.info(f"Renaming {len(mapping)} columns")

        renamed = df.rename(mapping)

        logger.info(f"Rename complete: {renamed.shape}")
        return renamed

    def get_unique_values(
        self,
        data: Any,
        column: str,
    ) -> List[Any]:
        """Get unique values in a column.

        Args:
            data: Input DataFrame
            column: Column to get unique values from

        Returns:
            List of unique values
        """
        df = to_polars(data)
        return df[column].unique().to_list()

    def generate_notebook(self) -> str:
        """Generate marimo notebook with wrangling results.

        Returns:
            Path to saved notebook
        """
        if not self.notebook:
            self.setup_notebook(
                title=f"{self.name} - Data Wrangling Report",
                description="Interactive data transformation and wrangling analysis"
            )

        # Add overview
        self.notebook.add_markdown("## Data Wrangling Overview")
        self.notebook.add_code("""
# Load wrangled data
original_df = duckdb.query('SELECT * FROM original_wrangling_data').pl()

print(f"Original shape: {original_df.shape}")
print(f"Columns: {original_df.columns}")
print(f"Data types: {original_df.dtypes}")
""")

        # Add unique value analysis
        self.notebook.add_markdown("## Column Value Analysis")
        self.notebook.add_code("""
print("\\nUnique values per column:")
for col in original_df.columns:
    unique_count = original_df[col].n_unique()
    print(f"  {col}: {unique_count} unique values")
    if unique_count <= 10:
        print(f"    Values: {original_df[col].unique().to_list()}")
""")

        # Add null analysis
        self.notebook.add_markdown("## Data Quality")
        self.notebook.add_code("""
print("\\nNull counts:")
print(original_df.null_count())

print("\\nBasic statistics:")
print(original_df.describe())
""")

        # Add wrangling recommendations
        self.notebook.add_markdown("## Wrangling Recommendations")
        self.notebook.add_code("""
print("Potential wrangling operations:")
print("- Pivot: Convert columns to long/wide format")
print("- Aggregate: Group and summarize data")
print("- Join: Combine with other datasets")
print("- Filter: Select rows by conditions")
print("- Transform: Rename columns, convert types")
""")

        return str(super().generate_notebook())
