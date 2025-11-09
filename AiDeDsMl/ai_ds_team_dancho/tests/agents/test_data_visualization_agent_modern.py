"""Unit tests for DataVisualizationAgentModern.

Tests cover:
- Column analysis
- Chart recommendations
- Data visualization workflow
- marimo notebook generation
"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from ai_data_science_team.agents.data_visualization_agent_modern import (
    DataVisualizationAgentModern,
)


class TestVisualizationAgentInitialization:
    """Tests for agent initialization."""

    def test_agent_creation(self):
        """Test creating visualization agent."""
        agent = DataVisualizationAgentModern("Visualizer")

        assert agent.name == "Visualizer"
        assert agent.max_dimensions == 20
        agent.close()


class TestColumnAnalysis:
    """Tests for column analysis."""

    def test_analyze_numeric_columns(self):
        """Test analyzing numeric columns."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "x": [1, 2, 3, 4, 5],
            "y": [10.0, 20.0, 30.0, 40.0, 50.0],
        })

        columns_info = agent._analyze_columns(df)

        assert "x" in columns_info["numeric"]
        assert "y" in columns_info["numeric"]
        assert len(columns_info["numeric"]) == 2
        agent.close()

    def test_analyze_categorical_columns(self):
        """Test analyzing categorical columns."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "category": ["A", "B", "C"],
            "status": ["active", "inactive", "active"],
        })

        columns_info = agent._analyze_columns(df)

        assert "category" in columns_info["categorical"]
        assert "status" in columns_info["categorical"]
        agent.close()

    def test_analyze_mixed_columns(self):
        """Test analyzing mixed column types."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.5, 20.5, 30.5],
            "name": ["A", "B", "C"],
        })

        columns_info = agent._analyze_columns(df)

        assert len(columns_info["numeric"]) == 2
        assert len(columns_info["categorical"]) == 1
        agent.close()


class TestChartRecommendations:
    """Tests for chart recommendations."""

    def test_recommendations_numeric_only(self):
        """Test recommendations with numeric data."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "x": [1, 2, 3],
            "y": [10, 20, 30],
        })
        columns_info = agent._analyze_columns(df)

        recommendations = agent._generate_recommendations(df, columns_info)

        assert "univariate" in recommendations
        assert "bivariate" in recommendations
        assert len(recommendations["bivariate"]) > 0
        agent.close()

    def test_recommendations_categorical_only(self):
        """Test recommendations with categorical data."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "type": ["A", "B", "C"],
            "group": ["X", "Y", "Z"],
        })
        columns_info = agent._analyze_columns(df)

        recommendations = agent._generate_recommendations(df, columns_info)

        assert "univariate" in recommendations
        assert len(recommendations["univariate"]) == 2
        agent.close()

    def test_correlation_recommendations(self):
        """Test correlation recommendations."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "a": [1, 2, 3, 4, 5],
            "b": [5, 4, 3, 2, 1],
            "c": [2, 4, 6, 8, 10],
        })
        columns_info = agent._analyze_columns(df)

        recommendations = agent._generate_recommendations(df, columns_info)

        assert "correlation" in recommendations
        assert len(recommendations["correlation"]) > 0
        agent.close()


class TestFullVisualizationWorkflow:
    """Tests for complete visualization workflow."""

    def test_execute_workflow(self):
        """Test full visualization workflow."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10.0, 20.0, 30.0, 40.0, 50.0],
            "category": ["A", "B", "A", "C", "B"],
        })

        results = agent.execute(df)

        assert results["shape"] == (5, 3)
        assert len(results["numeric_columns"]) == 2
        assert len(results["categorical_columns"]) == 1
        agent.close()

    def test_run_workflow(self):
        """Test run with notebook generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DataVisualizationAgentModern("Test")
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
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        })

        agent.execute(df)

        assert agent.db_manager.table_exists("visualization_data")
        loaded = agent.load_from_duckdb("visualization_data")
        assert loaded.shape == df.shape

        agent.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_single_column(self):
        """Test with single column."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({"col": [1, 2, 3]})

        results = agent.execute(df)

        assert results["shape"] == (3, 1)
        agent.close()

    def test_with_nulls(self):
        """Test handling null values."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": ["A", None, "C", "D"],
        })

        columns_info = agent._analyze_columns(df)

        assert columns_info["all"]["col1"]["null_count"] == 1
        assert columns_info["all"]["col2"]["null_count"] == 1
        agent.close()

    def test_single_value_column(self):
        """Test with column of identical values."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({"const": [5, 5, 5, 5]})

        results = agent.execute(df)

        assert results["shape"][0] == 4
        agent.close()


class TestStatistics:
    """Tests for statistical analysis."""

    def test_numeric_statistics(self):
        """Test numeric column statistics."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({"values": [1.0, 2.0, 3.0, 4.0, 5.0]})

        columns_info = agent._analyze_columns(df)
        col_info = columns_info["all"]["values"]

        assert col_info["min"] == 1.0
        assert col_info["max"] == 5.0
        assert col_info["mean"] == 3.0
        agent.close()

    def test_categorical_unique_count(self):
        """Test categorical unique count."""
        agent = DataVisualizationAgentModern("Test")
        df = pl.DataFrame({"categories": ["A", "B", "A", "C"]})

        columns_info = agent._analyze_columns(df)
        col_info = columns_info["all"]["categories"]

        assert col_info["unique_count"] == 3
        agent.close()
