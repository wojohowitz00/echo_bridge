"""Unit tests for marimo notebook generator.

Tests cover:
- Creating marimo cells
- Building notebooks with various cell types
- Saving notebooks to files
- Using notebook templates
- Cell counting and introspection
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from ai_data_science_team.utils.marimo_generator import (
    MarimoCell,
    MarimoNotebook,
    NotebookBuilder,
)


class TestMarimoCell:
    """Tests for MarimoCell class."""

    def test_code_cell_creation(self):
        """Test creating a code cell."""
        code = "print('Hello, World!')"
        cell = MarimoCell(code, cell_type="code")

        assert cell.source == code
        assert cell.cell_type == "code"
        assert cell.title is None
        assert cell.created_at is not None

    def test_markdown_cell_creation(self):
        """Test creating a markdown cell."""
        content = "# Hello\n\nThis is markdown."
        cell = MarimoCell(content, cell_type="markdown", title="Intro")

        assert cell.source == content
        assert cell.cell_type == "markdown"
        assert cell.title == "Intro"

    def test_cell_repr(self):
        """Test string representation of cell."""
        cell = MarimoCell("x = 1", cell_type="code")
        repr_str = repr(cell)

        assert "MarimoCell" in repr_str
        assert "CODE" in repr_str


class TestMarimoNotebook:
    """Tests for MarimoNotebook class."""

    def test_notebook_creation(self):
        """Test creating a notebook."""
        nb = MarimoNotebook(
            title="Test Notebook",
            description="A test notebook",
            author="Test Author"
        )

        assert nb.title == "Test Notebook"
        assert nb.description == "A test notebook"
        assert nb.author == "Test Author"
        assert nb.cell_count() > 0  # Has header cell

    def test_add_markdown(self):
        """Test adding markdown cell."""
        nb = MarimoNotebook()
        initial_count = nb.cell_count()

        nb.add_markdown("# Section", title="Header")

        assert nb.cell_count() == initial_count + 1
        assert nb.markdown_cell_count() >= 1

    def test_add_code(self):
        """Test adding code cell."""
        nb = MarimoNotebook()
        initial_count = nb.cell_count()

        nb.add_code("x = 1\nprint(x)")

        assert nb.cell_count() == initial_count + 1
        assert nb.code_cell_count() >= 1

    def test_method_chaining(self):
        """Test method chaining."""
        nb = (
            MarimoNotebook()
            .add_markdown("# Title")
            .add_code("x = 1")
            .add_code("y = 2")
        )

        assert nb.code_cell_count() >= 2

    def test_add_import_cell(self):
        """Test adding import cell."""
        nb = MarimoNotebook()
        imports = [
            "import polars as pl",
            "import duckdb",
            "import altair as alt"
        ]

        nb.add_import_cell(imports)

        code = nb.get_marimo_code()
        for imp in imports:
            assert imp in code

    def test_add_data_exploration_cell(self):
        """Test adding data exploration cell."""
        nb = MarimoNotebook()
        nb.add_data_exploration_cell("df", title="Explore Data")

        code = nb.get_marimo_code()
        assert "shape" in code.lower()
        assert "describe" in code.lower()

    def test_add_visualization_cell(self):
        """Test adding visualization cell."""
        nb = MarimoNotebook()
        viz_code = "chart = alt.Chart(df).mark_bar()"
        nb.add_visualization_cell(viz_code)

        code = nb.get_marimo_code()
        assert "alt.Chart" in code

    def test_add_duckdb_cell(self):
        """Test adding DuckDB query cell."""
        nb = MarimoNotebook()
        query = "SELECT * FROM events WHERE id > 10"

        nb.add_duckdb_cell("events", query)

        code = nb.get_marimo_code()
        assert "duckdb" in code.lower()
        assert "SELECT" in code

    def test_add_conclusion_cell(self):
        """Test adding conclusion cell."""
        nb = MarimoNotebook()
        summary = "The analysis shows positive trends."

        nb.add_conclusion_cell(summary)

        code = nb.get_marimo_code()
        assert summary in code

    def test_cell_counts(self):
        """Test cell counting methods."""
        nb = MarimoNotebook()
        initial_code_count = nb.code_cell_count()
        initial_md_count = nb.markdown_cell_count()

        nb.add_code("x = 1")
        nb.add_code("y = 2")
        nb.add_markdown("# Title")

        assert nb.code_cell_count() == initial_code_count + 2
        assert nb.markdown_cell_count() == initial_md_count + 1

    def test_get_marimo_code(self):
        """Test generating marimo code."""
        nb = MarimoNotebook()
        nb.add_code("x = 1")
        nb.add_markdown("# Section")
        nb.add_code("print(x)")

        code = nb.get_marimo_code()

        assert isinstance(code, str)
        assert len(code) > 0
        assert "marimo" in code

    def test_notebook_repr(self):
        """Test notebook string representation."""
        nb = MarimoNotebook(title="My Notebook")
        repr_str = repr(nb)

        assert "MarimoNotebook" in repr_str
        assert "My Notebook" in repr_str
        assert "cells=" in repr_str

    def test_notebook_str(self):
        """Test notebook string preview."""
        nb = MarimoNotebook()
        nb.add_code("x = 1")

        str_repr = str(nb)
        assert len(str_repr) > 0


class TestNotebookSaving:
    """Tests for saving notebooks to files."""

    def test_save_notebook(self):
        """Test saving notebook to file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nb = MarimoNotebook(title="Test")
            nb.add_code("x = 1")

            filepath = Path(tmpdir) / "test.py"
            saved_path = nb.save(filepath)

            assert saved_path.exists()
            assert saved_path.suffix == ".py"

    def test_saved_notebook_content(self):
        """Test content of saved notebook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nb = MarimoNotebook()
            code_to_add = "result = 42"
            nb.add_code(code_to_add)

            filepath = Path(tmpdir) / "test.py"
            nb.save(filepath)

            content = filepath.read_text()
            assert code_to_add in content
            assert "marimo" in content

    def test_save_creates_directories(self):
        """Test that save creates parent directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nb = MarimoNotebook()
            nested_path = Path(tmpdir) / "subdir" / "nested" / "notebook.py"

            saved_path = nb.save(nested_path)

            assert saved_path.parent.exists()
            assert saved_path.exists()

    def test_save_with_string_path(self):
        """Test save with string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nb = MarimoNotebook()
            path_str = str(Path(tmpdir) / "notebook.py")

            saved_path = nb.save(path_str)

            assert isinstance(saved_path, Path)
            assert saved_path.exists()

    def test_to_string_method(self):
        """Test to_string method."""
        nb = MarimoNotebook()
        nb.add_code("x = 1")

        code_str = nb.to_string()

        assert isinstance(code_str, str)
        assert "x = 1" in code_str


class TestNotebookBuilder:
    """Tests for NotebookBuilder factory."""

    def test_create_data_analysis_notebook(self):
        """Test creating data analysis notebook template."""
        nb = NotebookBuilder.create_data_analysis_notebook()

        assert "Data Analysis" in nb.title
        assert nb.cell_count() > 0
        code = nb.get_marimo_code()
        assert "polars" in code
        assert "duckdb" in code

    def test_create_ml_notebook(self):
        """Test creating ML notebook template."""
        nb = NotebookBuilder.create_ml_notebook()

        assert "Machine Learning" in nb.title
        code = nb.get_marimo_code()
        assert "sklearn" in code
        assert "StandardScaler" in code

    def test_create_etl_notebook(self):
        """Test creating ETL notebook template."""
        nb = NotebookBuilder.create_etl_notebook()

        assert "ETL" in nb.title
        code = nb.get_marimo_code()
        assert "dlt" in code

    def test_builder_customization(self):
        """Test customizing builder output."""
        nb = NotebookBuilder.create_data_analysis_notebook(
            title="Custom Title",
            author="Custom Author"
        )

        assert nb.title == "Custom Title"
        assert nb.author == "Custom Author"


class TestComplexNotebookScenarios:
    """Tests for complex notebook creation scenarios."""

    def test_full_data_analysis_workflow(self):
        """Test creating a complete data analysis notebook."""
        nb = NotebookBuilder.create_data_analysis_notebook()

        # Add workflow steps
        nb.add_markdown("## Step 1: Load Data")
        nb.add_code("df = pl.read_csv('data.csv')")
        nb.add_data_exploration_cell()

        nb.add_markdown("## Step 2: Visualize")
        nb.add_visualization_cell(
            "chart = alt.Chart(df).mark_bar().encode(x='col:N', y='val:Q')"
        )

        nb.add_markdown("## Step 3: Analysis")
        nb.add_duckdb_cell("data", "SELECT * FROM data WHERE val > 10")

        nb.add_conclusion_cell("Analysis complete")

        assert nb.cell_count() > 5
        code = nb.get_marimo_code()
        assert "Step 1" in code
        assert "Step 2" in code
        assert "Step 3" in code

    def test_multiline_code_cells(self):
        """Test adding multiline code cells."""
        nb = MarimoNotebook()

        multiline_code = """
        import polars as pl

        df = pl.DataFrame({
            'id': [1, 2, 3],
            'value': [10, 20, 30]
        })

        print(df)
        """

        nb.add_code(multiline_code)
        code = nb.get_marimo_code()

        assert "import polars" in code
        assert "print(df)" in code

    def test_special_characters_in_markdown(self):
        """Test handling special characters in markdown."""
        nb = MarimoNotebook()
        markdown = '# Test with "quotes" and \\n newlines'

        nb.add_markdown(markdown)
        code = nb.get_marimo_code()

        assert "Test with" in code

    def test_empty_notebook_generation(self):
        """Test generating code from empty notebook."""
        nb = MarimoNotebook()
        code = nb.get_marimo_code()

        assert isinstance(code, str)
        assert len(code) > 0
        assert "marimo" in code


class TestNotebookEdgeCases:
    """Tests for edge cases and error handling."""

    def test_very_long_code_cell(self):
        """Test adding very long code cell."""
        nb = MarimoNotebook()
        long_code = "\n".join([f"x{i} = {i}" for i in range(100)])

        nb.add_code(long_code)
        code = nb.get_marimo_code()

        assert "x0 = 0" in code
        assert "x99 = 99" in code

    def test_unicode_content(self):
        """Test handling unicode characters."""
        nb = MarimoNotebook()
        nb.add_markdown("# Analysis ✓ Complete 📊")
        nb.add_code("# Comment with emoji 🎯")

        code = nb.get_marimo_code()
        assert "✓" in code
        assert "🎯" in code

    def test_indented_code(self):
        """Test handling indented code."""
        nb = MarimoNotebook()
        indented_code = """
            def func():
                x = 1
                return x
        """

        nb.add_code(indented_code)
        code = nb.get_marimo_code()

        assert "def func():" in code

    def test_markdown_with_code_blocks(self):
        """Test markdown containing code blocks."""
        nb = MarimoNotebook()
        markdown = """
        # Example

        ```python
        df = pl.DataFrame({'a': [1, 2, 3]})
        ```
        """

        nb.add_markdown(markdown)
        code = nb.get_marimo_code()

        assert "pl.DataFrame" in code


class TestNotebookIntegration:
    """Integration tests combining multiple features."""

    def test_save_and_read_notebook(self):
        """Test saving and reading back a notebook."""
        with tempfile.TemporaryDirectory() as tmpdir:
            nb1 = NotebookBuilder.create_data_analysis_notebook()
            nb1.add_code("result = 42")

            filepath = Path(tmpdir) / "analysis.py"
            nb1.save(filepath)

            # Read back
            content = filepath.read_text()
            assert "result = 42" in content
            assert "polars" in content

    def test_notebook_with_all_cell_types(self):
        """Test notebook with all types of cells."""
        nb = MarimoNotebook()
        nb.add_import_cell(["import polars as pl"])
        nb.add_data_exploration_cell()
        nb.add_visualization_cell("alt.Chart()")
        nb.add_duckdb_cell("table", "SELECT * FROM table")
        nb.add_markdown("# Summary")
        nb.add_conclusion_cell("Done")

        assert nb.cell_count() > 5
        code = nb.get_marimo_code()

        assert "polars" in code
        assert "describe" in code
        assert "alt.Chart" in code
        assert "duckdb" in code
        assert "Summary" in code
