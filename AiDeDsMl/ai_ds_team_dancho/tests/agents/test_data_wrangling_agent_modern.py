"""Unit tests for DataWranglingAgentModern.

Tests cover:
- Pivot and unpivot operations
- Group by and aggregation
- Join operations
- Filtering and selection
- Sorting and renaming
- Data transformation workflows
"""

import tempfile
from pathlib import Path

import polars as pl
import pytest

from ai_data_science_team.agents.data_wrangling_agent_modern import (
    DataWranglingAgentModern,
)


class TestWranglingAgentInitialization:
    """Tests for agent initialization."""

    def test_agent_creation(self):
        """Test creating wrangling agent."""
        agent = DataWranglingAgentModern("Wrangler")

        assert agent.name == "Wrangler"
        agent.close()

    def test_agent_with_custom_db_path(self):
        """Test creating agent with custom database path."""
        agent = DataWranglingAgentModern("Wrangler", db_path=":memory:")

        assert agent.name == "Wrangler"
        agent.close()


class TestPivotOperations:
    """Tests for pivot transformations."""

    def test_pivot_basic(self):
        """Test basic pivot operation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B", "A", "B"],
            "category": ["X", "X", "Y", "Y"],
            "value": [1, 2, 3, 4],
        })

        pivoted = agent.pivot(df, index="group", columns="category", values="value")

        assert pivoted.shape[0] == 2  # 2 groups
        assert "X" in pivoted.columns
        assert "Y" in pivoted.columns
        agent.close()

    def test_pivot_with_aggregation(self):
        """Test pivot with sum aggregation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "A", "B"],
            "category": ["X", "X", "X"],
            "value": [1, 2, 3],
        })

        pivoted = agent.pivot(
            df,
            index="group",
            columns="category",
            values="value",
            aggregate_function="sum",
        )

        assert pivoted.shape[0] == 2
        agent.close()

    def test_pivot_mean_aggregation(self):
        """Test pivot with mean aggregation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "A", "B"],
            "category": ["X", "X", "X"],
            "value": [10.0, 20.0, 30.0],
        })

        pivoted = agent.pivot(
            df,
            index="group",
            columns="category",
            values="value",
            aggregate_function="mean",
        )

        assert pivoted.shape[0] == 2
        agent.close()


class TestUnpivotOperations:
    """Tests for unpivot transformations."""

    def test_unpivot_basic(self):
        """Test basic unpivot operation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "id": [1, 2],
            "X": [10, 20],
            "Y": [30, 40],
        })

        unpivoted = agent.unpivot(
            df,
            index="id",
            variable_name="category",
            value_name="value",
        )

        assert unpivoted.shape[0] == 4  # 2 rows × 2 variables
        assert "category" in unpivoted.columns
        assert "value" in unpivoted.columns
        agent.close()

    def test_unpivot_multiple_index(self):
        """Test unpivot with multiple index columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "id1": [1, 2],
            "id2": ["A", "B"],
            "X": [10, 20],
            "Y": [30, 40],
        })

        unpivoted = agent.unpivot(
            df,
            index=["id1", "id2"],
            variable_name="metric",
            value_name="val",
        )

        assert unpivoted.shape[0] == 4
        assert "metric" in unpivoted.columns
        agent.close()


class TestGroupAndAggregate:
    """Tests for grouping and aggregation."""

    def test_group_by_sum(self):
        """Test grouping with sum aggregation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1, 2, 3, 4],
        })

        agg = agent.group_and_aggregate(
            df,
            group_by="group",
            aggregations={"value": "sum"},
        )

        assert agg.shape[0] == 2
        assert "value_sum" in agg.columns
        agent.close()

    def test_group_by_multiple_functions(self):
        """Test grouping with multiple aggregation functions."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "A", "B", "B"],
            "value": [1.0, 3.0, 2.0, 4.0],
        })

        agg = agent.group_and_aggregate(
            df,
            group_by="group",
            aggregations={"value": ["sum", "mean"]},
        )

        assert agg.shape[0] == 2
        assert "value_sum" in agg.columns
        assert "value_mean" in agg.columns
        agent.close()

    def test_group_by_multiple_columns(self):
        """Test grouping by multiple columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group1": ["A", "A", "B"],
            "group2": ["X", "Y", "X"],
            "value": [1, 2, 3],
        })

        agg = agent.group_and_aggregate(
            df,
            group_by=["group1", "group2"],
            aggregations={"value": "sum"},
        )

        assert agg.shape[0] == 3
        agent.close()

    def test_group_by_count(self):
        """Test grouping with count aggregation."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "A", "B"],
            "value": [1, 2, 3],
        })

        agg = agent.group_and_aggregate(
            df,
            group_by="group",
            aggregations={"value": "count"},
        )

        assert "value_count" in agg.columns
        agent.close()


class TestJoinOperations:
    """Tests for join operations."""

    def test_inner_join(self):
        """Test inner join operation."""
        agent = DataWranglingAgentModern("Test")
        left = pl.DataFrame({
            "id": [1, 2, 3],
            "left_val": ["A", "B", "C"],
        })
        right = pl.DataFrame({
            "id": [2, 3, 4],
            "right_val": ["X", "Y", "Z"],
        })

        joined = agent.join_data(left, right, left_on="id", right_on="id", how="inner")

        assert joined.shape[0] == 2  # Only rows with ids 2 and 3
        assert "left_val" in joined.columns
        assert "right_val" in joined.columns
        agent.close()

    def test_left_join(self):
        """Test left join operation."""
        agent = DataWranglingAgentModern("Test")
        left = pl.DataFrame({
            "id": [1, 2, 3],
            "left_val": ["A", "B", "C"],
        })
        right = pl.DataFrame({
            "id": [2, 3, 4],
            "right_val": ["X", "Y", "Z"],
        })

        joined = agent.join_data(left, right, left_on="id", right_on="id", how="left")

        assert joined.shape[0] == 3  # All rows from left
        agent.close()

    def test_outer_join(self):
        """Test outer join operation."""
        agent = DataWranglingAgentModern("Test")
        left = pl.DataFrame({
            "id": [1, 2],
            "left_val": ["A", "B"],
        })
        right = pl.DataFrame({
            "id": [2, 3],
            "right_val": ["X", "Y"],
        })

        joined = agent.join_data(left, right, left_on="id", right_on="id", how="outer")

        assert joined.shape[0] == 3  # All unique ids
        agent.close()


class TestFilterOperations:
    """Tests for filtering rows."""

    def test_filter_single_condition(self):
        """Test filtering with single condition."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B", "A"],
            "value": [1, 2, 3],
        })

        filtered = agent.filter_rows(df, conditions={"group": "A"})

        assert filtered.shape[0] == 2
        agent.close()

    def test_filter_multiple_conditions(self):
        """Test filtering with multiple conditions."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B", "A"],
            "status": ["active", "active", "inactive"],
        })

        filtered = agent.filter_rows(
            df,
            conditions={"group": "A", "status": "active"},
        )

        assert filtered.shape[0] == 1
        agent.close()

    def test_filter_with_list_values(self):
        """Test filtering with list of values."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B", "C"],
            "value": [1, 2, 3],
        })

        filtered = agent.filter_rows(df, conditions={"group": ["A", "B"]})

        assert filtered.shape[0] == 2
        agent.close()


class TestSelectAndDropColumns:
    """Tests for column selection and removal."""

    def test_select_single_column(self):
        """Test selecting a single column."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
        })

        selected = agent.select_columns(df, columns="col1")

        assert selected.shape[1] == 1
        assert "col1" in selected.columns
        agent.close()

    def test_select_multiple_columns(self):
        """Test selecting multiple columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
            "col3": [7, 8, 9],
        })

        selected = agent.select_columns(df, columns=["col1", "col3"])

        assert selected.shape[1] == 2
        assert "col1" in selected.columns
        assert "col3" in selected.columns
        assert "col2" not in selected.columns
        agent.close()

    def test_drop_column(self):
        """Test dropping a column."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
        })

        dropped = agent.drop_columns(df, columns="col2")

        assert dropped.shape[1] == 1
        assert "col1" in dropped.columns
        assert "col2" not in dropped.columns
        agent.close()

    def test_drop_multiple_columns(self):
        """Test dropping multiple columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
            "col3": [7, 8, 9],
        })

        dropped = agent.drop_columns(df, columns=["col2", "col3"])

        assert dropped.shape[1] == 1
        assert "col1" in dropped.columns
        agent.close()


class TestSortOperations:
    """Tests for sorting data."""

    def test_sort_ascending(self):
        """Test sorting in ascending order."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "id": [3, 1, 2],
            "value": [30, 10, 20],
        })

        sorted_df = agent.sort_data(df, by="id", descending=False)

        assert sorted_df["id"].to_list() == [1, 2, 3]
        agent.close()

    def test_sort_descending(self):
        """Test sorting in descending order."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "id": [3, 1, 2],
            "value": [30, 10, 20],
        })

        sorted_df = agent.sort_data(df, by="id", descending=True)

        assert sorted_df["id"].to_list() == [3, 2, 1]
        agent.close()

    def test_sort_multiple_columns(self):
        """Test sorting by multiple columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["B", "A", "A"],
            "value": [1, 3, 2],
        })

        sorted_df = agent.sort_data(df, by=["group", "value"], descending=False)

        assert sorted_df["group"].to_list() == ["A", "A", "B"]
        assert sorted_df["value"].to_list() == [2, 3, 1]
        agent.close()


class TestRenameColumns:
    """Tests for renaming columns."""

    def test_rename_single_column(self):
        """Test renaming a single column."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "old_name": [1, 2, 3],
        })

        renamed = agent.rename_columns(df, mapping={"old_name": "new_name"})

        assert "new_name" in renamed.columns
        assert "old_name" not in renamed.columns
        agent.close()

    def test_rename_multiple_columns(self):
        """Test renaming multiple columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2, 3],
            "col2": [4, 5, 6],
        })

        renamed = agent.rename_columns(df, mapping={"col1": "a", "col2": "b"})

        assert "a" in renamed.columns
        assert "b" in renamed.columns
        assert "col1" not in renamed.columns
        agent.close()


class TestUniqueValues:
    """Tests for unique value extraction."""

    def test_get_unique_values(self):
        """Test extracting unique values."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B", "A", "C"],
        })

        unique = agent.get_unique_values(df, column="group")

        assert len(unique) == 3
        assert "A" in unique
        assert "B" in unique
        assert "C" in unique
        agent.close()

    def test_unique_values_numeric(self):
        """Test unique values with numeric column."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "value": [1, 2, 1, 3, 2],
        })

        unique = agent.get_unique_values(df, column="value")

        assert len(unique) == 3
        agent.close()


class TestFullWranglingWorkflow:
    """Tests for complete workflows."""

    def test_execute_basic(self):
        """Test basic execute workflow."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30],
        })

        results = agent.execute(df)

        assert results["original_shape"] == (3, 2)
        assert results["final_shape"] == (3, 2)
        assert len(results["columns"]) == 2
        agent.close()

    def test_run_workflow_with_notebook(self):
        """Test run with notebook generation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = DataWranglingAgentModern("Test")
            agent.notebook_dir = Path(tmpdir)

            df = pl.DataFrame({
                "group": ["A", "B"],
                "value": [1, 2],
            })

            results = agent.run(df)

            assert results["status"] == "success"
            assert Path(results["notebook_path"]).exists()
            agent.close()

    def test_duckdb_persistence(self):
        """Test data persistence to DuckDB."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "a": [1, 2, 3],
            "b": [10, 20, 30],
        })

        agent.execute(df)

        assert agent.db_manager.table_exists("original_wrangling_data")
        loaded = agent.load_from_duckdb("original_wrangling_data")
        assert loaded.shape == df.shape

        agent.close()


class TestEdgeCases:
    """Tests for edge cases."""

    def test_empty_dataframe(self):
        """Test with empty DataFrame."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({"col": []})

        results = agent.execute(df)

        assert results["final_shape"][0] == 0
        agent.close()

    def test_single_row(self):
        """Test with single row."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({"col": [1]})

        results = agent.execute(df)

        assert results["final_shape"] == (1, 1)
        agent.close()

    def test_single_column(self):
        """Test with single column."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({"col": [1, 2, 3]})

        results = agent.execute(df)

        assert results["final_shape"][1] == 1
        agent.close()

    def test_filter_empty_result(self):
        """Test filtering that returns empty result."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "group": ["A", "B"],
            "value": [1, 2],
        })

        filtered = agent.filter_rows(df, conditions={"group": "C"})

        assert filtered.shape[0] == 0
        agent.close()

    def test_select_all_columns(self):
        """Test selecting all columns."""
        agent = DataWranglingAgentModern("Test")
        df = pl.DataFrame({
            "col1": [1, 2],
            "col2": [3, 4],
        })

        selected = agent.select_columns(df, columns=["col1", "col2"])

        assert selected.shape == df.shape
        agent.close()
