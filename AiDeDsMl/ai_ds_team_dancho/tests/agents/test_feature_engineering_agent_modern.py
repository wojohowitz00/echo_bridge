"""Unit tests for FeatureEngineeringAgentModern.

Tests cover:
- Feature scaling (standardization and normalization)
- Polynomial and interaction features
- Encoding (one-hot and label)
- Binning and discretization
- Feature selection and statistics
- Feature analysis workflows
"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from ai_data_science_team.agents.feature_engineering_agent_modern import (
    FeatureEngineeringAgentModern,
)


class TestFeatureEngineeringInitialization:
    """Tests for agent initialization."""

    def test_agent_creation(self):
        """Test creating feature engineering agent."""
        agent = FeatureEngineeringAgentModern("Engineer")

        assert agent.name == "Engineer"
        agent.close()

    def test_agent_with_custom_db_path(self):
        """Test creating agent with custom database path."""
        agent = FeatureEngineeringAgentModern("Engineer", db_path=":memory:")

        assert agent.name == "Engineer"
        agent.close()


class TestFeatureScaling:
    """Tests for feature scaling operations."""

    def test_standardize_single_column(self):
        """Test standardization of single column."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        scaled = agent.scale_features(df, columns=["value"], method="standardize")

        assert "value_scaled" in scaled.columns
        # Mean should be near 0 after standardization
        mean = scaled["value_scaled"].mean()
        assert abs(mean) < 0.01
        agent.close()

    def test_normalize_single_column(self):
        """Test normalization to 0-1 range."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        scaled = agent.scale_features(df, columns=["value"], method="normalize")

        assert "value_scaled" in scaled.columns
        # Min should be 0, max should be 1
        assert scaled["value_scaled"].min() == 0.0
        assert scaled["value_scaled"].max() == 1.0
        agent.close()

    def test_scale_multiple_columns(self):
        """Test scaling multiple columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1.0, 2.0, 3.0],
            "col2": [10.0, 20.0, 30.0],
        })

        scaled = agent.scale_features(
            df,
            columns=["col1", "col2"],
            method="standardize",
        )

        assert "col1_scaled" in scaled.columns
        assert "col2_scaled" in scaled.columns
        agent.close()

    def test_scale_auto_detect_numeric(self):
        """Test auto-detection of numeric columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "numeric": [1.0, 2.0, 3.0],
            "categorical": ["A", "B", "C"],
        })

        scaled = agent.scale_features(df, columns=None, method="standardize")

        assert "numeric_scaled" in scaled.columns
        # Categorical should not be scaled
        assert "categorical_scaled" not in scaled.columns
        agent.close()


class TestPolynomialFeatures:
    """Tests for polynomial feature creation."""

    def test_create_polynomial_degree2(self):
        """Test creating polynomial features degree 2."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
        })

        poly = agent.create_polynomial_features(df, columns=["x"], degree=2)

        assert "x_pow2" in poly.columns
        assert poly["x_pow2"].to_list() == [1.0, 4.0, 9.0]
        agent.close()

    def test_create_polynomial_degree3(self):
        """Test creating polynomial features degree 3."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
        })

        poly = agent.create_polynomial_features(df, columns=["x"], degree=3)

        assert "x_pow2" in poly.columns
        assert "x_pow3" in poly.columns
        assert poly["x_pow3"].to_list() == [1.0, 8.0, 27.0]
        agent.close()

    def test_polynomial_multiple_columns(self):
        """Test polynomial features on multiple columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0],
            "y": [3.0, 4.0],
        })

        poly = agent.create_polynomial_features(df, columns=["x", "y"], degree=2)

        assert "x_pow2" in poly.columns
        assert "y_pow2" in poly.columns
        agent.close()


class TestInteractionFeatures:
    """Tests for interaction feature creation."""

    def test_create_interactions_basic(self):
        """Test creating interaction features."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
            "y": [10.0, 20.0, 30.0],
        })

        interacted = agent.create_interaction_features(df, columns=["x", "y"])

        assert "x_x_y" in interacted.columns
        assert interacted["x_x_y"].to_list() == [10.0, 40.0, 90.0]
        agent.close()

    def test_interaction_three_columns(self):
        """Test interactions with three columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "a": [1.0, 2.0],
            "b": [3.0, 4.0],
            "c": [5.0, 6.0],
        })

        interacted = agent.create_interaction_features(
            df,
            columns=["a", "b", "c"],
        )

        # Should create a_x_b, a_x_c, b_x_c
        assert "a_x_b" in interacted.columns
        assert "a_x_c" in interacted.columns
        assert "b_x_c" in interacted.columns
        agent.close()


class TestEncoding:
    """Tests for feature encoding."""

    def test_label_encode(self):
        """Test label encoding of categorical column."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "category": ["A", "B", "A", "C"],
        })

        encoded, mapping = agent.label_encode(df, column="category")

        assert "category_encoded" in encoded.columns
        assert len(mapping) == 3
        assert "A" in mapping
        agent.close()

    def test_label_encode_returns_mapping(self):
        """Test that label encoding returns correct mapping."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "color": ["red", "blue", "red"],
        })

        encoded, mapping = agent.label_encode(df, column="color")

        assert mapping["red"] == 0 or mapping["red"] == 1
        assert mapping["blue"] in [0, 1]
        agent.close()

    def test_one_hot_encode(self):
        """Test one-hot encoding."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "color": ["red", "blue", "red"],
        })

        encoded = agent.one_hot_encode(df, columns=["color"])

        # Should have more columns after one-hot encoding
        assert len(encoded.columns) > len(df.columns)
        agent.close()


class TestBinning:
    """Tests for feature binning."""

    def test_bin_features_basic(self):
        """Test basic feature binning."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        binned = agent.bin_features(df, column="value", n_bins=3)

        assert "value_binned" in binned.columns
        # Should have categorical data in binned column
        assert binned["value_binned"].dtype == pl.Categorical
        agent.close()

    def test_bin_features_five_bins(self):
        """Test binning with 5 bins."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": list(range(1, 101)),
        })

        binned = agent.bin_features(df, column="value", n_bins=5)

        assert "value_binned" in binned.columns
        agent.close()


class TestFeatureSelection:
    """Tests for feature selection."""

    def test_remove_low_variance_features(self):
        """Test removing low variance features."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "high_var": [1.0, 2.0, 3.0, 4.0, 5.0],
            "low_var": [1.0, 1.0, 1.0, 1.0, 1.0],  # No variance
        })

        filtered, removed = agent.remove_low_variance_features(
            df,
            threshold=0.1,
        )

        assert "low_var" in removed
        assert "low_var" not in filtered.columns
        assert "high_var" in filtered.columns
        agent.close()

    def test_low_variance_threshold_configuration(self):
        """Test configurable variance threshold."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1.0, 2.0, 3.0],
            "col2": [1.0, 1.1, 1.2],
        })

        # With high threshold, col2 should be removed
        filtered, removed = agent.remove_low_variance_features(
            df,
            threshold=0.05,
        )

        assert len(removed) > 0
        agent.close()


class TestFeatureStatistics:
    """Tests for feature statistics calculation."""

    def test_get_feature_statistics(self):
        """Test calculating feature statistics."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        stats = agent.get_feature_statistics(df)

        assert "x" in stats
        assert "mean" in stats["x"]
        assert "std" in stats["x"]
        assert "min" in stats["x"]
        assert "max" in stats["x"]
        agent.close()

    def test_feature_statistics_values(self):
        """Test accuracy of statistics."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        })

        stats = agent.get_feature_statistics(df)

        assert stats["value"]["mean"] == 3.0
        assert stats["value"]["min"] == 1.0
        assert stats["value"]["max"] == 5.0
        agent.close()

    def test_multiple_feature_statistics(self):
        """Test statistics for multiple features."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "a": [1.0, 2.0, 3.0],
            "b": [10.0, 20.0, 30.0],
        })

        stats = agent.get_feature_statistics(df)

        assert len(stats) == 2
        assert "a" in stats
        assert "b" in stats
        agent.close()


class TestFeatureCorrelations:
    """Tests for correlation analysis."""

    def test_get_feature_correlations(self):
        """Test correlation calculation."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0, 4.0, 5.0],
            "y": [2.0, 4.0, 6.0, 8.0, 10.0],  # Perfect correlation with x
        })

        corr = agent.get_feature_correlations(df)

        assert corr.shape[0] == 2
        assert corr.shape[1] == 2
        agent.close()

    def test_correlation_single_numeric_column(self):
        """Test with only one numeric column."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
        })

        corr = agent.get_feature_correlations(df)

        # Should return empty or minimal result
        assert corr.shape[0] == 0 or corr.shape[1] == 0
        agent.close()


class TestFullFeatureWorkflow:
    """Tests for complete workflows."""

    def test_execute_basic(self):
        """Test basic execute workflow."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
            "cat": ["A", "B", "C"],
        })

        results = agent.execute(df)

        assert results["feature_count"] == 2
        assert len(results["numeric_features"]) == 1
        assert len(results["categorical_features"]) == 1
        agent.close()

    def test_run_workflow_with_notebook(self):
        """Test run with notebook generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = FeatureEngineeringAgentModern("Test")
            agent.notebook_dir = Path(tmpdir)

            df = pl.DataFrame({
                "x": [1, 2, 3],
                "y": [10, 20, 30],
            })

            results = agent.run(df)

            assert results["status"] == "success"
            assert Path(results["notebook_path"]).exists()
            agent.close()

    def test_duckdb_persistence(self):
        """Test data persistence to DuckDB."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        })

        agent.execute(df)

        assert agent.db_manager.table_exists("feature_original_data")
        loaded = agent.load_from_duckdb("feature_original_data")
        assert loaded.shape == df.shape

        agent.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({"col": []})

        results = agent.execute(df)

        assert results["feature_count"] == 1
        agent.close()

    def test_single_row(self):
        """Test with single row."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0],
            "y": [2.0],
        })

        results = agent.execute(df)

        assert results["feature_count"] == 2
        agent.close()

    def test_all_numeric_columns(self):
        """Test with all numeric columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [4, 5, 6],
            "c": [7, 8, 9],
        })

        results = agent.execute(df)

        assert len(results["numeric_features"]) == 3
        assert len(results["categorical_features"]) == 0
        agent.close()

    def test_all_categorical_columns(self):
        """Test with all categorical columns."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "a": ["X", "Y", "Z"],
            "b": ["P", "Q", "R"],
        })

        results = agent.execute(df)

        assert len(results["numeric_features"]) == 0
        assert len(results["categorical_features"]) == 2
        agent.close()

    def test_scaling_with_nulls(self):
        """Test scaling with null values."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "value": [1.0, 2.0, None, 4.0],
        })

        scaled = agent.scale_features(df, columns=["value"], method="standardize")

        # Should still have scaled column (nulls handled by polars)
        assert "value_scaled" in scaled.columns
        agent.close()

    def test_interaction_with_single_column(self):
        """Test interaction with single column."""
        agent = FeatureEngineeringAgentModern("Test")
        df = pl.DataFrame({
            "x": [1.0, 2.0, 3.0],
        })

        interacted = agent.create_interaction_features(df, columns=["x"])

        # No interactions created with single column
        assert "x_x_x" not in interacted.columns
        agent.close()
