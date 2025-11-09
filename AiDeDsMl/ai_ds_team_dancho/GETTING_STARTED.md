# Getting Started - Modern Data Science Agent Framework

Quick start guide to get up and running with the AI Data Science Team framework.

## Installation

### Prerequisites
- Python 3.9+
- uv (package manager)

### Setup

1. **Clone repository**
   ```bash
   git clone <repo-url>
   cd ai_ds_team_dancho
   ```

2. **Install with uv** (recommended)
   ```bash
   uv sync
   ```

   Or with pip:
   ```bash
   pip install -e .
   ```

3. **Verify installation**
   ```bash
   python -c "from ai_data_science_team.agents import DataCleaningAgentModern; print('✅ Ready!')"
   ```

---

## Your First Analysis (5 minutes)

### Step 1: Create Sample Data

```python
import polars as pl

# Create sample data
df = pl.DataFrame({
    "customer_id": [1, 2, 3, 4, 5],
    "age": [25, 35, 45, None, 55],
    "purchase_amount": [100.0, 200.0, 150.0, 1000.0, 75.0],
    "category": ["A", "B", "A", "C", "B"]
})

print(df)
```

### Step 2: Clean Data

```python
from ai_data_science_team.agents import DataCleaningAgentModern

# Create cleaning agent
cleaner = DataCleaningAgentModern(
    name="DataCleaner",
    null_threshold=0.5,
    outlier_method="iqr"
)

# Run cleaning
results = cleaner.run(df)

# Check results
print(f"Original: {results['original_shape']}")
print(f"Cleaned: {results['cleaned_shape']}")
print(f"Outliers removed: {results['outliers_removed']}")
print(f"Duplicates removed: {results['duplicates_removed']}")

# Get cleaned data
cleaned_df = results["result"]["cleaned_data"]
print(cleaned_df)

# View notebook
print(f"Report: {results['notebook_path']}")
```

### Step 3: Visualize Data

```python
from ai_data_science_team.agents import DataVisualizationAgentModern

# Create visualization agent
viz = DataVisualizationAgentModern("DataExplorer")

# Run analysis
results = viz.run(cleaned_df)

# Check recommendations
print(f"Numeric columns: {results['numeric_columns']}")
print(f"Categorical columns: {results['categorical_columns']}")
print(f"Chart recommendations: {results['chart_recommendations']}")

# View notebook
print(f"Visualization: {results['notebook_path']}")
```

---

## Common Use Cases

### Use Case 1: Data Cleaning Pipeline

Clean messy raw data:

```python
from ai_data_science_team.agents import DataCleaningAgentModern
import polars as pl

# Load raw data
df = pl.read_csv("raw_data.csv")

# Clean
agent = DataCleaningAgentModern(
    name="DataCleaner",
    null_threshold=0.5,      # Remove columns >50% null
    outlier_method="iqr",    # IQR method for outliers
    remove_duplicates=True   # Remove exact duplicates
)

results = agent.run(df)
clean_df = results["result"]["cleaned_data"]

# Save cleaned data
clean_df.write_csv("clean_data.csv")
```

### Use Case 2: Exploratory Data Analysis

Understand your data:

```python
from ai_data_science_team.agents import DataVisualizationAgentModern
import polars as pl

df = pl.read_csv("clean_data.csv")

# Analyze
agent = DataVisualizationAgentModern("EDA")
results = agent.run(df)

# Get insights
print("Numeric columns:", results['numeric_columns'])
print("Categorical columns:", results['categorical_columns'])
print("Recommendations:", results['chart_recommendations'])

# Open notebook to explore
import os
os.system(f"marimo edit {results['notebook_path']}")
```

### Use Case 3: Data Aggregation & Reporting

Summarize data by groups:

```python
from ai_data_science_team.agents import DataWranglingAgentModern
import polars as pl

df = pl.read_csv("sales_data.csv")

wrangler = DataWranglingAgentModern("SalesAnalyzer")

# Aggregate by customer
customer_summary = wrangler.group_and_aggregate(
    df,
    group_by="customer_id",
    aggregations={
        "amount": ["sum", "mean", "count"],
        "date": "first"
    }
)

# Create pivot table
pivot = wrangler.pivot(
    df,
    index="customer_id",
    columns="month",
    values="amount",
    aggregate_function="sum"
)

print(customer_summary)
print(pivot)

# Save results
customer_summary.write_csv("customer_summary.csv")
pivot.write_csv("sales_pivot.csv")
```

### Use Case 4: Feature Engineering

Prepare data for ML:

```python
from ai_data_science_team.agents import FeatureEngineeringAgentModern
import polars as pl

df = pl.read_csv("data.csv")

fe = FeatureEngineeringAgentModern("MLPrep")

# Scale numeric features
scaled = fe.scale_features(
    df,
    columns=["age", "income", "duration"],
    method="standardize"
)

# Create polynomial features
poly = fe.create_polynomial_features(
    scaled,
    columns=["age"],
    degree=2
)

# Encode categorical
encoded = fe.one_hot_encode(
    poly,
    columns=["gender", "occupation"]
)

# Get feature statistics
stats = fe.get_feature_statistics(encoded)
print("Feature statistics:")
for col, col_stats in stats.items():
    print(f"  {col}: mean={col_stats['mean']:.2f}, std={col_stats['std']:.2f}")

# Save engineered features
encoded.write_csv("features.csv")
```

### Use Case 5: Complete ML Pipeline

End-to-end data science workflow:

```python
from ai_data_science_team.agents import (
    DataCleaningAgentModern,
    DataVisualizationAgentModern,
    DataWranglingAgentModern,
    FeatureEngineeringAgentModern
)
import polars as pl

print("Starting ML Pipeline...")

# Step 1: Load data
print("1. Loading data...")
df = pl.read_csv("raw_data.csv")
print(f"   Loaded: {df.shape}")

# Step 2: Clean data
print("2. Cleaning data...")
with DataCleaningAgentModern("Cleaner") as agent:
    clean_results = agent.run(df)
    clean_df = clean_results["result"]["cleaned_data"]
print(f"   Cleaned: {clean_df.shape}")

# Step 3: Explore data
print("3. Exploring data...")
with DataVisualizationAgentModern("EDA") as agent:
    eda_results = agent.run(clean_df)
print(f"   Found {len(eda_results['numeric_columns'])} numeric columns")

# Step 4: Wrangle data
print("4. Wrangling data...")
with DataWranglingAgentModern("Wrangler") as agent:
    agg_df = agent.group_and_aggregate(
        clean_df,
        group_by=["customer_id"],
        aggregations={"amount": ["sum", "mean"], "date": "count"}
    )
print(f"   Aggregated: {agg_df.shape}")

# Step 5: Engineer features
print("5. Engineering features...")
with FeatureEngineeringAgentModern("FeatureEng") as agent:
    fe_results = agent.run(agg_df)
    features_df = fe_results["result"]["feature_engineered_data"]
print(f"   Features: {features_df.shape}")

# Step 6: Save results
print("6. Saving results...")
features_df.write_csv("ml_features.csv")
print(f"   Saved to ml_features.csv")

print("\n✅ Pipeline complete!")
print(f"Ready for ML model training")
```

---

## Important Concepts

### 1. Agent Lifecycle

```python
# Explicit cleanup
agent = DataCleaningAgentModern("Cleaner")
try:
    results = agent.run(data)
finally:
    agent.close()  # Always cleanup

# Automatic cleanup (recommended)
with DataCleaningAgentModern("Cleaner") as agent:
    results = agent.run(data)
    # agent.close() called automatically
```

### 2. Data Format Flexibility

```python
from ai_data_science_team.utils import to_polars
import polars as pl
import pandas as pd

# All these work:
df1 = to_polars(pl.DataFrame({"a": [1, 2, 3]}))  # Polars
df2 = to_polars(pd.DataFrame({"a": [1, 2, 3]}))  # Pandas
df3 = to_polars({"a": [1, 2, 3]})                # Dict
df4 = to_polars([{"a": 1}, {"a": 2}])           # List of dicts

# All produce polars DataFrames
print(type(df1))  # <class 'polars.dataframe.frame.DataFrame'>
```

### 3. DuckDB Persistence

```python
# Data automatically persisted
results = agent.run(data)

# Access from another agent
other_agent = AnotherAgent("other")
loaded_df = other_agent.load_from_duckdb("table_name")

# Or query directly
query_result = other_agent.query_duckdb(
    "SELECT * FROM table_name WHERE value > 100"
)
```

### 4. marimo Notebooks

```python
# Each agent generates a notebook
results = agent.run(data)

# Location of notebook
notebook_path = results["notebook_path"]

# Open in browser/editor
import subprocess
subprocess.run(["marimo", "edit", notebook_path])
```

---

## Troubleshooting

### Problem: Import errors
```python
# Solution: Ensure package is installed
pip install -e .
# Or with uv:
uv sync
```

### Problem: DuckDB in-memory limits
```python
# Solution: Use file-based database
agent = DataCleaningAgentModern(
    "Cleaner",
    db_path="/path/to/database.db"  # File-based instead of ":memory:"
)
```

### Problem: marimo notebook won't open
```python
# Solution: Install marimo
uv pip install marimo

# Or check installation
python -c "import marimo; print(marimo.__version__)"
```

### Problem: Large data causes memory issues
```python
# Solution: Process in chunks
for chunk in chunks:
    results = agent.run(chunk)
    # Process results
```

---

## Next Steps

1. **Read the [API Reference](API_REFERENCE.md)**
   - Complete method documentation
   - Parameter descriptions
   - Return value specifications

2. **Study the [Architecture Guide](ARCHITECTURE_GUIDE.md)**
   - Design patterns
   - Data flow
   - Extensibility

3. **Explore [Example Notebooks](examples/)**
   - Real-world workflows
   - Multi-agent pipelines
   - Best practices

4. **Create Custom Agents**
   - Extend BaseAgentModern
   - Implement execute() method
   - Add your domain logic

---

## Tips & Best Practices

### ✅ Do's

```python
# ✅ Use context managers
with DataCleaningAgentModern("Cleaner") as agent:
    results = agent.run(data)

# ✅ Check results structure
if results["status"] == "success":
    processed_data = results["result"]

# ✅ Use type hints
from typing import Union
def process(
    data: Union[pl.DataFrame, pd.DataFrame]
) -> pl.DataFrame:
    ...

# ✅ Log operations
import logging
logger = logging.getLogger(__name__)
logger.info(f"Processing {data.shape}")
```

### ❌ Don'ts

```python
# ❌ Don't forget to close
agent = DataCleaningAgentModern("Cleaner")
results = agent.run(data)
agent.close()  # Don't forget!

# ❌ Don't assume shape
if data.shape[0] > 0:  # Check before operations
    results = agent.run(data)

# ❌ Don't ignore errors
try:
    results = agent.run(data)
except Exception as e:
    logger.error(f"Failed: {e}")  # Always handle
```

---

## Performance Tips

### 1. Batch Processing
```python
# Instead of processing row-by-row
for row in df.iter_rows():
    # Process individual row (slow)

# Do batching
batch_size = 1000
for i in range(0, len(df), batch_size):
    batch = df.slice(i, batch_size)
    results = agent.run(batch)
```

### 2. Use Polars Query Optimization
```python
# Polars optimizes lazy queries
result = (
    df
    .filter(pl.col("amount") > 100)
    .select(["id", "amount"])
    .group_by("id")
    .agg(pl.col("amount").sum())
)
```

### 3. Persistent DuckDB
```python
# In-memory is fast but limited
agent1 = Agent("A", db_path=":memory:")  # In-memory

# File-based survives restarts
agent2 = Agent("B", db_path="my_data.db")  # Persistent
```

---

## Key Resources

- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Architecture Guide**: [ARCHITECTURE_GUIDE.md](ARCHITECTURE_GUIDE.md)
- **Best Practices**: [BEST_PRACTICES.md](BEST_PRACTICES.md)
- **Examples**: [examples/](examples/)
- **Tests**: [tests/](tests/)

---

## Community & Support

- Report issues: [GitHub Issues](https://github.com/your-repo/issues)
- Discussions: [GitHub Discussions](https://github.com/your-repo/discussions)
- Documentation: [Full Docs](https://docs.example.com)

---

## What's Next?

Ready to dive deeper? Check out:

1. **Advanced Patterns** - Multi-agent workflows
2. **Custom Agents** - Create your own agents
3. **Deployment** - Move to production
4. **Performance** - Optimization techniques

Happy data science! 🚀
