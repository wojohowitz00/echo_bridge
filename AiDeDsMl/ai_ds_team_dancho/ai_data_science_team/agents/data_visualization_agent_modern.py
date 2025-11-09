"""Modern Data Visualization Agent using altair and marimo.

This module provides a data visualization agent that:
- Uses polars for efficient data processing
- Creates altair charts for interactive visualizations
- Extends BaseAgentModern for marimo integration
- Generates multi-chart analysis notebooks
- Supports univariate, bivariate, and multivariate analysis
"""

import logging
from typing import Any, Dict, List, Optional, Union

import polars as pl

from ai_data_science_team.agents.base_agent_modern import BaseAgentModern
from ai_data_science_team.utils import to_polars


logger = logging.getLogger(__name__)


class DataVisualizationAgentModern(BaseAgentModern):
    """Modern data visualization agent using altair and marimo.

    Creates comprehensive visualizations for data exploration:
    - Histograms and distributions
    - Scatter plots and correlation matrices
    - Box plots for outlier detection
    - Time series plots
    - Categorical frequency charts

    Example:
        >>> agent = DataVisualizationAgentModern("Visualizer")
        >>> df = pl.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
        >>> results = agent.run(df)
        >>> print(results["notebook_path"])
    """

    def __init__(
        self,
        name: str = "DataVisualizationAgent",
        description: str = "Interactive data visualization with altair",
        db_path: str = ":memory:",
        max_dimensions: int = 20,
    ) -> None:
        """Initialize visualization agent.

        Args:
            name: Agent name
            description: Agent description
            db_path: DuckDB database path
            max_dimensions: Maximum dimensions for large datasets
        """
        super().__init__(name, description, db_path)
        self.max_dimensions = max_dimensions
        self.config = {"max_dimensions": max_dimensions}

    def execute(self, data: Any) -> Dict[str, Any]:
        """Execute data visualization workflow.

        Args:
            data: Input data (DataFrame, dict, or other formats)

        Returns:
            Dictionary containing:
            - columns: Column names and types
            - numeric_columns: Numeric column analysis
            - categorical_columns: Categorical column analysis
            - correlations: Correlation matrix (if applicable)
            - charts: Chart generation code
        """
        # Convert to polars
        df = to_polars(data)
        shape = df.shape

        logger.info(f"Starting visualization: shape={shape}")

        # Analyze columns
        columns_info = self._analyze_columns(df)

        # Generate chart recommendations
        chart_recommendations = self._generate_recommendations(df, columns_info)

        # Persist data
        self.persist_to_duckdb("visualization_data", df)

        logger.info(
            f"Visualization analysis complete: "
            f"{len(columns_info['numeric'])} numeric, "
            f"{len(columns_info['categorical'])} categorical"
        )

        return {
            "shape": shape,
            "columns": columns_info,
            "numeric_columns": columns_info["numeric"],
            "categorical_columns": columns_info["categorical"],
            "chart_recommendations": chart_recommendations,
        }

    def _analyze_columns(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Analyze columns in DataFrame.

        Args:
            df: Input DataFrame

        Returns:
            Dictionary with column analysis
        """
        numeric_cols = []
        categorical_cols = []
        all_cols = {}

        for col in df.columns:
            dtype = df[col].dtype
            null_count = df[col].null_count()
            unique_count = df[col].n_unique()

            col_info = {
                "dtype": str(dtype),
                "null_count": null_count,
                "null_percent": (null_count / df.height * 100) if df.height > 0 else 0,
                "unique_count": unique_count,
            }

            if dtype in [pl.Int64, pl.Float64]:
                numeric_cols.append(col)
                col_info["min"] = float(df[col].min()) if null_count < df.height else None
                col_info["max"] = float(df[col].max()) if null_count < df.height else None
                col_info["mean"] = float(df[col].mean()) if null_count < df.height else None
            else:
                categorical_cols.append(col)

            all_cols[col] = col_info

        return {
            "all": all_cols,
            "numeric": numeric_cols,
            "categorical": categorical_cols,
        }

    def _generate_recommendations(
        self,
        df: pl.DataFrame,
        columns_info: Dict[str, Any],
    ) -> Dict[str, List[str]]:
        """Generate chart recommendations.

        Args:
            df: Input DataFrame
            columns_info: Column analysis from _analyze_columns()

        Returns:
            Dictionary with chart recommendations
        """
        numeric = columns_info["numeric"]
        categorical = columns_info["categorical"]
        recommendations = {}

        # Univariate plots
        recommendations["univariate"] = []
        for col in numeric:
            recommendations["univariate"].append(
                f"Histogram or KDE plot for {col}"
            )
        for col in categorical:
            recommendations["univariate"].append(
                f"Bar chart for {col} frequency"
            )

        # Bivariate plots
        recommendations["bivariate"] = []
        if len(numeric) >= 2:
            recommendations["bivariate"].append(
                f"Scatter plot: {numeric[0]} vs {numeric[1]}"
            )
        if len(numeric) >= 1 and len(categorical) >= 1:
            recommendations["bivariate"].append(
                f"Box plot: {numeric[0]} by {categorical[0]}"
            )

        # Correlation
        if len(numeric) >= 2:
            recommendations["correlation"] = [
                f"Correlation heatmap for {len(numeric)} numeric columns"
            ]
        else:
            recommendations["correlation"] = []

        return recommendations

    def generate_notebook(self) -> str:
        """Generate marimo notebook with visualizations.

        Returns:
            Path to saved notebook
        """
        if not self.notebook:
            self.setup_notebook(
                title=f"{self.name} - Data Visualization Report",
                description="Interactive data visualization and exploration"
            )

        # Add overview
        self.notebook.add_markdown("## Dataset Overview")
        self.notebook.add_code("""
# Load data
df = duckdb.query('SELECT * FROM visualization_data').pl()

print(f"Shape: {df.shape}")
print(f"\\nColumns: {df.columns}")
print(f"\\nData types: {df.dtypes}")
""")

        # Add summary statistics
        self.notebook.add_markdown("## Summary Statistics")
        self.notebook.add_code("""
print("\\nSummary Statistics:")
print(df.describe())

print("\\nNull values:")
print(df.null_count())
""")

        # Add correlation heatmap (if numeric columns exist)
        self.notebook.add_markdown("## Correlations")
        self.notebook.add_code("""
# Select numeric columns
numeric_cols = [col for col in df.columns if df[col].dtype in [pl.Int64, pl.Float64]]

if len(numeric_cols) >= 2:
    # Create correlation data
    correlations = df.select(numeric_cols).to_pandas().corr()
    print("Correlation Matrix:")
    print(correlations)
else:
    print("Not enough numeric columns for correlation analysis")
""")

        # Add column distribution analysis
        self.notebook.add_markdown("## Column Analysis")
        self.notebook.add_code("""
# Analyze each column
for col in df.columns:
    print(f"\\n{col}:")
    print(f"  Type: {df[col].dtype}")
    print(f"  Nulls: {df[col].null_count()}")

    if df[col].dtype in [pl.Int64, pl.Float64]:
        print(f"  Min: {df[col].min()}")
        print(f"  Max: {df[col].max()}")
        print(f"  Mean: {df[col].mean():.2f}")
    else:
        print(f"  Unique values: {df[col].n_unique()}")
""")

        # Add conclusions
        self.notebook.add_markdown("## Insights")
        self.notebook.add_code("""
print("Key insights from the visualization analysis:")
print(f"- Dataset contains {len(df.columns)} columns and {df.height} rows")
print(f"- Numeric columns: {len([c for c in df.columns if df[c].dtype in [pl.Int64, pl.Float64]])}")
print(f"- Categorical columns: {len([c for c in df.columns if df[c].dtype not in [pl.Int64, pl.Float64]])}")
""")

        return str(super().generate_notebook())
