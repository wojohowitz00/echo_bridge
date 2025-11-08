"""Tests for DataFrame compatibility layer."""

import pandas as pd
import polars as pl
import pytest

from ai_data_science_team.utils.dataframe_compat import (
    describe,
    get_columns,
    get_dtypes,
    get_shape,
    head,
    is_dataframe,
    is_pandas,
    is_polars,
    sample,
    tail,
    to_pandas,
    to_polars,
)


class TestToPolars:
    """Test to_polars conversion function."""

    def test_polars_dataframe_passthrough(self):
        """Test that polars DataFrame is returned unchanged."""
        df = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        result = to_polars(df)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (3, 2)

    def test_pandas_to_polars_conversion(self):
        """Test pandas DataFrame conversion."""
        pdf = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        plf = to_polars(pdf)
        assert isinstance(plf, pl.DataFrame)
        assert plf.shape == (3, 2)
        assert plf.columns == ["a", "b"]

    def test_dict_to_polars_conversion(self):
        """Test dict conversion."""
        data = {"a": [1, 2, 3], "b": [4, 5, 6]}
        df = to_polars(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)

    def test_list_of_dicts_conversion(self):
        """Test list of dicts conversion."""
        data = [{"a": 1, "b": 4}, {"a": 2, "b": 5}, {"a": 3, "b": 6}]
        df = to_polars(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 2)

    def test_list_of_lists_conversion(self):
        """Test list of lists conversion."""
        data = [[1, 2, 3], [4, 5, 6]]
        df = to_polars(data)
        assert isinstance(df, pl.DataFrame)
        # polars treats [[1,2,3], [4,5,6]] as 3 rows with 2 columns
        assert df.shape == (3, 2)

    def test_single_list_conversion(self):
        """Test single list conversion."""
        data = [1, 2, 3]
        df = to_polars(data)
        assert isinstance(df, pl.DataFrame)
        assert df.shape == (3, 1)
        assert df.columns == ["column_0"]

    def test_empty_list_raises_error(self):
        """Test that empty list raises TypeError."""
        with pytest.raises(TypeError):
            to_polars([])

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError):
            to_polars("invalid")

    def test_none_raises_error(self):
        """Test that None raises TypeError."""
        with pytest.raises(TypeError):
            to_polars(None)

    def test_numeric_value_raises_error(self):
        """Test that numeric value raises TypeError."""
        with pytest.raises(TypeError):
            to_polars(42)


class TestToPandas:
    """Test to_pandas conversion function."""

    def test_polars_to_pandas_conversion(self):
        """Test polars to pandas conversion."""
        plf = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        pdf = to_pandas(plf)
        assert isinstance(pdf, pd.DataFrame)
        assert pdf.shape == (3, 2)

    def test_pandas_passthrough(self):
        """Test pandas DataFrame is returned unchanged."""
        pdf = pd.DataFrame({"a": [1, 2, 3]})
        result = to_pandas(pdf)
        assert isinstance(result, pd.DataFrame)
        assert result.shape == (3, 1)

    def test_invalid_type_raises_error(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError):
            to_pandas([1, 2, 3])

    def test_none_raises_error(self):
        """Test that None raises TypeError."""
        with pytest.raises(TypeError):
            to_pandas(None)

    def test_dict_raises_error(self):
        """Test that dict raises TypeError."""
        with pytest.raises(TypeError):
            to_pandas({"a": [1, 2, 3]})


class TestHelperFunctions:
    """Test helper functions."""

    def test_is_polars(self):
        """Test is_polars detection."""
        plf = pl.DataFrame({"a": [1, 2, 3]})
        pdf = pd.DataFrame({"a": [1, 2, 3]})
        assert is_polars(plf) is True
        assert is_polars(pdf) is False
        assert is_polars([1, 2, 3]) is False
        assert is_polars(None) is False

    def test_is_pandas(self):
        """Test is_pandas detection."""
        pdf = pd.DataFrame({"a": [1, 2, 3]})
        plf = pl.DataFrame({"a": [1, 2, 3]})
        assert is_pandas(pdf) is True
        assert is_pandas(plf) is False
        assert is_pandas([1, 2, 3]) is False
        assert is_pandas(None) is False

    def test_is_dataframe(self):
        """Test is_dataframe detection."""
        plf = pl.DataFrame({"a": [1, 2, 3]})
        pdf = pd.DataFrame({"a": [1, 2, 3]})
        assert is_dataframe(plf) is True
        assert is_dataframe(pdf) is True
        assert is_dataframe([1, 2, 3]) is False
        assert is_dataframe(None) is False
        assert is_dataframe({"a": [1, 2, 3]}) is False

    def test_get_shape_polars(self):
        """Test get_shape with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert get_shape(plf) == (3, 2)

    def test_get_shape_pandas(self):
        """Test get_shape with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert get_shape(pdf) == (3, 2)

    def test_get_shape_invalid_raises_error(self):
        """Test get_shape with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            get_shape([1, 2, 3])

    def test_get_columns_polars(self):
        """Test get_columns with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert get_columns(plf) == ["a", "b"]

    def test_get_columns_pandas(self):
        """Test get_columns with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        assert get_columns(pdf) == ["a", "b"]

    def test_get_columns_invalid_raises_error(self):
        """Test get_columns with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            get_columns([1, 2, 3])

    def test_get_dtypes_polars(self):
        """Test get_dtypes with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        dtypes = get_dtypes(plf)
        assert "a" in dtypes
        assert "b" in dtypes
        assert "Int" in dtypes["a"] or "i64" in dtypes["a"].lower()
        assert "Utf8" in dtypes["b"] or "str" in dtypes["b"].lower()

    def test_get_dtypes_pandas(self):
        """Test get_dtypes with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        dtypes = get_dtypes(pdf)
        assert "a" in dtypes
        assert "b" in dtypes

    def test_get_dtypes_invalid_raises_error(self):
        """Test get_dtypes with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            get_dtypes([1, 2, 3])


class TestSampleFunction:
    """Test sample function."""

    def test_sample_polars(self):
        """Test sample with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        sampled = sample(plf, n=3)
        assert isinstance(sampled, pl.DataFrame)
        assert len(sampled) == 3

    def test_sample_pandas(self):
        """Test sample with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        sampled = sample(pdf, n=3)
        assert isinstance(sampled, pd.DataFrame)
        assert len(sampled) == 3

    def test_sample_larger_than_df(self):
        """Test sample when n is larger than DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3]})
        sampled = sample(plf, n=10)
        assert len(sampled) == 3  # Should return all rows

    def test_sample_invalid_raises_error(self):
        """Test sample with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            sample([1, 2, 3], n=2)


class TestHeadFunction:
    """Test head function."""

    def test_head_polars(self):
        """Test head with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = head(plf, n=3)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["a"].to_list() == [1, 2, 3]

    def test_head_pandas(self):
        """Test head with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = head(pdf, n=3)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_head_default(self):
        """Test head with default n=5."""
        plf = pl.DataFrame({"a": list(range(10))})
        result = head(plf)
        assert len(result) == 5

    def test_head_invalid_raises_error(self):
        """Test head with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            head([1, 2, 3])


class TestTailFunction:
    """Test tail function."""

    def test_tail_polars(self):
        """Test tail with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = tail(plf, n=3)
        assert isinstance(result, pl.DataFrame)
        assert len(result) == 3
        assert result["a"].to_list() == [3, 4, 5]

    def test_tail_pandas(self):
        """Test tail with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = tail(pdf, n=3)
        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3

    def test_tail_default(self):
        """Test tail with default n=5."""
        plf = pl.DataFrame({"a": list(range(10))})
        result = tail(plf)
        assert len(result) == 5

    def test_tail_invalid_raises_error(self):
        """Test tail with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            tail([1, 2, 3])


class TestDescribeFunction:
    """Test describe function."""

    def test_describe_polars(self):
        """Test describe with polars DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = describe(plf)
        assert isinstance(result, pl.DataFrame)
        assert len(result) > 0

    def test_describe_pandas(self):
        """Test describe with pandas DataFrame."""
        pdf = pd.DataFrame({"a": [1, 2, 3, 4, 5]})
        result = describe(pdf)
        assert isinstance(result, pd.DataFrame)
        assert len(result) > 0

    def test_describe_invalid_raises_error(self):
        """Test describe with invalid input raises TypeError."""
        with pytest.raises(TypeError):
            describe([1, 2, 3])


class TestRoundTripConversions:
    """Test round-trip conversions between pandas and polars."""

    def test_pandas_to_polars_to_pandas(self):
        """Test pandas → polars → pandas round trip."""
        pdf_original = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        plf = to_polars(pdf_original)
        pdf_result = to_pandas(plf)

        assert isinstance(pdf_result, pd.DataFrame)
        assert pdf_result.shape == pdf_original.shape
        assert list(pdf_result.columns) == list(pdf_original.columns)

    def test_polars_to_pandas_to_polars(self):
        """Test polars → pandas → polars round trip."""
        plf_original = pl.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
        pdf = to_pandas(plf_original)
        plf_result = to_polars(pdf)

        assert isinstance(plf_result, pl.DataFrame)
        assert plf_result.shape == plf_original.shape
        assert plf_result.columns == plf_original.columns


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_dataframe_polars(self):
        """Test with empty polars DataFrame."""
        plf = pl.DataFrame({"a": []})
        result = to_polars(plf)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (0, 1)

    def test_empty_dataframe_pandas(self):
        """Test with empty pandas DataFrame."""
        pdf = pd.DataFrame({"a": []})
        result = to_polars(pdf)
        assert isinstance(result, pl.DataFrame)
        assert result.shape == (0, 1)

    def test_single_row_dataframe(self):
        """Test with single row DataFrame."""
        plf = pl.DataFrame({"a": [1], "b": [2]})
        result = to_polars(plf)
        assert result.shape == (1, 2)

    def test_single_column_dataframe(self):
        """Test with single column DataFrame."""
        plf = pl.DataFrame({"a": [1, 2, 3]})
        result = to_polars(plf)
        assert result.shape == (3, 1)

    def test_dataframe_with_nulls(self):
        """Test with DataFrame containing null values."""
        plf = pl.DataFrame({"a": [1, None, 3], "b": [4, 5, None]})
        pdf = to_pandas(plf)
        plf_result = to_polars(pdf)

        assert isinstance(plf_result, pl.DataFrame)
        assert plf_result.shape == (3, 2)
