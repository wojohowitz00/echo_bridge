"""DuckDB Manager for data storage and OLAP queries.

This module provides a comprehensive interface to DuckDB for:
- Creating and managing tables with polars DataFrames
- CRUD operations (Create, Read, Update, Delete)
- SQL queries and aggregations
- Schema introspection
- Data persistence and recovery
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import duckdb
import polars as pl


class DuckDBManager:
    """Manager for DuckDB database operations with polars integration.

    Attributes:
        db_path: Path to DuckDB database file
        connection: Active DuckDB connection
        metadata: Dictionary tracking table schemas and statistics
    """

    def __init__(self, db_path: str = "data.duckdb") -> None:
        """Initialize DuckDBManager.

        Args:
            db_path: Path to DuckDB database file. Defaults to "data.duckdb".
                    If ":memory:" is passed, creates in-memory database.

        Raises:
            OSError: If database directory cannot be created.

        Example:
            >>> manager = DuckDBManager("analytics.duckdb")
            >>> print(manager.db_path)
            analytics.duckdb
        """
        self.db_path = db_path
        self.connection: duckdb.DuckDBPyConnection = duckdb.connect(db_path)
        self.metadata: Dict[str, Dict[str, Any]] = {}
        self._initialize_metadata()

    def _initialize_metadata(self) -> None:
        """Initialize metadata dictionary from existing tables."""
        try:
            result = self.connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_catalog = 'memory' AND table_schema = 'main'"
            ).fetchall()

            for row in result:
                table_name = row[0]
                self.metadata[table_name] = {
                    "created_at": datetime.now().isoformat(),
                    "row_count": self._get_row_count(table_name),
                    "columns": self._get_columns(table_name),
                }
        except Exception:
            # If metadata initialization fails, continue with empty metadata
            pass

    def create_table(
        self,
        name: str,
        data: Union[pl.DataFrame, "pd.DataFrame", dict, list],
        replace: bool = False,
    ) -> None:
        """Create a table from a DataFrame or data structure.

        Args:
            name: Name of the table to create
            data: Data to populate table (polars/pandas DataFrame, dict, or list of dicts)
            replace: If True, replace existing table. If False, raise error if exists.

        Raises:
            ValueError: If table exists and replace=False
            TypeError: If data type is unsupported

        Example:
            >>> import polars as pl
            >>> df = pl.DataFrame({"id": [1, 2], "value": [10, 20]})
            >>> manager.create_table("metrics", df)
            >>> manager.table_exists("metrics")
            True
        """
        # Import here to avoid circular dependency
        from ai_data_science_team.utils.dataframe_compat import to_polars

        # Check if table exists
        if self.table_exists(name):
            if not replace:
                raise ValueError(
                    f"Table '{name}' already exists. Use replace=True to overwrite."
                )
            self.drop_table(name)

        # Convert data to polars
        df = to_polars(data)

        # Create table by inserting into a new table (CREATE TABLE AS)
        # First register temporarily to access the data
        temp_name = f"__temp_{name}_"
        self.connection.register(temp_name, df)

        # Create actual table from temp view
        self.connection.execute(
            f"CREATE TABLE {name} AS SELECT * FROM {temp_name}"
        )

        # Clean up temp view
        self.connection.execute(f"DROP VIEW {temp_name}")

        # Update metadata
        self.metadata[name] = {
            "created_at": datetime.now().isoformat(),
            "row_count": df.height,
            "columns": self._get_columns(name),
        }

    def insert_data(
        self,
        table_name: str,
        data: Union[pl.DataFrame, "pd.DataFrame", dict, list],
    ) -> int:
        """Insert data into an existing table.

        Args:
            table_name: Name of existing table
            data: Data to insert (polars/pandas DataFrame, dict, or list of dicts)

        Returns:
            Number of rows inserted

        Raises:
            ValueError: If table does not exist

        Example:
            >>> manager.insert_data("metrics", {"id": 3, "value": 30})
            1
        """
        from ai_data_science_team.utils.dataframe_compat import to_polars

        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        df = to_polars(data)
        rows_before = self._get_row_count(table_name)

        # Register data temporarily
        temp_name = f"__temp_insert_"
        self.connection.register(temp_name, df)

        try:
            # Insert using SELECT from temp view
            self.connection.execute(
                f"INSERT INTO {table_name} SELECT * FROM {temp_name}"
            )
        finally:
            # Clean up temp view
            try:
                self.connection.execute(f"DROP VIEW {temp_name}")
            except Exception:
                pass

        rows_after = self._get_row_count(table_name)
        rows_inserted = rows_after - rows_before

        # Update metadata
        if table_name in self.metadata:
            self.metadata[table_name]["row_count"] = rows_after

        return rows_inserted

    def read_table(self, table_name: str) -> pl.DataFrame:
        """Read entire table as polars DataFrame.

        Args:
            table_name: Name of table to read

        Returns:
            Table data as polars DataFrame

        Raises:
            ValueError: If table does not exist

        Example:
            >>> df = manager.read_table("metrics")
            >>> print(df.shape)
            (3, 2)
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        result = self.connection.execute(f"SELECT * FROM {table_name}").fetch_arrow_table()
        return pl.from_arrow(result)

    def query(self, sql: str) -> pl.DataFrame:
        """Execute SQL query and return results as polars DataFrame.

        Args:
            sql: SQL query string (can reference tables)

        Returns:
            Query results as polars DataFrame

        Raises:
            Exception: If SQL execution fails

        Example:
            >>> df = manager.query("SELECT * FROM metrics WHERE value > 15")
            >>> print(df.height)
            2
        """
        try:
            result = self.connection.execute(sql).fetch_arrow_table()
            return pl.from_arrow(result)
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    def aggregation(
        self,
        table_name: str,
        group_by: Optional[List[str]] = None,
        agg: Optional[Dict[str, str]] = None,
    ) -> pl.DataFrame:
        """Perform aggregation on table.

        Args:
            table_name: Name of table to aggregate
            group_by: Columns to group by
            agg: Dict mapping column name to aggregation function
                 (e.g., {"value": "SUM", "id": "COUNT"})

        Returns:
            Aggregated results as polars DataFrame

        Raises:
            ValueError: If table does not exist

        Example:
            >>> df = manager.aggregation(
            ...     "metrics",
            ...     group_by=["type"],
            ...     agg={"value": "SUM", "id": "COUNT"}
            ... )
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        if not agg:
            raise ValueError("agg dictionary cannot be empty")

        # Build aggregation columns
        agg_cols = ", ".join([f"{func}({col}) as {col}_{func.lower()}"
                              for col, func in agg.items()])

        if group_by:
            group_clause = ", ".join(group_by)
            sql = (
                f"SELECT {group_clause}, {agg_cols} FROM {table_name} "
                f"GROUP BY {group_clause}"
            )
        else:
            sql = f"SELECT {agg_cols} FROM {table_name}"

        return self.query(sql)

    def update_rows(
        self,
        table_name: str,
        where_clause: str,
        updates: Dict[str, Any],
    ) -> int:
        """Update rows matching condition.

        Args:
            table_name: Name of table
            where_clause: SQL WHERE clause condition
            updates: Dict mapping column names to new values

        Returns:
            Number of rows updated

        Raises:
            ValueError: If table does not exist

        Example:
            >>> count = manager.update_rows(
            ...     "metrics",
            ...     "id = 1",
            ...     {"value": 15}
            ... )
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        set_clause = ", ".join(
            [f"{col} = {self._format_value(val)}"
             for col, val in updates.items()]
        )

        sql = f"UPDATE {table_name} SET {set_clause} WHERE {where_clause}"

        try:
            self.connection.execute(sql)
            return self._get_row_count(table_name)
        except Exception as e:
            raise Exception(f"Update failed: {str(e)}")

    def delete_rows(self, table_name: str, where_clause: str) -> int:
        """Delete rows matching condition.

        Args:
            table_name: Name of table
            where_clause: SQL WHERE clause condition

        Returns:
            Number of rows remaining in table

        Raises:
            ValueError: If table does not exist

        Example:
            >>> count = manager.delete_rows("metrics", "value < 10")
            >>> print(count)
            2
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        sql = f"DELETE FROM {table_name} WHERE {where_clause}"

        try:
            self.connection.execute(sql)
            return self._get_row_count(table_name)
        except Exception as e:
            raise Exception(f"Delete failed: {str(e)}")

    def drop_table(self, table_name: str) -> None:
        """Drop (delete) a table.

        Args:
            table_name: Name of table to drop

        Raises:
            ValueError: If table does not exist

        Example:
            >>> manager.drop_table("old_metrics")
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        self.connection.execute(f"DROP TABLE {table_name}")
        self.metadata.pop(table_name, None)

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists.

        Args:
            table_name: Name of table to check

        Returns:
            True if table exists, False otherwise

        Example:
            >>> manager.table_exists("metrics")
            True
        """
        try:
            self.connection.execute(f"SELECT 1 FROM {table_name} LIMIT 1")
            return True
        except Exception:
            return False

    def list_tables(self) -> List[str]:
        """List all tables in database.

        Returns:
            List of table names

        Example:
            >>> tables = manager.list_tables()
            >>> print(tables)
            ['metrics', 'events']
        """
        try:
            result = self.connection.execute(
                "SELECT table_name FROM information_schema.tables "
                "WHERE table_schema = 'main' AND table_type = 'BASE TABLE'"
            ).fetchall()
            tables = [row[0] for row in result]
            # Filter out temp tables
            return [t for t in tables if not t.startswith("__temp_")]
        except Exception:
            return []

    def get_schema(self, table_name: str) -> Dict[str, str]:
        """Get column names and types for a table.

        Args:
            table_name: Name of table

        Returns:
            Dict mapping column names to data types

        Raises:
            ValueError: If table does not exist

        Example:
            >>> schema = manager.get_schema("metrics")
            >>> print(schema)
            {'id': 'BIGINT', 'value': 'DOUBLE'}
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        result = self.connection.execute(
            f"PRAGMA table_info({table_name})"
        ).fetchall()

        return {row[1]: row[2] for row in result}

    def get_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get statistics for a table.

        Args:
            table_name: Name of table

        Returns:
            Dictionary with row count, column count, and memory usage

        Raises:
            ValueError: If table does not exist

        Example:
            >>> stats = manager.get_statistics("metrics")
            >>> print(stats['row_count'])
            3
        """
        if not self.table_exists(table_name):
            raise ValueError(f"Table '{table_name}' does not exist.")

        row_count = self._get_row_count(table_name)
        schema = self.get_schema(table_name)
        col_count = len(schema)

        return {
            "row_count": row_count,
            "column_count": col_count,
            "columns": list(schema.keys()),
            "schema": schema,
        }

    def _get_row_count(self, table_name: str) -> int:
        """Get number of rows in table."""
        try:
            result = self.connection.execute(
                f"SELECT COUNT(*) FROM {table_name}"
            ).fetchone()
            return result[0] if result else 0
        except Exception:
            return 0

    def _get_columns(self, table_name: str) -> List[str]:
        """Get column names from table."""
        try:
            schema = self.get_schema(table_name)
            return list(schema.keys())
        except Exception:
            return []

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format value for SQL query."""
        if value is None:
            return "NULL"
        if isinstance(value, str):
            return f"'{value.replace(chr(39), chr(39) * 2)}'"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        return str(value)

    def close(self) -> None:
        """Close database connection.

        Example:
            >>> manager.close()
        """
        if self.connection:
            self.connection.close()

    def __del__(self) -> None:
        """Cleanup on deletion."""
        self.close()

    def __repr__(self) -> str:
        """String representation of DuckDBManager."""
        tables = len(self.list_tables())
        return f"DuckDBManager(db_path='{self.db_path}', tables={tables})"
