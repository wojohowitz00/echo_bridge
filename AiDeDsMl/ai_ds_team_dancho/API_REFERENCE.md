# AI Data Science Team - API Reference

Complete API documentation for the modern data science agent framework.

## Table of Contents

1. [Core Classes](#core-classes)
2. [BaseAgentModern](#baseagentmodern)
3. [DataCleaningAgentModern](#datacleaningagentmodern)
4. [DataVisualizationAgentModern](#datavisualizationagentmodern)
5. [DataWranglingAgentModern](#datawranglingagentmodern)
6. [FeatureEngineeringAgentModern](#featureengineeringagentmodern)
7. [Utilities](#utilities)

---

## Core Classes

### DuckDBManager

Data persistence and CRUD operations with DuckDB.

```python
from ai_data_science_team.utils import DuckDBManager

manager = DuckDBManager(db_path=":memory:")
```

**Key Methods**:
- `create_table(name, data, replace=False)` - Create table from DataFrame
- `insert_data(table_name, data)` - Insert data into existing table
- `read_table(table_name)` - Read entire table as DataFrame
- `query(sql_query)` - Execute SQL query
- `table_exists(table_name)` - Check if table exists
- `list_tables()` - Get all table names
- `drop_table(table_name)` - Delete table
- `close()` - Close database connection

### MarimoNotebook

Programmatic marimo notebook creation.

```python
from ai_data_science_team.utils import MarimoNotebook

notebook = MarimoNotebook(
    title="My Analysis",
    description="Data analysis report"
)

# Add cells
notebook.add_markdown("# Title")
notebook.add_code("x = 1")
notebook.add_import_cell("import polars as pl")

# Save
path = notebook.save(filepath="/path/to/notebook.py")
```

**Key Methods**:
- `add_markdown(content)` - Add markdown cell
- `add_code(code)` - Add code cell
- `add_import_cell(imports)` - Add import cell
- `add_duckdb_cell(query)` - Add DuckDB query cell
- `save(filepath)` - Save notebook to file
- `get_marimo_code()` - Get notebook as string

---

## BaseAgentModern

Abstract base class for all modern agents. Provides DuckDB integration and marimo notebook generation.

```python
from ai_data_science_team.agents import BaseAgentModern
import polars as pl

class MyAgent(BaseAgentModern):
    def __init__(self, name, db_path=":memory:"):
        super().__init__(name, description="My agent", db_path=db_path)

    def execute(self, data):
        """Implement agent-specific logic."""
        df = to_polars(data)
        result = self._process(df)
        self.persist_to_duckdb("result_table", result)
        return {"result": result}
```

**Constructor**:
```python
BaseAgentModern(
    name: str,
    description: str = "Modern data science agent",
    db_path: str = ":memory:"
)
```

**Abstract Methods**:
- `execute(data)` - Core agent logic (must be implemented)

**Public Methods**:
- `run(data)` - Execute with automatic notebook generation
  - Returns: dict with `status`, `result`, `notebook_path`
- `persist_to_duckdb(table_name, data)` - Save DataFrame to DuckDB
- `load_from_duckdb(table_name)` - Load DataFrame from DuckDB
- `query_duckdb(sql)` - Execute raw SQL query
- `setup_notebook(title, description)` - Initialize notebook
- `generate_notebook()` - Create and save marimo notebook
- `close()` - Close database and cleanup resources

**Context Manager**:
```python
with MyAgent("name") as agent:
    results = agent.run(data)
```

---

## DataCleaningAgentModern

Advanced data cleaning with null/outlier/duplicate handling.

```python
from ai_data_science_team.agents import DataCleaningAgentModern
import polars as pl

df = pl.read_csv("data.csv")
agent = DataCleaningAgentModern(
    name="Cleaner",
    null_threshold=0.5,      # Remove columns >50% null
    outlier_method="iqr",     # "iqr" or "zscore"
    remove_duplicates=True
)

results = agent.run(df)
```

**Constructor**:
```python
DataCleaningAgentModern(
    name: str = "DataCleaningAgent",
    description: str = "Advanced data cleaning with polars",
    db_path: str = ":memory:",
    null_threshold: float = 0.5,
    outlier_method: str = "iqr",
    remove_duplicates: bool = True
)
```

**Key Methods**:

### execute(data)
Execute full cleaning workflow.
```python
results = agent.execute(df)
# Returns: {
#   "cleaned_data": pl.DataFrame,
#   "original_shape": tuple,
#   "cleaned_shape": tuple,
#   "null_report": dict,
#   "outliers_removed": int,
#   "duplicates_removed": int
# }
```

### _analyze_nulls(df)
Analyze null values in DataFrame.
```python
null_report = agent._analyze_nulls(df)
# Returns: {
#   "null_counts": dict,
#   "null_proportions": dict,
#   "columns_exceeding_threshold": list
# }
```

### _remove_outliers(df)
Remove outliers using configured method.
```python
rows_removed, df_cleaned = agent._remove_outliers(df)
```

### _handle_remaining_nulls(df)
Fill nulls with mean (numeric) or mode (categorical).
```python
df_filled = agent._handle_remaining_nulls(df)
```

**DuckDB Tables**:
- `original_data` - Original input data
- `cleaned_data` - Cleaned output data

---

## DataVisualizationAgentModern

Data exploration with chart recommendations.

```python
from ai_data_science_team.agents import DataVisualizationAgentModern
import polars as pl

df = pl.read_csv("data.csv")
agent = DataVisualizationAgentModern(
    name="Visualizer",
    max_dimensions=20
)

results = agent.run(df)
```

**Constructor**:
```python
DataVisualizationAgentModern(
    name: str = "DataVisualizationAgent",
    description: str = "Interactive data visualization with altair",
    db_path: str = ":memory:",
    max_dimensions: int = 20
)
```

**Key Methods**:

### execute(data)
Execute visualization analysis.
```python
results = agent.execute(df)
# Returns: {
#   "shape": tuple,
#   "columns": dict,
#   "numeric_columns": list,
#   "categorical_columns": list,
#   "chart_recommendations": dict
# }
```

### _analyze_columns(df)
Analyze column types and statistics.
```python
columns_info = agent._analyze_columns(df)
# Returns: {
#   "all": {
#     "column_name": {
#       "dtype": str,
#       "null_count": int,
#       "null_percent": float,
#       "min": float,  # numeric only
#       "max": float,
#       "mean": float
#     }
#   },
#   "numeric": list,
#   "categorical": list
# }
```

### _generate_recommendations(df, columns_info)
Generate chart recommendations.
```python
recommendations = agent._generate_recommendations(df, columns_info)
# Returns: {
#   "univariate": list,
#   "bivariate": list,
#   "correlation": list
# }
```

**DuckDB Tables**:
- `visualization_data` - Data used for analysis

---

## DataWranglingAgentModern

Data transformation and reshaping operations.

```python
from ai_data_science_team.agents import DataWranglingAgentModern
import polars as pl

agent = DataWranglingAgentModern("Wrangler")
df = pl.read_csv("data.csv")
```

**Constructor**:
```python
DataWranglingAgentModern(
    name: str = "DataWranglingAgent",
    description: str = "Advanced data transformation with polars",
    db_path: str = ":memory:"
)
```

**Key Methods**:

### pivot(data, index, columns, values, aggregate_function="first")
Convert long to wide format.
```python
wide_df = agent.pivot(
    df,
    index="customer_id",
    columns="month",
    values="sales",
    aggregate_function="sum"  # "first", "sum", "mean", "count"
)
```

### unpivot(data, index, variable_name="variable", value_name="value")
Convert wide to long format.
```python
long_df = agent.unpivot(
    df,
    index="customer_id",
    variable_name="metric",
    value_name="val"
)
```

### group_and_aggregate(data, group_by, aggregations)
Group and apply multiple aggregations.
```python
agg_df = agent.group_and_aggregate(
    df,
    group_by="customer_id",
    aggregations={
        "sales": ["sum", "mean", "count"],
        "quantity": "sum"
    }
)
# Supported functions: "sum", "mean", "count", "min", "max", "first", "last"
```

### join_data(left_data, right_data, left_on, right_on, how="inner")
Join two DataFrames.
```python
joined = agent.join_data(
    customers,
    transactions,
    left_on="customer_id",
    right_on="cust_id",
    how="inner"  # "inner", "left", "right", "outer", "cross"
)
```

### filter_rows(data, conditions)
Filter rows by conditions.
```python
filtered = agent.filter_rows(
    df,
    conditions={
        "status": "active",
        "region": ["US", "EU"],  # List = "in" operator
        "sales": 100  # Single value = equality
    }
)
```

### select_columns(data, columns)
Select specific columns.
```python
selected = agent.select_columns(df, columns=["id", "name", "value"])
```

### drop_columns(data, columns)
Remove columns.
```python
dropped = agent.drop_columns(df, columns=["temp_col", "debug"])
```

### sort_data(data, by, descending=False)
Sort DataFrame.
```python
sorted_df = agent.sort_data(
    df,
    by=["customer_id", "date"],
    descending=False
)
```

### rename_columns(data, mapping)
Rename columns.
```python
renamed = agent.rename_columns(
    df,
    mapping={"col_old": "col_new", "x": "feature_x"}
)
```

### get_unique_values(data, column)
Extract unique values.
```python
unique_values = agent.get_unique_values(df, "category")
# Returns: list
```

**DuckDB Tables**:
- `original_wrangling_data` - Original input data

---

## FeatureEngineeringAgentModern

Feature transformation and creation for machine learning.

```python
from ai_data_science_team.agents import FeatureEngineeringAgentModern
import polars as pl

agent = FeatureEngineeringAgentModern("FeatureEngineer")
df = pl.read_csv("data.csv")
```

**Constructor**:
```python
FeatureEngineeringAgentModern(
    name: str = "FeatureEngineeringAgent",
    description: str = "Advanced feature engineering with polars",
    db_path: str = ":memory:"
)
```

**Key Methods**:

### scale_features(data, columns=None, method="standardize")
Scale numeric features.
```python
scaled = agent.scale_features(
    df,
    columns=["age", "income"],
    method="standardize"  # "standardize" (z-score) or "normalize" (0-1)
)
# Creates: column_scaled for each scaled column
```

### create_polynomial_features(data, columns=None, degree=2)
Create polynomial features.
```python
poly = agent.create_polynomial_features(
    df,
    columns=["income"],
    degree=3
)
# Creates: column_pow2, column_pow3
```

### create_interaction_features(data, columns=None)
Create pairwise interactions.
```python
interactions = agent.create_interaction_features(
    df,
    columns=["age", "income"]
)
# Creates: age_x_income
```

### one_hot_encode(data, columns=None)
One-hot encode categorical features.
```python
encoded = agent.one_hot_encode(
    df,
    columns=["gender", "category"]
)
# Creates: column_value for each category value
```

### label_encode(data, column)
Label encode categorical column.
```python
encoded_df, mapping = agent.label_encode(
    df,
    column="color"
)
# Returns: (encoded_df with column_encoded, mapping dict)
```

### bin_features(data, column, n_bins=5)
Discretize numeric feature.
```python
binned = agent.bin_features(
    df,
    column="age",
    n_bins=10
)
# Creates: column_binned with categorical intervals
```

### remove_low_variance_features(data, threshold=0.01)
Remove low variance features.
```python
filtered, removed = agent.remove_low_variance_features(
    df,
    threshold=0.01
)
# Returns: (filtered_df, list_of_removed_columns)
```

### get_feature_statistics(data)
Calculate feature statistics.
```python
stats = agent.get_feature_statistics(df)
# Returns: {
#   "column_name": {
#     "dtype": str,
#     "mean": float,
#     "std": float,
#     "min": float,
#     "max": float,
#     "median": float,
#     "null_count": int,
#     "variance": float
#   }
# }
```

### get_feature_correlations(data)
Calculate correlations between numeric features.
```python
corr_matrix = agent.get_feature_correlations(df)
# Returns: pl.DataFrame (correlation matrix)
```

**DuckDB Tables**:
- `feature_original_data` - Original input data

---

## Utilities

### to_polars(data)
Convert any input format to polars DataFrame.

```python
from ai_data_science_team.utils import to_polars

# From pandas
import pandas as pd
pdf = pd.DataFrame({"a": [1, 2, 3]})
df = to_polars(pdf)

# From dict
d = {"x": [1, 2, 3], "y": [4, 5, 6]}
df = to_polars(d)

# From list of dicts
lst = [{"a": 1}, {"a": 2}]
df = to_polars(lst)

# From polars (returns as-is)
import polars as pl
df = pl.DataFrame({"x": [1, 2, 3]})
df = to_polars(df)
```

---

## Common Workflows

### Data Cleaning Pipeline
```python
from ai_data_science_team.agents import DataCleaningAgentModern
import polars as pl

df = pl.read_csv("raw_data.csv")

cleaner = DataCleaningAgentModern(
    name="RawDataCleaner",
    null_threshold=0.5,
    outlier_method="iqr"
)

results = cleaner.run(df)
print(f"Cleaned {results['duplicates_removed']} duplicates")
print(f"Removed {results['outliers_removed']} outliers")
print(f"Shape: {results['original_shape']} → {results['cleaned_shape']}")
```

### Exploratory Data Analysis
```python
from ai_data_science_team.agents import DataVisualizationAgentModern
import polars as pl

df = pl.read_csv("clean_data.csv")

viz = DataVisualizationAgentModern("EDA")
results = viz.run(df)

# Open notebook
print(f"Analysis available at: {results['notebook_path']}")
```

### Data Transformation
```python
from ai_data_science_team.agents import DataWranglingAgentModern
import polars as pl

df = pl.read_csv("data.csv")
agent = DataWranglingAgentModern("Transform")

# Aggregate by group
sales_by_region = agent.group_and_aggregate(
    df,
    group_by="region",
    aggregations={"sales": ["sum", "mean"], "quantity": "count"}
)

# Pivot for reporting
pivot_report = agent.pivot(
    df,
    index="region",
    columns="product",
    values="sales",
    aggregate_function="sum"
)
```

### Feature Engineering
```python
from ai_data_science_team.agents import FeatureEngineeringAgentModern
import polars as pl

df = pl.read_csv("data.csv")
fe = FeatureEngineeringAgentModern("FeatureEng")

# Scale numeric features
scaled = fe.scale_features(df, method="standardize")

# Create polynomial features
poly = fe.create_polynomial_features(scaled, degree=2)

# Encode categorical
encoded = fe.one_hot_encode(poly, columns=["category"])

# Get statistics
stats = fe.get_feature_statistics(encoded)
```

### Multi-Agent Workflow
```python
from ai_data_science_team.agents import (
    DataCleaningAgentModern,
    DataVisualizationAgentModern,
    DataWranglingAgentModern,
    FeatureEngineeringAgentModern
)
import polars as pl

df = pl.read_csv("raw_data.csv")

# Step 1: Clean
cleaner = DataCleaningAgentModern("Cleaner")
clean_results = cleaner.run(df)
clean_df = clean_results["result"]["cleaned_data"]

# Step 2: Visualize
viz = DataVisualizationAgentModern("Visualizer")
viz_results = viz.run(clean_df)

# Step 3: Wrangle
wrangler = DataWranglingAgentModern("Wrangler")
agg_df = wrangler.group_and_aggregate(
    clean_df,
    group_by="customer_id",
    aggregations={"amount": ["sum", "mean"]}
)

# Step 4: Engineer Features
fe = FeatureEngineeringAgentModern("FE")
fe_results = fe.run(agg_df)

print(f"Pipeline complete!")
print(f"- Cleaning notebook: {clean_results['notebook_path']}")
print(f"- Visualization notebook: {viz_results['notebook_path']}")
print(f"- Feature engineering notebook: {fe_results['notebook_path']}")
```

---

## Error Handling

All agents use standard exception handling:

```python
from ai_data_science_team.agents import DataCleaningAgentModern

agent = DataCleaningAgentModern("Cleaner")

try:
    results = agent.run(data)
except Exception as e:
    print(f"Error: {e}")
finally:
    agent.close()  # Always cleanup
```

With context manager (recommended):

```python
from ai_data_science_team.agents import DataCleaningAgentModern

with DataCleaningAgentModern("Cleaner") as agent:
    results = agent.run(data)
    # Automatic cleanup on exit
```

---

## Version Info

- **Framework**: AI Data Science Team - Modern Python Stack
- **Python**: 3.9+
- **Key Dependencies**:
  - polars (data processing)
  - duckdb (data persistence)
  - marimo (interactive notebooks)
  - ruff (code quality)
  - uv (package management)

---

## More Resources

- [Architecture Guide](ARCHITECTURE_GUIDE.md)
- [Getting Started](GETTING_STARTED.md)
- [Best Practices](BEST_PRACTICES.md)
- [Example Notebooks](examples/)
