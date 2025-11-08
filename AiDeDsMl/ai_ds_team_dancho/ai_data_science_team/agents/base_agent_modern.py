"""Base agent class with marimo notebook generation support.

This module provides a modern base agent that:
- Integrates with DuckDB for data persistence
- Generates marimo notebooks as output artifacts
- Supports both polars and pandas (during migration)
- Uses type hints throughout
- Includes comprehensive logging and error handling
"""

import json
import logging
import tempfile
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import polars as pl

from ai_data_science_team.utils import (
    DuckDBManager,
    MarimoNotebook,
    NotebookBuilder,
    to_polars,
)


logger = logging.getLogger(__name__)


class BaseAgentModern(ABC):
    """Modern base agent with marimo notebook generation.

    This abstract base class provides a foundation for all agents in the
    modernized system. It integrates:
    - DuckDB for data persistence
    - marimo for reactive notebook output
    - polars for efficient data processing
    - Full type hints and validation

    Attributes:
        name: Agent name
        description: Agent description
        db_manager: DuckDB manager instance
        notebook: marimo notebook being built
        config: Agent configuration dictionary
        results: Dictionary of execution results
    """

    def __init__(
        self,
        name: str,
        description: str = "",
        db_path: str = ":memory:",
        notebook_dir: Optional[Path] = None,
    ) -> None:
        """Initialize the base agent.

        Args:
            name: Agent name
            description: Agent description
            db_path: Path to DuckDB database (default: in-memory)
            notebook_dir: Directory to save generated notebooks

        Example:
            >>> class MyAgent(BaseAgentModern):
            ...     def execute(self, data):
            ...         return {"result": data}
            >>> agent = MyAgent("MyAgent", "My custom agent")
        """
        self.name = name
        self.description = description
        self.db_manager = DuckDBManager(db_path)
        # Use absolute path with explicit temp directory by default
        if notebook_dir:
            self.notebook_dir = Path(notebook_dir).resolve()
        else:
            self.notebook_dir = Path(tempfile.gettempdir()) / "ai_data_science_team" / "notebooks"
        self.notebook: Optional[MarimoNotebook] = None
        self.config: Dict[str, Any] = {}
        self.results: Dict[str, Any] = {}
        self._created_at = datetime.now().isoformat()

        logger.info(f"Initialized agent: {self.name}")

    @abstractmethod
    def execute(self, data: Any) -> Dict[str, Any]:
        """Execute agent logic on input data.

        Args:
            data: Input data (DataFrame, dict, or other formats)

        Returns:
            Dictionary of results
        """
        pass

    def run(self, data: Any) -> Dict[str, Any]:
        """Run agent and generate marimo notebook output.

        This orchestrates the full agent workflow:
        1. Validate input
        2. Execute agent logic
        3. Persist results to DuckDB
        4. Generate marimo notebook
        5. Return results

        Args:
            data: Input data

        Returns:
            Dictionary containing results and notebook path

        Example:
            >>> agent = MyAgent("test")
            >>> results = agent.run({"x": [1, 2, 3]})
            >>> print(results["notebook_path"])
        """
        try:
            # Validate input
            if data is None:
                raise ValueError("Input data cannot be None")

            logger.info(f"Running agent: {self.name}")

            # Execute agent logic
            self.results = self.execute(data)

            # Generate and save notebook
            notebook_path = self.generate_notebook()

            # Return combined results
            return {
                "status": "success",
                "agent": self.name,
                "results": self.results,
                "notebook_path": str(notebook_path),
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as e:
            logger.error(f"Agent execution failed: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "agent": self.name,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    def setup_notebook(
        self,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> MarimoNotebook:
        """Create a new marimo notebook for this agent.

        Args:
            title: Notebook title (default: agent name)
            description: Notebook description (default: agent description)

        Returns:
            Configured MarimoNotebook instance

        Example:
            >>> agent = MyAgent("test")
            >>> nb = agent.setup_notebook()
            >>> nb.add_code("x = 1")
        """
        title = title or self.name
        description = description or self.description or ""

        self.notebook = MarimoNotebook(
            title=title,
            description=description,
            author=f"Agent: {self.name}",
        )

        # Add standard header
        self.notebook.add_markdown(
            f"# {self.name}\n\n{self.description}\n\n"
            f"**Generated**: {datetime.now().isoformat()}"
        )

        self.notebook.add_import_cell([
            "import marimo as mo",
            "import polars as pl",
            "import duckdb",
            "import altair as alt",
        ])

        return self.notebook

    def add_results_to_notebook(self, results: Dict[str, Any]) -> None:
        """Add results to marimo notebook.

        Args:
            results: Dictionary of results to add

        Example:
            >>> agent.add_results_to_notebook({"metric": 42})
        """
        if not self.notebook:
            self.setup_notebook()

        self.notebook.add_markdown("## Results")

        for key, value in results.items():
            if isinstance(value, pl.DataFrame):
                # Add DataFrame preview
                self.notebook.add_markdown(f"### {key}")
                self.notebook.add_code(
                    f"{key} = pl.DataFrame({value.to_dicts()})\nprint({key})"
                )
            elif isinstance(value, (int, float, str, bool)):
                # Add scalar value
                self.notebook.add_code(f"{key} = {repr(value)}\nprint(f'{key}: {{{key}}}')")
            else:
                # Add generic representation
                self.notebook.add_markdown(f"**{key}**: {str(value)[:200]}...")

    def persist_to_duckdb(
        self,
        table_name: str,
        data: Union[pl.DataFrame, "pd.DataFrame", dict, list],
    ) -> None:
        """Persist data to DuckDB.

        Args:
            table_name: Name of table to create
            data: Data to persist

        Example:
            >>> agent.persist_to_duckdb("results", results_df)
        """
        try:
            df = to_polars(data)
            self.db_manager.create_table(table_name, df, replace=True)
            logger.info(f"Persisted {df.height} rows to {table_name}")
        except Exception as e:
            logger.error(f"Failed to persist data: {str(e)}")

    def load_from_duckdb(self, table_name: str) -> pl.DataFrame:
        """Load data from DuckDB.

        Args:
            table_name: Name of table to load

        Returns:
            Data as polars DataFrame

        Raises:
            ValueError: If table does not exist

        Example:
            >>> df = agent.load_from_duckdb("results")
        """
        if not self.db_manager.table_exists(table_name):
            raise ValueError(f"Table {table_name} does not exist in DuckDB")

        return self.db_manager.read_table(table_name)

    def query_duckdb(self, sql: str) -> pl.DataFrame:
        """Execute SQL query on DuckDB.

        Args:
            sql: SQL query string

        Returns:
            Query results as polars DataFrame

        Example:
            >>> df = agent.query_duckdb("SELECT * FROM results WHERE value > 10")
        """
        return self.db_manager.query(sql)

    def generate_notebook(self) -> Path:
        """Generate marimo notebook from execution results.

        This creates a reactive notebook that can be viewed and edited
        interactively using marimo.

        Returns:
            Path to saved notebook file

        Example:
            >>> notebook_path = agent.generate_notebook()
            >>> print(f"Saved to: {notebook_path}")
        """
        if not self.notebook:
            self.setup_notebook()

        # Add results
        if self.results:
            self.add_results_to_notebook(self.results)

        # Add conclusion
        self.notebook.add_markdown(
            "## Agent Info\n\n"
            f"- Agent: {self.name}\n"
            f"- Created: {self._created_at}\n"
            f"- Results tables: {', '.join(self.db_manager.list_tables())}"
        )

        # Save notebook
        self.notebook_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{self.name.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.py"
        notebook_path = self.notebook_dir / filename

        self.notebook.save(notebook_path)
        logger.info(f"Generated notebook: {notebook_path}")

        return notebook_path

    def get_config(self) -> Dict[str, Any]:
        """Get agent configuration.

        Returns:
            Configuration dictionary
        """
        return {
            "name": self.name,
            "description": self.description,
            "created_at": self._created_at,
            "db_path": self.db_manager.db_path,
            "notebook_dir": str(self.notebook_dir),
        }

    def set_config(self, config: Dict[str, Any]) -> None:
        """Set agent configuration.

        Args:
            config: Configuration dictionary
        """
        self.config = {**self.config, **config}
        logger.info(f"Updated config: {config}")

    def close(self) -> None:
        """Close resources (database connections, etc).

        Example:
            >>> agent.close()
        """
        self.db_manager.close()
        logger.info(f"Closed agent: {self.name}")

    def __repr__(self) -> str:
        """String representation of agent."""
        return (
            f"BaseAgentModern(name='{self.name}', "
            f"tables={len(self.db_manager.list_tables())})"
        )

    def __del__(self) -> None:
        """Cleanup on deletion."""
        try:
            self.close()
        except Exception:
            pass
