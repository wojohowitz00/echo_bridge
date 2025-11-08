"""Tests for polars tools."""

import polars as pl
import pytest

from ai_data_science_team.tools.polars_tools import PolarsTools


class TestDuplicateDetection:
    """Test duplicate detection."""

    def test_detect_duplicates_all_columns(self):
        """Test finding duplicate rows across all columns."""
        df = pl.DataFrame({"a": [1, 2, 1, 3], "b": [4, 5, 4, 6]})
        dupes = PolarsTools.detect_duplicates(df)
        assert len(dupes) == 2  # Rows with duplicates
        assert dupes["a"].to_list() == [1, 1]

    def test_detect_duplicates_subset(self):
        """Test finding duplicates in subset of columns."""
        df = pl.DataFrame({"a": [1, 2, 1, 3], "b": [4, 5, 6, 7]})
        dupes = PolarsTools.detect_duplicates(df, subset=["a"])
        assert len(dupes) == 2
        assert dupes["a"].to_list() == [1, 1]

    def test_no_duplicates(self):
        """Test when there are no duplicates."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        dupes = PolarsTools.detect_duplicates(df)
        assert len(dupes) == 0

    def test_all_duplicates(self):
        """Test when all rows are duplicates."""
        df = pl.DataFrame({"a": [1, 1, 1], "b": [2, 2, 2]})
        dupes = PolarsTools.detect_duplicates(df)
        assert len(dupes) == 3


class TestRemoveDuplicates:
    """Test duplicate removal."""

    def test_remove_duplicates(self):
        """Test removing duplicate rows."""
        df = pl.DataFrame({"a": [1, 2, 1, 3], "b": [4, 5, 4, 6]})
        unique = PolarsTools.remove_duplicates(df)
        assert len(unique) == 3
        # unique() doesn't guarantee order, so sort before comparing
        assert sorted(unique["a"].to_list()) == [1, 2, 3]

    def test_remove_duplicates_subset(self):
        """Test removing duplicates based on subset of columns."""
        df = pl.DataFrame({"a": [1, 2, 1, 3], "b": [4, 5, 6, 7]})
        unique = PolarsTools.remove_duplicates(df, subset=["a"])
        assert len(unique) == 3

    def test_remove_duplicates_no_dupes(self):
        """Test removing duplicates when there are none."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        unique = PolarsTools.remove_duplicates(df)
        assert len(unique) == 3


class TestNullHandling:
    """Test null value handling."""

    def test_detect_nulls(self):
        """Test null value detection."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
        nulls = PolarsTools.detect_nulls(df)
        assert nulls == {"a": 1, "b": 1}

    def test_detect_nulls_no_nulls(self):
        """Test detecting nulls when there are none."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        nulls = PolarsTools.detect_nulls(df)
        assert nulls == {"a": 0, "b": 0}

    def test_detect_nulls_all_nulls(self):
        """Test detecting nulls when all values are null."""
        df = pl.DataFrame({"a": [None, None, None]})
        nulls = PolarsTools.detect_nulls(df)
        assert nulls == {"a": 3}

    def test_drop_nulls(self):
        """Test dropping null rows."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, 6]})
        clean = PolarsTools.drop_nulls(df)
        assert len(clean) == 2
        assert clean["a"].to_list() == [1, 3]

    def test_drop_nulls_subset(self):
        """Test dropping nulls from subset of columns."""
        df = pl.DataFrame({"a": [1, None, 3], "b": [4, None, 6]})
        clean = PolarsTools.drop_nulls(df, subset=["a"])
        assert len(clean) == 2
        assert clean["a"].to_list() == [1, 3]

    def test_drop_nulls_no_nulls(self):
        """Test dropping nulls when there are none."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        clean = PolarsTools.drop_nulls(df)
        assert len(clean) == 3

    def test_fill_nulls_mean(self):
        """Test filling nulls with mean."""
        df = pl.DataFrame({"a": [1.0, None, 3.0], "b": [4.0, 5.0, 6.0]})
        filled = PolarsTools.fill_nulls(df, strategy="mean")
        # Mean of [1.0, 3.0] = 2.0
        assert filled["a"][1] == 2.0

    def test_fill_nulls_median(self):
        """Test filling nulls with median."""
        df = pl.DataFrame({"a": [1.0, None, 5.0], "b": [4.0, 5.0, 6.0]})
        filled = PolarsTools.fill_nulls(df, strategy="median")
        # Median of [1.0, 5.0] = 3.0
        assert filled["a"][1] == 3.0

    def test_fill_nulls_forward(self):
        """Test filling nulls with forward fill."""
        df = pl.DataFrame({"a": [1, None, 3]})
        filled = PolarsTools.fill_nulls(df, strategy="forward")
        assert filled["a"][1] == 1

    def test_fill_nulls_backward(self):
        """Test filling nulls with backward fill."""
        df = pl.DataFrame({"a": [1, None, 3]})
        filled = PolarsTools.fill_nulls(df, strategy="backward")
        assert filled["a"][1] == 3

    def test_fill_nulls_value(self):
        """Test filling nulls with specific value."""
        df = pl.DataFrame({"a": [1, None, 3]})
        filled = PolarsTools.fill_nulls(df, strategy="value", value=99)
        assert filled["a"][1] == 99

    def test_fill_nulls_value_requires_value_param(self):
        """Test that fill_nulls with 'value' strategy requires value parameter."""
        df = pl.DataFrame({"a": [1, None, 3]})
        with pytest.raises(ValueError):
            PolarsTools.fill_nulls(df, strategy="value")

    def test_fill_nulls_invalid_strategy(self):
        """Test that invalid strategy raises ValueError."""
        df = pl.DataFrame({"a": [1, None, 3]})
        with pytest.raises(ValueError):
            PolarsTools.fill_nulls(df, strategy="invalid")


class TestSummaryStats:
    """Test summary statistics."""

    def test_get_summary(self):
        """Test getting summary statistics."""
        df = pl.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
        summary = PolarsTools.get_summary(df)
        assert isinstance(summary, pl.DataFrame)
        assert len(summary) > 0

    def test_get_summary_with_nulls(self):
        """Test summary statistics with null values."""
        df = pl.DataFrame({"a": [1, None, 3, 4, 5]})
        summary = PolarsTools.get_summary(df)
        assert isinstance(summary, pl.DataFrame)

    def test_get_dtypes(self):
        """Test getting data types."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [1.0, 2.0, 3.0]})
        dtypes = PolarsTools.get_dtypes(df)
        assert "a" in dtypes
        assert "b" in dtypes
        assert "c" in dtypes

    def test_get_dtypes_empty(self):
        """Test getting dtypes from empty DataFrame."""
        df = pl.DataFrame({"a": []})
        dtypes = PolarsTools.get_dtypes(df)
        assert "a" in dtypes


class TestColumnManipulation:
    """Test column manipulation functions."""

    def test_standardize_column_names(self):
        """Test standardizing column names."""
        df = pl.DataFrame({"First Name": [1], "Last Name": [2], "AGE": [3]})
        clean = PolarsTools.standardize_column_names(df)
        assert clean.columns == ["first_name", "last_name", "age"]

    def test_standardize_column_names_already_clean(self):
        """Test standardizing already clean column names."""
        df = pl.DataFrame({"first_name": [1], "last_name": [2]})
        clean = PolarsTools.standardize_column_names(df)
        assert clean.columns == ["first_name", "last_name"]

    def test_standardize_column_names_special_chars(self):
        """Test standardizing column names with special characters."""
        df = pl.DataFrame({"First Name": [1], "Last  Name": [2]})
        clean = PolarsTools.standardize_column_names(df)
        assert "first_name" in clean.columns
        assert "last__name" in clean.columns


class TestOutlierDetection:
    """Test outlier detection."""

    def test_detect_outliers_iqr(self):
        """Test IQR-based outlier detection."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 100]})  # 100 is outlier
        outliers = PolarsTools.detect_outliers(df, "value", method="iqr")
        assert len(outliers) > 0
        assert 100 in outliers["value"].to_list()

    def test_detect_outliers_iqr_no_outliers(self):
        """Test IQR outlier detection when there are no outliers."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5]})
        outliers = PolarsTools.detect_outliers(df, "value", method="iqr")
        assert len(outliers) == 0

    def test_detect_outliers_iqr_custom_threshold(self):
        """Test IQR outlier detection with custom threshold."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5, 10]})
        outliers = PolarsTools.detect_outliers(df, "value", method="iqr", threshold=0.5)
        assert len(outliers) > 0

    def test_detect_outliers_zscore(self):
        """Test z-score based outlier detection."""
        df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0]})
        outliers = PolarsTools.detect_outliers(df, "value", method="zscore", threshold=2.0)
        assert len(outliers) > 0
        assert 100.0 in outliers["value"].to_list()

    def test_detect_outliers_zscore_no_outliers(self):
        """Test z-score outlier detection when there are no outliers."""
        df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0]})
        outliers = PolarsTools.detect_outliers(df, "value", method="zscore", threshold=10.0)
        assert len(outliers) == 0

    def test_detect_outliers_invalid_method(self):
        """Test that invalid method raises ValueError."""
        df = pl.DataFrame({"value": [1, 2, 3, 4, 5]})
        with pytest.raises(ValueError):
            PolarsTools.detect_outliers(df, "value", method="invalid")


class TestColumnInfo:
    """Test column information functions."""

    def test_get_column_info(self):
        """Test getting column information."""
        df = pl.DataFrame({"a": [1, 2, None], "b": ["x", "y", "z"]})
        info = PolarsTools.get_column_info(df)
        assert isinstance(info, pl.DataFrame)
        assert "column_name" in info.columns
        assert "dtype" in info.columns
        assert "null_count" in info.columns
        assert "unique_count" in info.columns

    def test_get_column_info_empty(self):
        """Test getting column info from empty DataFrame."""
        df = pl.DataFrame({"a": []})
        info = PolarsTools.get_column_info(df)
        assert len(info) == 1  # One column

    def test_get_numeric_columns(self):
        """Test getting numeric column names."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"], "c": [1.0, 2.0, 3.0]})
        numeric = PolarsTools.get_numeric_columns(df)
        assert "a" in numeric
        assert "c" in numeric
        assert "b" not in numeric

    def test_get_numeric_columns_all_numeric(self):
        """Test getting numeric columns when all are numeric."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        numeric = PolarsTools.get_numeric_columns(df)
        assert len(numeric) == 2

    def test_get_numeric_columns_no_numeric(self):
        """Test getting numeric columns when there are none."""
        df = pl.DataFrame({"a": ["x", "y", "z"], "b": ["1", "2", "3"]})
        numeric = PolarsTools.get_numeric_columns(df)
        assert len(numeric) == 0

    def test_get_categorical_columns(self):
        """Test getting categorical column names."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        categorical = PolarsTools.get_categorical_columns(df)
        assert "b" in categorical
        assert "a" not in categorical

    def test_get_categorical_columns_all_categorical(self):
        """Test getting categorical columns when all are categorical."""
        df = pl.DataFrame({"a": ["x", "y", "z"], "b": ["1", "2", "3"]})
        categorical = PolarsTools.get_categorical_columns(df)
        assert len(categorical) == 2

    def test_get_categorical_columns_no_categorical(self):
        """Test getting categorical columns when there are none."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4.0, 5.0, 6.0]})
        categorical = PolarsTools.get_categorical_columns(df)
        assert len(categorical) == 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe(self):
        """Test functions with empty DataFrame."""
        df = pl.DataFrame({"a": []})

        # Should not raise errors
        nulls = PolarsTools.detect_nulls(df)
        assert nulls == {"a": 0}

        summary = PolarsTools.get_summary(df)
        assert isinstance(summary, pl.DataFrame)

        dtypes = PolarsTools.get_dtypes(df)
        assert "a" in dtypes

    def test_single_row(self):
        """Test functions with single row DataFrame."""
        df = pl.DataFrame({"a": [1], "b": [2]})

        shape = df.shape
        assert shape == (1, 2)

        dtypes = PolarsTools.get_dtypes(df)
        assert len(dtypes) == 2

    def test_single_column(self):
        """Test functions with single column DataFrame."""
        df = pl.DataFrame({"a": [1, 2, 3]})

        shape = df.shape
        assert shape == (3, 1)

        numeric = PolarsTools.get_numeric_columns(df)
        assert len(numeric) == 1

    def test_large_dataframe(self):
        """Test functions with large DataFrame."""
        df = pl.DataFrame({"a": list(range(10000)), "b": list(range(10000))})

        dtypes = PolarsTools.get_dtypes(df)
        assert len(dtypes) == 2

        summary = PolarsTools.get_summary(df)
        assert isinstance(summary, pl.DataFrame)


class TestIntegration:
    """Integration tests combining multiple operations."""

    def test_full_cleaning_pipeline(self):
        """Test a full data cleaning pipeline."""
        # Create dirty data
        df = pl.DataFrame(
            {
                "First Name": ["Alice", "Bob", "Alice", None, "Charlie"],
                "Age": [25, None, 25, 30, 35],
                "Score": [85, 90, 85, 92, 88],
            }
        )

        # Clean column names
        df = PolarsTools.standardize_column_names(df)
        assert "first_name" in df.columns

        # Remove duplicates
        df = PolarsTools.remove_duplicates(df)
        assert len(df) <= 5

        # Fill nulls
        df = PolarsTools.fill_nulls(df, strategy="mean")

        # Get info
        info = PolarsTools.get_column_info(df)
        assert len(info) == 3

    def test_outlier_removal_pipeline(self):
        """Test outlier detection and removal pipeline."""
        df = pl.DataFrame({"value": [1.0, 2.0, 3.0, 4.0, 5.0, 100.0, 200.0]})

        # Detect outliers using z-score (more sensitive)
        outliers = PolarsTools.detect_outliers(df, "value", method="zscore", threshold=2.0)
        assert len(outliers) > 0
        # At least one extreme value should be detected
        assert any(val > 50.0 for val in outliers["value"].to_list())

        # Simple check that outliers were identified
        assert len(df) > len(outliers)
