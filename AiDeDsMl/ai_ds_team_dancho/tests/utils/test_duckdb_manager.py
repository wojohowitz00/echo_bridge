"""Unit tests for DuckDBManager.

Tests cover:
- Table creation and management
- CRUD operations
- SQL queries and aggregations
- Schema introspection
- Error handling
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import duckdb
import polars as pl
import pytest

from ai_data_science_team.utils.duckdb_manager import DuckDBManager


class TestDuckDBManagerInitialization:
    """Tests for DuckDBManager initialization."""

    def test_memory_database_creation(self):
        """Test creating in-memory database."""
        manager = DuckDBManager(":memory:")
        assert manager.db_path == ":memory:"
        assert manager.connection is not None
        assert isinstance(manager.metadata, dict)
        manager.close()

    def test_file_database_creation(self):
        """Test creating file-based database."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.duckdb")
            manager = DuckDBManager(db_path)
            assert manager.db_path == db_path
            assert os.path.exists(db_path)
            manager.close()

    def test_default_database_path(self):
        """Test default database path."""
        with patch('duckdb.connect'):
            with tempfile.TemporaryDirectory() as tmpdir:
                os.chdir(tmpdir)
                manager = DuckDBManager()
                assert manager.db_path == "data.duckdb"
                manager.close()


class TestTableCreation:
    """Tests for table creation operations."""

    @pytest.fixture
    def manager(self):
        """Create in-memory DuckDB manager for testing."""
        mgr = DuckDBManager(":memory:")
        yield mgr
        mgr.close()

    def test_create_table_from_polars_dataframe(self, manager):
        """Test creating table from polars DataFrame."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "name": ["Alice", "Bob", "Charlie"],
            "value": [10.5, 20.3, 15.8]
        })
        manager.create_table("users", df)

        assert manager.table_exists("users")
        assert len(manager.metadata["users"]["columns"]) == 3
        assert manager.metadata["users"]["row_count"] == 3

    def test_create_table_from_dict(self, manager):
        """Test creating table from dictionary."""
        data = {
            "id": [1, 2, 3],
            "value": [100, 200, 300]
        }
        manager.create_table("metrics", data)

        assert manager.table_exists("metrics")
        result = manager.read_table("metrics")
        assert result.height == 3

    def test_create_table_from_list(self, manager):
        """Test creating table from list of dictionaries."""
        data = [
            {"id": 1, "status": "active"},
            {"id": 2, "status": "inactive"}
        ]
        manager.create_table("events", data)

        assert manager.table_exists("events")
        result = manager.read_table("events")
        assert result.height == 2

    def test_create_table_duplicate_error(self, manager):
        """Test error when creating duplicate table."""
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)

        with pytest.raises(ValueError, match="already exists"):
            manager.create_table("test", df)

    def test_create_table_replace(self, manager):
        """Test replacing existing table."""
        df1 = pl.DataFrame({"id": [1, 2]})
        df2 = pl.DataFrame({"id": [10, 20, 30]})

        manager.create_table("test", df1)
        assert manager._get_row_count("test") == 2

        manager.create_table("test", df2, replace=True)
        assert manager._get_row_count("test") == 3


class TestCRUDOperations:
    """Tests for Create, Read, Update, Delete operations."""

    @pytest.fixture
    def manager_with_data(self):
        """Create manager with sample data."""
        mgr = DuckDBManager(":memory:")
        df = pl.DataFrame({
            "id": [1, 2, 3, 4],
            "name": ["Alice", "Bob", "Charlie", "David"],
            "score": [85.5, 92.0, 78.5, 88.0]
        })
        mgr.create_table("students", df)
        yield mgr
        mgr.close()

    def test_read_table(self, manager_with_data):
        """Test reading entire table."""
        result = manager_with_data.read_table("students")

        assert isinstance(result, pl.DataFrame)
        assert result.height == 4
        assert list(result.columns) == ["id", "name", "score"]

    def test_read_nonexistent_table(self, manager_with_data):
        """Test error reading nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager_with_data.read_table("nonexistent")

    def test_insert_data_single_row(self, manager_with_data):
        """Test inserting single row."""
        rows_inserted = manager_with_data.insert_data(
            "students",
            {"id": 5, "name": "Eve", "score": 95.0}
        )

        assert rows_inserted == 1
        assert manager_with_data._get_row_count("students") == 5

    def test_insert_data_multiple_rows(self, manager_with_data):
        """Test inserting multiple rows."""
        df_new = pl.DataFrame({
            "id": [5, 6],
            "name": ["Eve", "Frank"],
            "score": [95.0, 81.5]
        })
        rows_inserted = manager_with_data.insert_data("students", df_new)

        assert rows_inserted == 2
        assert manager_with_data._get_row_count("students") == 6

    def test_insert_into_nonexistent_table(self, manager_with_data):
        """Test error inserting into nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager_with_data.insert_data("nonexistent", {"id": 1})

    def test_update_rows(self, manager_with_data):
        """Test updating rows."""
        manager_with_data.update_rows(
            "students",
            "id = 1",
            {"score": 90.0}
        )

        result = manager_with_data.query(
            "SELECT score FROM students WHERE id = 1"
        )
        assert result["score"][0] == 90.0

    def test_update_multiple_rows(self, manager_with_data):
        """Test updating multiple rows."""
        manager_with_data.update_rows(
            "students",
            "score < 80",
            {"score": 80.0}
        )

        result = manager_with_data.query(
            "SELECT COUNT(*) as count FROM students WHERE score < 80"
        )
        assert result["count"][0] == 0

    def test_delete_rows(self, manager_with_data):
        """Test deleting rows."""
        initial_count = manager_with_data._get_row_count("students")
        remaining = manager_with_data.delete_rows("students", "id = 1")

        assert remaining == initial_count - 1
        result = manager_with_data.query("SELECT * FROM students WHERE id = 1")
        assert result.height == 0

    def test_delete_nonexistent_table(self, manager_with_data):
        """Test error deleting from nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager_with_data.delete_rows("nonexistent", "id = 1")


class TestQueries:
    """Tests for SQL query operations."""

    @pytest.fixture
    def manager_with_data(self):
        """Create manager with sample data."""
        mgr = DuckDBManager(":memory:")
        df = pl.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "category": ["A", "B", "A", "B", "A"],
            "value": [100, 200, 150, 250, 175]
        })
        mgr.create_table("data", df)
        yield mgr
        mgr.close()

    def test_simple_query(self, manager_with_data):
        """Test simple SELECT query."""
        result = manager_with_data.query("SELECT * FROM data")

        assert result.height == 5
        assert result.width == 3

    def test_query_with_where_clause(self, manager_with_data):
        """Test query with WHERE clause."""
        result = manager_with_data.query(
            "SELECT * FROM data WHERE value > 150"
        )

        assert result.height == 3
        values = sorted(result["value"].to_list())
        assert values == [175, 200, 250]

    def test_query_with_aggregation(self, manager_with_data):
        """Test query with aggregation."""
        result = manager_with_data.query(
            "SELECT category, COUNT(*) as count FROM data GROUP BY category"
        )

        assert result.height == 2
        assert result["count"].sum() == 5

    def test_aggregation_method(self, manager_with_data):
        """Test aggregation method."""
        result = manager_with_data.aggregation(
            "data",
            group_by=["category"],
            agg={"value": "SUM", "id": "COUNT"}
        )

        assert result.height == 2
        assert "value_sum" in result.columns
        assert "id_count" in result.columns

    def test_aggregation_without_group_by(self, manager_with_data):
        """Test aggregation without GROUP BY."""
        result = manager_with_data.aggregation(
            "data",
            agg={"value": "AVG", "id": "COUNT"}
        )

        assert result.height == 1

    def test_aggregation_invalid_table(self, manager_with_data):
        """Test aggregation on nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager_with_data.aggregation(
                "nonexistent",
                agg={"value": "SUM"}
            )

    def test_aggregation_empty_agg(self, manager_with_data):
        """Test aggregation with empty agg dict."""
        with pytest.raises(ValueError, match="cannot be empty"):
            manager_with_data.aggregation("data", agg={})


class TestTableManagement:
    """Tests for table management operations."""

    @pytest.fixture
    def manager(self):
        """Create in-memory DuckDB manager for testing."""
        mgr = DuckDBManager(":memory:")
        yield mgr
        mgr.close()

    def test_list_tables_empty(self, manager):
        """Test listing tables in empty database."""
        tables = manager.list_tables()
        assert tables == []

    def test_list_tables_multiple(self, manager):
        """Test listing multiple tables."""
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("table1", df)
        manager.create_table("table2", df)
        manager.create_table("table3", df)

        tables = manager.list_tables()
        assert set(tables) == {"table1", "table2", "table3"}

    def test_table_exists(self, manager):
        """Test checking table existence."""
        assert not manager.table_exists("nonexistent")

        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)
        assert manager.table_exists("test")

    def test_get_schema(self, manager):
        """Test getting table schema."""
        df = pl.DataFrame({
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "score": [85.5, 92.0]
        })
        manager.create_table("students", df)

        schema = manager.get_schema("students")
        assert "id" in schema
        assert "name" in schema
        assert "score" in schema

    def test_get_schema_nonexistent_table(self, manager):
        """Test error getting schema of nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager.get_schema("nonexistent")

    def test_get_statistics(self, manager):
        """Test getting table statistics."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })
        manager.create_table("data", df)

        stats = manager.get_statistics("data")
        assert stats["row_count"] == 3
        assert stats["column_count"] == 2
        assert set(stats["columns"]) == {"id", "value"}

    def test_get_statistics_nonexistent_table(self, manager):
        """Test error getting statistics of nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager.get_statistics("nonexistent")

    def test_drop_table(self, manager):
        """Test dropping table."""
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)
        assert manager.table_exists("test")

        manager.drop_table("test")
        assert not manager.table_exists("test")

    def test_drop_nonexistent_table(self, manager):
        """Test error dropping nonexistent table."""
        with pytest.raises(ValueError, match="does not exist"):
            manager.drop_table("nonexistent")


class TestMetadataManagement:
    """Tests for metadata tracking."""

    @pytest.fixture
    def manager(self):
        """Create in-memory DuckDB manager for testing."""
        mgr = DuckDBManager(":memory:")
        yield mgr
        mgr.close()

    def test_metadata_on_table_creation(self, manager):
        """Test metadata is updated on table creation."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10, 20, 30]
        })
        manager.create_table("test", df)

        assert "test" in manager.metadata
        assert manager.metadata["test"]["row_count"] == 3
        assert set(manager.metadata["test"]["columns"]) == {"id", "value"}
        assert "created_at" in manager.metadata["test"]

    def test_metadata_on_data_insertion(self, manager):
        """Test metadata is updated on data insertion."""
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)

        manager.insert_data("test", {"id": 3})
        assert manager.metadata["test"]["row_count"] == 3

    def test_metadata_on_table_drop(self, manager):
        """Test metadata is removed on table drop."""
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)
        assert "test" in manager.metadata

        manager.drop_table("test")
        assert "test" not in manager.metadata


class TestDataTypeHandling:
    """Tests for different data types."""

    @pytest.fixture
    def manager(self):
        """Create in-memory DuckDB manager for testing."""
        mgr = DuckDBManager(":memory:")
        yield mgr
        mgr.close()

    def test_integer_types(self, manager):
        """Test integer data types."""
        df = pl.DataFrame({
            "small_int": [1, 2, 3],
            "large_int": [1000000, 2000000, 3000000]
        })
        manager.create_table("integers", df)
        result = manager.read_table("integers")
        assert result.height == 3

    def test_float_types(self, manager):
        """Test float data types."""
        df = pl.DataFrame({
            "float_col": [1.5, 2.7, 3.9]
        })
        manager.create_table("floats", df)
        result = manager.read_table("floats")
        assert result["float_col"][0] == 1.5

    def test_string_types(self, manager):
        """Test string data types."""
        df = pl.DataFrame({
            "text": ["hello", "world", "test"]
        })
        manager.create_table("strings", df)
        result = manager.read_table("strings")
        assert result["text"][0] == "hello"

    def test_boolean_types(self, manager):
        """Test boolean data types."""
        df = pl.DataFrame({
            "flag": [True, False, True]
        })
        manager.create_table("booleans", df)
        result = manager.read_table("booleans")
        assert result.height == 3

    def test_null_handling(self, manager):
        """Test NULL value handling."""
        df = pl.DataFrame({
            "id": [1, 2, 3],
            "value": [10.0, None, 30.0]
        })
        manager.create_table("nulls", df)
        result = manager.read_table("nulls")
        assert result.height == 3


class TestValueFormatting:
    """Tests for SQL value formatting."""

    def test_format_null(self):
        """Test NULL value formatting."""
        assert DuckDBManager._format_value(None) == "NULL"

    def test_format_string(self):
        """Test string formatting."""
        assert DuckDBManager._format_value("hello") == "'hello'"

    def test_format_string_with_quotes(self):
        """Test string with quotes formatting."""
        result = DuckDBManager._format_value("it's")
        assert "it" in result and "s" in result

    def test_format_boolean_true(self):
        """Test boolean TRUE formatting."""
        assert DuckDBManager._format_value(True) == "TRUE"

    def test_format_boolean_false(self):
        """Test boolean FALSE formatting."""
        assert DuckDBManager._format_value(False) == "FALSE"

    def test_format_number(self):
        """Test number formatting."""
        assert DuckDBManager._format_value(42) == "42"
        assert DuckDBManager._format_value(3.14) == "3.14"


class TestStringRepresentation:
    """Tests for string representation."""

    def test_repr(self):
        """Test __repr__ method."""
        manager = DuckDBManager(":memory:")
        df = pl.DataFrame({"id": [1, 2]})
        manager.create_table("test", df)

        repr_str = repr(manager)
        assert "DuckDBManager" in repr_str
        assert "tables=1" in repr_str
        manager.close()
