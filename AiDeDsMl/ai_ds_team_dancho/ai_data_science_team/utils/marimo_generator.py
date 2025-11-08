"""Marimo notebook generator for creating reactive Python notebooks.

This module provides utilities to programmatically generate marimo notebooks
that can be used to display agent outputs, visualizations, and data insights.

Key features:
- Create marimo notebooks from Python code
- Auto-format code with ruff
- Add markdown cells for documentation
- Include visualization cells
- Support for data exploration and analysis
"""

import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union


class MarimoCell:
    """Represents a single marimo notebook cell."""

    def __init__(
        self,
        source: str,
        cell_type: str = "code",
        title: Optional[str] = None,
    ) -> None:
        """Initialize a marimo cell.

        Args:
            source: Cell content (code or markdown)
            cell_type: Type of cell - "code" or "markdown"
            title: Optional cell title/label
        """
        self.source = source
        self.cell_type = cell_type
        self.title = title
        self.created_at = datetime.now().isoformat()

    def __repr__(self) -> str:
        """String representation of cell."""
        cell_type_str = self.cell_type.upper()
        return f"MarimoCell({cell_type_str}, lines={len(self.source.splitlines())})"


class MarimoNotebook:
    """Builder for marimo notebooks.

    A marimo notebook is a reactive Python notebook that auto-recomputes
    when cell dependencies change. Unlike Jupyter notebooks (JSON-based),
    marimo notebooks are pure Python files (.py) with special cell markers.

    Example:
        >>> notebook = MarimoNotebook(title="Data Analysis")
        >>> notebook.add_markdown("# Data Exploration")
        >>> notebook.add_code("import polars as pl\\ndf = pl.DataFrame(...)")
        >>> notebook.add_markdown("## Summary Statistics")
        >>> notebook.add_code("print(df.describe())")
        >>> notebook.save("analysis.py")
    """

    def __init__(
        self,
        title: str = "Untitled Notebook",
        description: str = "",
        author: str = "",
    ) -> None:
        """Initialize a marimo notebook.

        Args:
            title: Notebook title
            description: Notebook description
            author: Author name
        """
        self.title = title
        self.description = description
        self.author = author
        self.cells: List[MarimoCell] = []
        self._add_header()

    def _add_header(self) -> None:
        """Add header comment to notebook."""
        header = f'''"""
{self.title}

{self.description}

Author: {self.author}
Created: {datetime.now().isoformat()}

This is a marimo notebook. Marimo notebooks are reactive Python files
that auto-recompute when cell dependencies change.

Run with: marimo edit {self.title}.py
"""

import marimo as mo

__all__ = []
'''
        self.cells.append(MarimoCell(header, cell_type="code", title="Header"))

    def add_markdown(self, content: str, title: Optional[str] = None) -> "MarimoNotebook":
        """Add a markdown cell to the notebook.

        Args:
            content: Markdown content
            title: Optional cell title

        Returns:
            Self for method chaining

        Example:
            >>> nb = MarimoNotebook()
            >>> nb.add_markdown("# Section\\nSome content")
        """
        cell = MarimoCell(content, cell_type="markdown", title=title)
        self.cells.append(cell)
        return self

    def add_code(self, code: str, title: Optional[str] = None) -> "MarimoNotebook":
        """Add a code cell to the notebook.

        Args:
            code: Python code
            title: Optional cell title

        Returns:
            Self for method chaining

        Example:
            >>> nb = MarimoNotebook()
            >>> nb.add_code("import polars as pl")
        """
        # Strip common indentation
        code = textwrap.dedent(code).strip()
        cell = MarimoCell(code, cell_type="code", title=title)
        self.cells.append(cell)
        return self

    def add_import_cell(
        self,
        imports: List[str],
        title: str = "Imports",
    ) -> "MarimoNotebook":
        """Add an import cell with common dependencies.

        Args:
            imports: List of import statements
            title: Cell title

        Returns:
            Self for method chaining

        Example:
            >>> nb = MarimoNotebook()
            >>> nb.add_import_cell([
            ...     "import polars as pl",
            ...     "import duckdb",
            ...     "import altair as alt"
            ... ])
        """
        import_code = "\n".join(imports)
        return self.add_code(import_code, title=title)

    def add_data_exploration_cell(
        self,
        df_name: str = "df",
        title: str = "Data Exploration",
    ) -> "MarimoNotebook":
        """Add a cell for exploring DataFrame properties.

        Args:
            df_name: Name of the DataFrame variable
            title: Cell title

        Returns:
            Self for method chaining
        """
        code = f"""# Data shape and info
print(f"Shape: {{{df_name}.shape}}")
print(f"Columns: {{{df_name}.columns}}")
print(f"Data types: {{{df_name}.dtypes}}")

# Basic statistics
print("\\nBasic Statistics:")
print({df_name}.describe())

# Check for nulls
print("\\nNull values:")
print({df_name}.null_count())"""

        return self.add_code(code, title=title)

    def add_visualization_cell(
        self,
        code: str,
        title: str = "Visualization",
    ) -> "MarimoNotebook":
        """Add a cell with altair visualization.

        Args:
            code: Altair visualization code
            title: Cell title

        Returns:
            Self for method chaining

        Example:
            >>> nb = MarimoNotebook()
            >>> nb.add_visualization_cell('''
            ...     import altair as alt
            ...     chart = alt.Chart(df).mark_bar().encode(
            ...         x='category:N',
            ...         y='value:Q'
            ...     )
            ... ''')
        """
        return self.add_code(code, title=title)

    def add_duckdb_cell(
        self,
        table_name: str,
        query: str,
        title: str = "DuckDB Query",
    ) -> "MarimoNotebook":
        """Add a cell for DuckDB query execution.

        Args:
            table_name: Name of table in DuckDB
            query: SQL query
            title: Cell title

        Returns:
            Self for method chaining

        Example:
            >>> nb.add_duckdb_cell(
            ...     "events",
            ...     "SELECT category, COUNT(*) FROM events GROUP BY category"
            ... )
        """
        code = f"""import duckdb

# Execute DuckDB query
result = duckdb.query('''
{textwrap.indent(query, '    ')}
''').pl()

print(result)"""

        return self.add_code(code, title=title)

    def add_conclusion_cell(
        self,
        summary: str,
        title: str = "Conclusion",
    ) -> "MarimoNotebook":
        """Add a conclusion/summary markdown cell.

        Args:
            summary: Summary text
            title: Cell title

        Returns:
            Self for method chaining
        """
        md_content = f"""## {title}

{summary}"""
        return self.add_markdown(md_content, title=title)

    def get_marimo_code(self) -> str:
        """Get complete marimo notebook as Python code.

        Returns:
            Python code representing the marimo notebook
        """
        lines: List[str] = []

        for i, cell in enumerate(self.cells):
            if cell.cell_type == "markdown":
                # Markdown cells in marimo are mo.md() calls
                escaped_content = cell.source.replace('"""', r'\"\"\"')
                lines.append(f'mo.md(r"""\\')
                lines.append(escaped_content)
                lines.append('""")')
            else:
                # Code cells are regular Python
                lines.append(cell.source)

            # Add separator between cells (optional but helpful)
            if i < len(self.cells) - 1:
                lines.append("")
                lines.append("# ─" * 40)
                lines.append("")

        return "\n".join(lines)

    def save(self, filepath: Union[str, Path]) -> Path:
        """Save notebook to a .py file.

        Args:
            filepath: Path where notebook will be saved

        Returns:
            Path object of saved file

        Raises:
            IOError: If file cannot be written

        Example:
            >>> nb = MarimoNotebook(title="Analysis")
            >>> nb.add_code("print('Hello')")
            >>> path = nb.save("notebook.py")
            >>> print(path.exists())
            True
        """
        filepath = Path(filepath)

        # Ensure parent directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write notebook code
        code = self.get_marimo_code()

        try:
            filepath.write_text(code, encoding="utf-8")
            return filepath
        except IOError as e:
            raise IOError(f"Failed to save notebook to {filepath}: {str(e)}")

    def to_string(self) -> str:
        """Get notebook as string (alias for get_marimo_code).

        Returns:
            Notebook code as string
        """
        return self.get_marimo_code()

    def cell_count(self) -> int:
        """Get number of cells in notebook.

        Returns:
            Total cell count
        """
        return len(self.cells)

    def code_cell_count(self) -> int:
        """Get number of code cells.

        Returns:
            Count of code cells
        """
        return sum(1 for cell in self.cells if cell.cell_type == "code")

    def markdown_cell_count(self) -> int:
        """Get number of markdown cells.

        Returns:
            Count of markdown cells
        """
        return sum(1 for cell in self.cells if cell.cell_type == "markdown")

    def __repr__(self) -> str:
        """String representation of notebook."""
        return (
            f"MarimoNotebook(title='{self.title}', "
            f"cells={self.cell_count()}, "
            f"code={self.code_cell_count()}, "
            f"markdown={self.markdown_cell_count()})"
        )

    def __str__(self) -> str:
        """String representation (returns first 500 chars of code)."""
        code = self.get_marimo_code()
        preview = code[:500] + "..." if len(code) > 500 else code
        return preview


class NotebookBuilder:
    """Factory for creating common notebook templates.

    Provides convenience methods for creating notebooks with standard
    structures like data analysis, ML experiments, etc.
    """

    @staticmethod
    def create_data_analysis_notebook(
        title: str = "Data Analysis",
        description: str = "Exploratory Data Analysis",
        author: str = "AI Data Science Team",
    ) -> MarimoNotebook:
        """Create a data analysis notebook template.

        Args:
            title: Notebook title
            description: Description
            author: Author name

        Returns:
            Configured MarimoNotebook

        Example:
            >>> nb = NotebookBuilder.create_data_analysis_notebook()
            >>> nb.add_code("import polars as pl")
        """
        nb = MarimoNotebook(title=title, description=description, author=author)

        nb.add_markdown("# Data Analysis\n\nThis notebook performs exploratory data analysis.")
        nb.add_import_cell([
            "import marimo as mo",
            "import polars as pl",
            "import duckdb",
            "import altair as alt",
        ])

        return nb

    @staticmethod
    def create_ml_notebook(
        title: str = "Machine Learning",
        description: str = "ML Model Training & Evaluation",
        author: str = "AI Data Science Team",
    ) -> MarimoNotebook:
        """Create an ML experiment notebook template.

        Args:
            title: Notebook title
            description: Description
            author: Author name

        Returns:
            Configured MarimoNotebook
        """
        nb = MarimoNotebook(title=title, description=description, author=author)

        nb.add_markdown("# Machine Learning Experiment\n\nModel training and evaluation.")
        nb.add_import_cell([
            "import marimo as mo",
            "import polars as pl",
            "from sklearn.model_selection import train_test_split",
            "from sklearn.preprocessing import StandardScaler",
            "import altair as alt",
        ])

        return nb

    @staticmethod
    def create_etl_notebook(
        title: str = "ETL Pipeline",
        description: str = "Data Extraction, Transformation, Loading",
        author: str = "AI Data Science Team",
    ) -> MarimoNotebook:
        """Create an ETL pipeline notebook template.

        Args:
            title: Notebook title
            description: Description
            author: Author name

        Returns:
            Configured MarimoNotebook
        """
        nb = MarimoNotebook(title=title, description=description, author=author)

        nb.add_markdown(
            "# ETL Pipeline\n\n"
            "Data extraction, transformation, and loading workflow."
        )
        nb.add_import_cell([
            "import marimo as mo",
            "import polars as pl",
            "import duckdb",
            "from dlt import pipeline",
        ])

        return nb
