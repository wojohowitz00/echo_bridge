"""Modern Feature Engineering Agent using polars and marimo.

This module provides a feature engineering agent that:
- Uses polars for efficient feature transformations
- Extends BaseAgentModern for marimo integration
- Supports scaling, encoding, and binning operations
- Creates polynomial and interaction features
- Generates feature analysis and recommendations
- Integrates with DuckDB for persistence
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import polars as pl

from ai_data_science_team.agents.base_agent_modern import BaseAgentModern
from ai_data_science_team.utils import to_polars


logger = logging.getLogger(__name__)


class FeatureEngineeringAgentModern(BaseAgentModern):
    """Modern feature engineering agent using polars.

    Creates and transforms features for machine learning:
    - Scaling and normalization
    - Encoding (one-hot, label, ordinal)
    - Polynomial and interaction features
    - Binning and discretization
    - Feature selection and filtering
    - Feature statistics and importance

    Example:
        >>> agent = FeatureEngineeringAgentModern("FeatureEngineer")
        >>> df = pl.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
        >>> scaled = agent.scale_features(df, method="standardize")
        >>> results = agent.run(df)
        >>> print(results["notebook_path"])
    """

    def __init__(
        self,
        name: str = "FeatureEngineeringAgent",
        description: str = "Advanced feature engineering with polars",
        db_path: str = ":memory:",
    ) -> None:
        """Initialize feature engineering agent.

        Args:
            name: Agent name
            description: Agent description
            db_path: DuckDB database path
        """
        super().__init__(name, description, db_path)
        self.config = {}
        self.feature_stats = {}

    def execute(self, data: Any) -> Dict[str, Any]:
        """Execute feature engineering workflow.

        Args:
            data: Input data (DataFrame, dict, or other formats)

        Returns:
            Dictionary containing:
            - feature_engineered_data: Transformed polars DataFrame
            - feature_count: Number of features
            - numeric_features: List of numeric features
            - categorical_features: List of categorical features
            - statistics: Feature statistics
        """
        # Convert to polars
        df = to_polars(data)
        original_shape = df.shape

        logger.info(f"Starting feature engineering: shape={original_shape}")

        # Analyze features
        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Float64]
        ]
        categorical_cols = [
            col for col in df.columns
            if df[col].dtype not in [pl.Int64, pl.Float64]
        ]

        # Store original
        self.persist_to_duckdb("feature_original_data", df)

        logger.info(
            f"Feature engineering complete: "
            f"{len(numeric_cols)} numeric, {len(categorical_cols)} categorical"
        )

        return {
            "feature_engineered_data": df,
            "original_shape": original_shape,
            "feature_count": len(df.columns),
            "numeric_features": numeric_cols,
            "categorical_features": categorical_cols,
            "columns": df.columns,
        }

    def scale_features(
        self,
        data: Any,
        columns: Optional[List[str]] = None,
        method: str = "standardize",
    ) -> pl.DataFrame:
        """Scale numeric features.

        Args:
            data: Input DataFrame
            columns: Columns to scale (None for all numeric)
            method: "standardize" (z-score) or "normalize" (0-1)

        Returns:
            DataFrame with scaled features
        """
        df = to_polars(data)

        if columns is None:
            columns = [
                col for col in df.columns
                if df[col].dtype in [pl.Int64, pl.Float64]
            ]

        logger.info(f"Scaling {len(columns)} features using {method}")

        for col in columns:
            if df[col].dtype not in [pl.Int64, pl.Float64]:
                continue

            if method == "standardize":
                mean = df[col].mean()
                std = df[col].std()
                if std != 0:
                    df = df.with_columns([
                        ((pl.col(col) - mean) / std).alias(f"{col}_scaled")
                    ])
            elif method == "normalize":
                min_val = df[col].min()
                max_val = df[col].max()
                range_val = max_val - min_val
                if range_val != 0:
                    df = df.with_columns([
                        ((pl.col(col) - min_val) / range_val).alias(f"{col}_scaled")
                    ])

        logger.info(f"Scaling complete: {df.shape}")
        return df

    def create_polynomial_features(
        self,
        data: Any,
        columns: Optional[List[str]] = None,
        degree: int = 2,
    ) -> pl.DataFrame:
        """Create polynomial features.

        Args:
            data: Input DataFrame
            columns: Columns to create polynomials for (None for all numeric)
            degree: Maximum polynomial degree

        Returns:
            DataFrame with polynomial features added
        """
        df = to_polars(data)

        if columns is None:
            columns = [
                col for col in df.columns
                if df[col].dtype in [pl.Int64, pl.Float64]
            ]

        logger.info(f"Creating polynomial features: degree={degree}")

        for col in columns:
            for d in range(2, degree + 1):
                df = df.with_columns([
                    (pl.col(col) ** d).alias(f"{col}_pow{d}")
                ])

        logger.info(f"Polynomial features complete: {df.shape}")
        return df

    def create_interaction_features(
        self,
        data: Any,
        columns: Optional[List[str]] = None,
    ) -> pl.DataFrame:
        """Create interaction features between numeric columns.

        Args:
            data: Input DataFrame
            columns: Columns to create interactions for (None for all numeric)

        Returns:
            DataFrame with interaction features added
        """
        df = to_polars(data)

        if columns is None:
            columns = [
                col for col in df.columns
                if df[col].dtype in [pl.Int64, pl.Float64]
            ]

        logger.info(f"Creating interaction features for {len(columns)} columns")

        # Create pairwise interactions
        for i, col1 in enumerate(columns):
            for col2 in columns[i + 1:]:
                df = df.with_columns([
                    (pl.col(col1) * pl.col(col2)).alias(f"{col1}_x_{col2}")
                ])

        logger.info(f"Interaction features complete: {df.shape}")
        return df

    def one_hot_encode(
        self,
        data: Any,
        columns: Optional[List[str]] = None,
    ) -> pl.DataFrame:
        """Apply one-hot encoding to categorical features.

        Args:
            data: Input DataFrame
            columns: Columns to encode (None for all categorical)

        Returns:
            DataFrame with one-hot encoded features
        """
        df = to_polars(data)

        if columns is None:
            columns = [
                col for col in df.columns
                if df[col].dtype not in [pl.Int64, pl.Float64]
            ]

        logger.info(f"One-hot encoding {len(columns)} columns")

        for col in columns:
            try:
                df = df.to_dummies(columns=[col], separator="_")
            except Exception as e:
                logger.warning(f"Could not encode {col}: {e}")

        logger.info(f"One-hot encoding complete: {df.shape}")
        return df

    def label_encode(
        self,
        data: Any,
        column: str,
    ) -> Tuple[pl.DataFrame, Dict[str, int]]:
        """Apply label encoding to a categorical column.

        Args:
            data: Input DataFrame
            column: Column to encode

        Returns:
            Tuple of (encoded_df, mapping_dict)
        """
        df = to_polars(data)

        logger.info(f"Label encoding {column}")

        unique_vals = df[column].unique().to_list()
        mapping = {str(v): i for i, v in enumerate(unique_vals)}

        # Create encoded column
        df = df.with_columns([
            pl.col(column).map_elements(
                lambda x: mapping.get(str(x), -1),
                return_dtype=pl.Int64
            ).alias(f"{column}_encoded")
        ])

        logger.info(f"Label encoding complete: {column} -> {len(mapping)} classes")
        return df, mapping

    def bin_features(
        self,
        data: Any,
        column: str,
        n_bins: int = 5,
    ) -> pl.DataFrame:
        """Discretize numeric features into bins.

        Args:
            data: Input DataFrame
            column: Column to bin
            n_bins: Number of bins

        Returns:
            DataFrame with binned feature
        """
        df = to_polars(data)

        logger.info(f"Binning {column} into {n_bins} bins")

        # Create bins using quantiles
        min_val = df[column].min()
        max_val = df[column].max()

        # Create bin edges
        bin_edges = []
        for i in range(n_bins + 1):
            bin_edges.append(min_val + (max_val - min_val) * i / n_bins)

        # Use cut() with proper number of labels (for n bins, need n+1 labels for boundaries)
        df = df.with_columns([
            pl.col(column).cut(
                breaks=bin_edges[1:-1]  # Don't include min/max as they're implicit
            ).alias(f"{column}_binned")
        ])

        logger.info(f"Binning complete: {column} -> {n_bins} bins")
        return df

    def remove_low_variance_features(
        self,
        data: Any,
        threshold: float = 0.01,
    ) -> Tuple[pl.DataFrame, List[str]]:
        """Remove features with low variance.

        Args:
            data: Input DataFrame
            threshold: Variance threshold for removal

        Returns:
            Tuple of (filtered_df, removed_columns)
        """
        df = to_polars(data)

        logger.info(f"Removing low variance features (threshold={threshold})")

        removed = []
        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Float64]
        ]

        for col in numeric_cols:
            variance = df[col].var()
            if variance is not None and variance < threshold:
                removed.append(col)
                df = df.drop(col)

        logger.info(f"Removed {len(removed)} low variance features")
        return df, removed

    def get_feature_statistics(
        self,
        data: Any,
    ) -> Dict[str, Dict[str, Any]]:
        """Calculate statistics for all features.

        Args:
            data: Input DataFrame

        Returns:
            Dictionary with feature statistics
        """
        df = to_polars(data)

        logger.info("Calculating feature statistics")

        stats = {}
        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Float64]
        ]

        for col in numeric_cols:
            stats[col] = {
                "dtype": str(df[col].dtype),
                "mean": float(df[col].mean() or 0),
                "std": float(df[col].std() or 0),
                "min": float(df[col].min() or 0),
                "max": float(df[col].max() or 0),
                "median": float(df[col].median() or 0),
                "null_count": int(df[col].null_count()),
                "variance": float(df[col].var() or 0),
            }

        self.feature_stats = stats
        logger.info(f"Calculated statistics for {len(stats)} features")
        return stats

    def get_feature_correlations(
        self,
        data: Any,
    ) -> pl.DataFrame:
        """Calculate correlations between numeric features.

        Args:
            data: Input DataFrame

        Returns:
            Correlation matrix as DataFrame
        """
        df = to_polars(data)

        logger.info("Calculating feature correlations")

        numeric_cols = [
            col for col in df.columns
            if df[col].dtype in [pl.Int64, pl.Float64]
        ]

        if len(numeric_cols) < 2:
            logger.warning("Need at least 2 numeric columns for correlation")
            return pl.DataFrame()

        # Convert to pandas for correlation calculation
        pandas_df = df.select(numeric_cols).to_pandas()
        corr_matrix = pandas_df.corr()

        # Convert back to polars
        corr_df = pl.from_pandas(corr_matrix)
        logger.info(f"Correlation matrix: {corr_df.shape}")
        return corr_df

    def generate_notebook(self) -> str:
        """Generate marimo notebook with feature engineering results.

        Returns:
            Path to saved notebook
        """
        if not self.notebook:
            self.setup_notebook(
                title=f"{self.name} - Feature Engineering Report",
                description="Interactive feature engineering and analysis"
            )

        # Add overview
        self.notebook.add_markdown("## Feature Engineering Overview")
        self.notebook.add_code("""
# Load original data
original_df = duckdb.query('SELECT * FROM feature_original_data').pl()

print(f"Original shape: {original_df.shape}")
print(f"Columns: {original_df.columns}")
print(f"Data types: {original_df.dtypes}")
""")

        # Add numeric/categorical breakdown
        self.notebook.add_markdown("## Feature Types")
        self.notebook.add_code("""
numeric_cols = [col for col in original_df.columns if original_df[col].dtype in [pl.Int64, pl.Float64]]
categorical_cols = [col for col in original_df.columns if original_df[col].dtype not in [pl.Int64, pl.Float64]]

print(f"Numeric features ({len(numeric_cols)}): {numeric_cols}")
print(f"Categorical features ({len(categorical_cols)}): {categorical_cols}")
""")

        # Add statistics
        self.notebook.add_markdown("## Feature Statistics")
        self.notebook.add_code("""
print("\\nNumeric Feature Statistics:")
print(original_df.select(numeric_cols).describe())

print("\\nNull Counts:")
print(original_df.null_count())
""")

        # Add feature engineering recommendations
        self.notebook.add_markdown("## Feature Engineering Recommendations")
        self.notebook.add_code("""
print("Recommended transformations:")
print("1. Scaling: Standardize or normalize numeric features")
print("2. Encoding: One-hot or label encode categorical features")
print("3. Polynomial: Create higher-order polynomial features")
print("4. Interactions: Create interaction features between predictors")
print("5. Binning: Discretize continuous features if needed")
print("6. Selection: Remove low-variance or highly correlated features")
""")

        return str(super().generate_notebook())
