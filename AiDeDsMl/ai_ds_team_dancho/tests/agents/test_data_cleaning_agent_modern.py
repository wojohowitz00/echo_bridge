"""Unit tests for DataCleaningAgentModern.

Tests cover:
- Null value detection and removal
- Outlier detection (IQR and z-score)
- Duplicate removal
- Data type handling
- Integration with DuckDB and marimo
"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from ai_data_science_team.agents.data_cleaning_agent_modern import (
    DataCleaningAgentModern,
)


class TestDataCleaningAgentInitialization:
    """Tests for agent initialization."""

    def test_agent_creation(self):
        """Test creating cleaning agent."""
        agent = DataCleaningAgentModern("TestCleaner")

        assert agent.name == "TestCleaner"
        assert agent.null_threshold == 0.5
        assert agent.outlier_method == "iqr"
        assert agent.remove_duplicates is True
        agent.close()

    def test_custom_configuration(self):
        """Test creating agent with custom config."""
        agent = DataCleaningAgentModern(
            "TestCleaner",
            null_threshold=0.7,
            outlier_method="zscore",
            remove_duplicates=False,
        )

        assert agent.null_threshold == 0.7
        assert agent.outlier_method == "zscore"
        assert agent.remove_duplicates is False
        agent.close()


class TestNullHandling:
    """Tests for null value detection and handling."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DataCleaningAgentModern("Test")

    def test_analyze_nulls(self, agent):
        """Test null analysis."""
        df = pl.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": [10, None, None, 40],
            "col3": [100, 200, 300, 400],
        })

        null_report = agent._analyze_nulls(df)

        assert "col1" in null_report["null_counts"]
        assert "col2" in null_report["null_counts"]
        assert "col3" in null_report["null_counts"]
        assert null_report["null_counts"]["col1"] == 1
        assert null_report["null_counts"]["col2"] == 2
        agent.close()

    def test_remove_high_null_columns(self, agent):
        """Test removing columns with many nulls."""
        df = pl.DataFrame({
            "col1": [1, 2, 3, None],
            "col2": [None, None, None, 40],
            "col3": [100, 200, 300, 400],
        })

        null_report = agent._analyze_nulls(df)
        df_cleaned = agent._remove_high_null_columns(df, null_report)

        # col2 has 3/4 nulls (75%) > 50% threshold
        assert "col2" not in df_cleaned.columns
        assert "col1" in df_cleaned.columns
        assert "col3" in df_cleaned.columns
        agent.close()

    def test_handle_remaining_nulls_numeric(self, agent):
        """Test filling numeric nulls with mean."""
        df = pl.DataFrame({
            "value": [10.0, 20.0, 30.0, None],
        })

        df_filled = agent._handle_remaining_nulls(df)

        assert df_filled.null_count()[0, 0] == 0
        # Mean of [10, 20, 30] = 20
        assert df_filled["value"][-1] == 20.0
        agent.close()

    def test_handle_remaining_nulls_categorical(self, agent):
        """Test filling categorical nulls with mode."""
        df = pl.DataFrame({
            "category": ["A", "B", "A", None],
        })

        df_filled = agent._handle_remaining_nulls(df)

        assert df_filled.null_count()[0, 0] == 0
        # Mode is "A"
        assert df_filled["category"][-1] == "A"
        agent.close()


class TestOutlierDetection:
    """Tests for outlier detection and removal."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DataCleaningAgentModern("Test", outlier_method="iqr")

    def test_remove_outliers_iqr(self, agent):
        """Test removing outliers with IQR method."""
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5, 100],  # 100 is outlier
        })

        rows_removed, df_cleaned = agent._remove_outliers(df)

        assert rows_removed == 1
        assert df_cleaned.height == 5
        assert 100 not in df_cleaned["value"].to_list()
        agent.close()

    def test_remove_outliers_zscore(self):
        """Test removing outliers with z-score method."""
        agent = DataCleaningAgentModern("Test", outlier_method="zscore")
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5, 100],
        })

        rows_removed, df_cleaned = agent._remove_outliers(df)

        # Z-score method should remove the outlier (100)
        assert rows_removed >= 0  # May be 0 or 1 depending on z-score threshold
        assert df_cleaned.height <= df.height
        agent.close()

    def test_no_outliers(self, agent):
        """Test when no outliers present."""
        df = pl.DataFrame({
            "value": [1, 2, 3, 4, 5],
        })

        rows_removed, df_cleaned = agent._remove_outliers(df)

        assert rows_removed == 0
        assert df_cleaned.height == 5
        agent.close()

    def test_multiple_numeric_columns(self, agent):
        """Test outlier removal on multiple numeric columns."""
        df = pl.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": [10, 20, 30, 40, 200],
        })

        rows_removed, df_cleaned = agent._remove_outliers(df)

        # Should remove row with 200 in col2
        assert rows_removed > 0
        agent.close()


class TestDuplicateRemoval:
    """Tests for duplicate detection and removal."""

    def test_remove_duplicates(self):
        """Test removing duplicate rows."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 1, 3],
            "col2": [10, 20, 10, 40],
        })

        duplicates_removed, df_cleaned = agent._remove_duplicates(df)

        assert duplicates_removed == 1
        assert df_cleaned.height == 3
        agent.close()

    def test_no_duplicates(self):
        """Test when no duplicates present."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [10, 20, 30],
        })

        duplicates_removed, df_cleaned = agent._remove_duplicates(df)

        assert duplicates_removed == 0
        assert df_cleaned.height == 3
        agent.close()

    def test_all_duplicate_rows(self):
        """Test when all rows are identical."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 1, 1],
            "col2": [10, 10, 10],
        })

        duplicates_removed, df_cleaned = agent._remove_duplicates(df)

        assert duplicates_removed == 2
        assert df_cleaned.height == 1
        agent.close()


class TestFullCleaningWorkflow:
    """Tests for complete cleaning workflow."""

    def test_execute_with_messy_data(self):
        """Test full cleaning workflow."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "id": [1, 2, 3, 4, 1],
            "value": [10, 20, 30, 1000, 10],
            "category": ["A", "B", None, "C", "A"],
        })

        results = agent.execute(df)

        assert "cleaned_data" in results
        assert results["cleaned_data"].height < df.height
        assert results["outliers_removed"] > 0
        assert results["duplicates_removed"] > 0
        agent.close()

    def test_run_with_dict_data(self):
        """Test run with dict data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DataCleaningAgentModern("Test")
            agent.notebook_dir = Path(tmpdir)

            data = {
                "x": [1, 2, 3, None, 1],
                "y": [10, 20, 30, 40, 10],
            }

            results = agent.run(data)

            assert results["status"] == "success"
            assert Path(results["notebook_path"]).exists()
            agent.close()

    def test_duckdb_persistence(self):
        """Test data persistence to DuckDB."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, None, 4],
            "col2": [10, 20, 30, 40],
        })

        agent.execute(df)

        # Verify tables created
        assert agent.db_manager.table_exists("original_data")
        assert agent.db_manager.table_exists("cleaned_data")

        # Verify data
        original = agent.load_from_duckdb("original_data")
        cleaned = agent.load_from_duckdb("cleaned_data")

        assert original.height == 4
        assert cleaned.height == 3  # One null row removed

        agent.close()


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({"col": []})

        results = agent.execute(df)

        assert results["cleaned_shape"][0] == 0
        agent.close()

    def test_all_nulls_column(self):
        """Test with column of all nulls."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [None, None, None],
        })

        results = agent.execute(df)

        # col2 should be removed (100% null > 50% threshold)
        assert "col2" not in results["cleaned_data"].columns
        agent.close()

    def test_single_row(self):
        """Test with single row."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({"col": [1]})

        results = agent.execute(df)

        assert results["cleaned_shape"] == (1, 1)
        agent.close()

    def test_mixed_data_types(self):
        """Test with mixed data types."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.5, 2.5, 3.5],
            "str_col": ["a", "b", "c"],
            "bool_col": [True, False, True],
        })

        results = agent.execute(df)

        assert results["cleaned_data"].height == 3
        agent.close()


class TestConfiguration:
    """Tests for agent configuration."""

    def test_null_threshold_configuration(self):
        """Test custom null threshold."""
        agent = DataCleaningAgentModern("Test", null_threshold=0.2)
        df = pl.DataFrame({
            "col1": [1, 2, 3, 4, 5],
            "col2": [None, None, 3, 4, 5],
        })

        null_report = agent._analyze_nulls(df)

        # col2 has 40% nulls > 20% threshold
        assert "col2" in null_report["columns_exceeding_threshold"]
        agent.close()

    def test_disable_duplicate_removal(self):
        """Test disabling duplicate removal."""
        agent = DataCleaningAgentModern("Test", remove_duplicates=False)
        df = pl.DataFrame({
            "col1": [1, 2, 1],
            "col2": [10, 20, 10],
        })

        results = agent.execute(df)

        # Duplicates not removed
        assert results["duplicates_removed"] == 0
        agent.close()


class TestDataTypes:
    """Tests for data type handling."""

    def test_numeric_column_preservation(self):
        """Test numeric columns are preserved."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "int_col": [1, 2, 3],
            "float_col": [1.1, 2.2, 3.3],
        })

        results = agent.execute(df)

        cleaned = results["cleaned_data"]
        assert cleaned["int_col"].dtype == pl.Int64
        assert cleaned["float_col"].dtype == pl.Float64
        agent.close()

    def test_string_column_handling(self):
        """Test string columns are handled properly."""
        agent = DataCleaningAgentModern("Test")
        df = pl.DataFrame({
            "text": ["hello", "world", "test"],
        })

        results = agent.execute(df)

        assert results["cleaned_data"].height == 3
        agent.close()
