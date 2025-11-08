"""Unit tests for BaseAgentModern class.

Tests cover:
- Agent initialization and configuration
- Data processing and DuckDB persistence
- marimo notebook generation
- Error handling and edge cases
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from ai_data_science_team.agents.base_agent_modern import BaseAgentModern


class SimpleTestAgent(BaseAgentModern):
    """Simple concrete implementation for testing."""

    def execute(self, data):
        """Simple agent that sums numeric values."""
        if isinstance(data, dict):
            data = pl.DataFrame(data)
        elif not isinstance(data, pl.DataFrame):
            data = pl.from_arrow(data) if hasattr(data, 'to_pandas') else pl.DataFrame(data)

        numeric_cols = [col for col in data.columns if data[col].dtype in [pl.Int64, pl.Float64]]

        return {
            "input_shape": data.shape,
            "numeric_columns": numeric_cols,
            "row_count": data.height,
        }


class TestAgentInitialization:
    """Tests for agent initialization."""

    def test_agent_creation(self):
        """Test creating agent instance."""
        agent = SimpleTestAgent("TestAgent", "A test agent")

        assert agent.name == "TestAgent"
        assert agent.description == "A test agent"
        assert agent.db_manager is not None
        agent.close()

    def test_agent_with_file_db(self):
        """Test agent with file-based database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.duckdb"
            agent = SimpleTestAgent("Test", db_path=str(db_path))

            assert agent.db_manager.db_path == str(db_path)
            agent.close()

    def test_agent_config(self):
        """Test agent configuration."""
        agent = SimpleTestAgent("TestAgent")
        config = agent.get_config()

        assert config["name"] == "TestAgent"
        assert "created_at" in config
        agent.close()

    def test_agent_set_config(self):
        """Test setting agent configuration."""
        agent = SimpleTestAgent("Test")
        agent.set_config({"custom_key": "custom_value"})

        assert agent.config["custom_key"] == "custom_value"
        agent.close()


class TestAgentExecution:
    """Tests for agent execution."""

    def test_execute_with_dict_data(self):
        """Test executing agent with dict data."""
        agent = SimpleTestAgent("Test")
        data = {"col1": [1, 2, 3], "col2": [4, 5, 6]}

        results = agent.execute(data)

        assert "input_shape" in results
        assert results["row_count"] == 3
        agent.close()

    def test_execute_with_dataframe_data(self):
        """Test executing agent with DataFrame."""
        agent = SimpleTestAgent("Test")
        data = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0]
        })

        results = agent.execute(data)

        assert results["row_count"] == 3
        agent.close()

    def test_run_workflow(self):
        """Test full run workflow."""
        agent = SimpleTestAgent("Test")
        data = {"x": [1, 2, 3], "y": [4, 5, 6]}

        results = agent.run(data)

        assert results["status"] == "success"
        assert results["agent"] == "Test"
        assert "notebook_path" in results
        assert Path(results["notebook_path"]).exists()
        agent.close()

    def test_run_with_invalid_data(self):
        """Test run with invalid data."""
        agent = SimpleTestAgent("Test")

        results = agent.run(None)

        assert results["status"] == "error"
        agent.close()


class TestDuckDBIntegration:
    """Tests for DuckDB integration."""

    def test_persist_to_duckdb(self):
        """Test persisting data to DuckDB."""
        agent = SimpleTestAgent("Test")
        df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})

        agent.persist_to_duckdb("test_table", df)

        assert agent.db_manager.table_exists("test_table")
        agent.close()

    def test_load_from_duckdb(self):
        """Test loading data from DuckDB."""
        agent = SimpleTestAgent("Test")
        df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        agent.persist_to_duckdb("test_table", df)

        loaded_df = agent.load_from_duckdb("test_table")

        assert loaded_df.height == 3
        assert list(loaded_df.columns) == ["id", "value"]
        agent.close()

    def test_load_nonexistent_table(self):
        """Test loading nonexistent table raises error."""
        agent = SimpleTestAgent("Test")

        with pytest.raises(ValueError):
            agent.load_from_duckdb("nonexistent")

        agent.close()

    def test_query_duckdb(self):
        """Test querying DuckDB."""
        agent = SimpleTestAgent("Test")
        df = pl.DataFrame({"id": [1, 2, 3], "value": [10, 20, 30]})
        agent.persist_to_duckdb("test_table", df)

        result = agent.query_duckdb("SELECT * FROM test_table WHERE value > 15")

        assert result.height == 2
        agent.close()


class TestNotebookGeneration:
    """Tests for marimo notebook generation."""

    def test_setup_notebook(self):
        """Test notebook setup."""
        agent = SimpleTestAgent("Test", "Test description")
        notebook = agent.setup_notebook()

        assert notebook is not None
        assert "Test" in notebook.title
        agent.close()

    def test_custom_notebook_title(self):
        """Test custom notebook title."""
        agent = SimpleTestAgent("Test")
        notebook = agent.setup_notebook(title="Custom Title")

        assert "Custom Title" in notebook.title
        agent.close()

    def test_add_results_to_notebook(self):
        """Test adding results to notebook."""
        agent = SimpleTestAgent("Test")
        agent.setup_notebook()
        results = {"metric1": 42, "metric2": 3.14}

        agent.add_results_to_notebook(results)

        code = agent.notebook.get_marimo_code()
        assert "metric1" in code
        agent.close()

    def test_add_dataframe_results_to_notebook(self):
        """Test adding DataFrame results to notebook."""
        agent = SimpleTestAgent("Test")
        agent.setup_notebook()
        df = pl.DataFrame({"id": [1, 2], "value": [10, 20]})
        results = {"data": df}

        agent.add_results_to_notebook(results)

        code = agent.notebook.get_marimo_code()
        assert "data" in code
        agent.close()

    def test_generate_notebook(self):
        """Test generating notebook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = SimpleTestAgent("Test")
            agent.notebook_dir = Path(tmpdir)
            agent.results = {"metric": 42}

            notebook_path = agent.generate_notebook()

            assert notebook_path.exists()
            assert notebook_path.suffix == ".py"
            content = notebook_path.read_text()
            assert "Test" in content
            agent.close()

    def test_notebook_with_duckdb_data(self):
        """Test notebook includes DuckDB data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = SimpleTestAgent("Test")
            agent.notebook_dir = Path(tmpdir)

            # Persist data
            df = pl.DataFrame({"id": [1, 2, 3]})
            agent.persist_to_duckdb("results", df)

            # Generate notebook
            notebook_path = agent.generate_notebook()
            content = notebook_path.read_text()

            assert "results" in content
            agent.close()


class TestAgentRepr:
    """Tests for string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        agent = SimpleTestAgent("TestAgent")
        repr_str = repr(agent)

        assert "BaseAgentModern" in repr_str
        assert "TestAgent" in repr_str
        agent.close()


class TestAgentResourceManagement:
    """Tests for resource management."""

    def test_close(self):
        """Test closing agent."""
        agent = SimpleTestAgent("Test")
        agent.close()

    def test_context_manager_like_behavior(self):
        """Test agent can be used in try-finally."""
        agent = None
        try:
            agent = SimpleTestAgent("Test")
            data = {"x": [1, 2, 3]}
            agent.run(data)
        finally:
            if agent:
                agent.close()


class TestAgentErrorHandling:
    """Tests for error handling."""

    def test_execution_error_handling(self):
        """Test error handling during execution."""
        class BrokenAgent(BaseAgentModern):
            def execute(self, data):
                raise ValueError("Intentional error")

        agent = BrokenAgent("Broken")
        results = agent.run({"x": [1, 2, 3]})

        assert results["status"] == "error"
        assert "Intentional error" in results["error"]
        agent.close()

    def test_missing_notebook_dir(self):
        """Test handling missing notebook directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = SimpleTestAgent("Test")
            agent.notebook_dir = Path(tmpdir) / "deep" / "nested" / "dir"

            notebook_path = agent.generate_notebook()

            assert notebook_path.parent.exists()
            agent.close()


class TestAgentDataFormats:
    """Tests for various data format handling."""

    def test_with_mixed_column_types(self):
        """Test with mixed column types."""
        agent = SimpleTestAgent("Test")
        data = {
            "id": [1, 2, 3],
            "name": ["a", "b", "c"],
            "value": [10.5, 20.5, 30.5]
        }

        results = agent.execute(data)

        assert results["row_count"] == 3
        agent.close()

    def test_with_empty_dataframe(self):
        """Test with empty DataFrame."""
        agent = SimpleTestAgent("Test")
        data = pl.DataFrame({"col": []})

        results = agent.execute(data)

        assert results["row_count"] == 0
        agent.close()

    def test_persist_and_retrieve_cycle(self):
        """Test persist and retrieve cycle."""
        agent = SimpleTestAgent("Test")
        original_df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, 20.0, 30.0]
        })

        agent.persist_to_duckdb("data", original_df)
        loaded_df = agent.load_from_duckdb("data")

        assert loaded_df.equals(original_df)
        agent.close()


class TestAgentIntegration:
    """Integration tests combining multiple features."""

    def test_full_workflow(self):
        """Test full agent workflow with all features."""
        with tempfile.TemporaryDirectory() as tmpdir:
            agent = SimpleTestAgent(
                "TestAgent",
                "Integration test agent"
            )
            agent.notebook_dir = Path(tmpdir)

            data = {
                "id": [1, 2, 3, 4, 5],
                "value": [10, 20, 30, 40, 50]
            }
            results = agent.run(data)

            assert results["status"] == "success"
            assert Path(results["notebook_path"]).exists()

            notebook_content = Path(results["notebook_path"]).read_text()
            assert "TestAgent" in notebook_content
            assert "marimo" in notebook_content

            agent.close()

    def test_agent_with_multiple_tables(self):
        """Test agent managing multiple tables."""
        agent = SimpleTestAgent("Test")

        df1 = pl.DataFrame({"id": [1, 2], "data": ["a", "b"]})
        df2 = pl.DataFrame({"id": [3, 4], "data": ["c", "d"]})

        agent.persist_to_duckdb("table1", df1)
        agent.persist_to_duckdb("table2", df2)

        tables = agent.db_manager.list_tables()
        assert "table1" in tables
        assert "table2" in tables

        agent.close()
