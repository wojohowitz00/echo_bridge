# Architecture Guide - Modern Data Science Agent Framework

## Overview

The AI Data Science Team framework is built on a **modern Python data stack** with a polars-first architecture. It provides specialized agents for data cleaning, visualization, wrangling, and feature engineering.

## Technology Stack

### Core Technologies

| Tool | Purpose | Why |
|------|---------|-----|
| **uv** | Package management | 10-100x faster than pip |
| **ruff** | Linting & formatting | 100x faster than black/isort/flake8 |
| **polars** | Data processing | 5-20x faster than pandas, lazy evaluation |
| **duckdb** | Data persistence | In-process OLAP database, SQL interface |
| **marimo** | Notebooks | Reactive notebooks in .py files |
| **altair** | Visualization | Declarative Vega-Lite visualizations |
| **dlt** | ETL framework | Declarative data loading |

### Design Philosophy

```
Principles:
├─ Polars-first: Use polars natively (not pandas compatibility)
├─ Type-safe: Full type hints (mypy compatible)
├─ Observable: Automatic marimo notebooks
├─ Persistent: DuckDB for all data
├─ Composable: Agents extend BaseAgentModern
├─ Fast: Modern compiled tools (ruff, uv, polars)
└─ Testable: Comprehensive test coverage
```

---

## Architecture Layers

### Layer 1: Foundation (Phase C)

**DuckDBManager** - Data persistence layer
- CRUD operations on DuckDB tables
- SQL query execution
- Schema inspection
- Multi-table support

```
Application
    ↓
DuckDBManager
    ↓
DuckDB (in-memory or file-based)
```

**MarimoNotebook** - Interactive notebook generator
- Programmatic notebook creation
- Fluent API for building cells
- Export to .py files

```
Agent Results
    ↓
MarimoNotebook
    ↓
marimo .py file
```

**BaseAgentModern** - Abstract agent base
- Orchestrates DuckDB + marimo
- Provides lifecycle management
- Defines agent interface

```
Concrete Agent
    ↓
BaseAgentModern (execute + run)
    ├─ DuckDB integration
    ├─ Notebook generation
    └─ Resource cleanup
```

### Layer 2: Agents (Phase D & E)

**5 Specialized Agents** - Domain-specific functionality

```
DataCleaningAgentModern (370 lines)
├─ Null detection & removal
├─ Outlier detection (IQR, z-score)
├─ Duplicate removal
└─ Smart null filling

DataVisualizationAgentModern (240 lines)
├─ Column analysis
├─ Statistical summaries
├─ Chart recommendations
└─ Correlation analysis

DataWranglingAgentModern (364 lines)
├─ Pivot/unpivot
├─ Group & aggregate
├─ Joins (all types)
├─ Filtering & sorting
└─ Column operations

FeatureEngineeringAgentModern (411 lines)
├─ Scaling (standardize, normalize)
├─ Polynomial features
├─ Interactions
├─ Encoding (one-hot, label)
├─ Binning
└─ Feature selection

All extend BaseAgentModern
```

### Layer 3: Utilities

**Data Conversion Layer**
```python
to_polars(data) → pl.DataFrame
├─ Input: pandas, dict, list, polars
├─ Process: Standardize to polars
└─ Output: Polars DataFrame
```

**Type System**
```python
All functions use Union types for flexibility:
- Union[str, List[str]] for column selections
- Union[pl.DataFrame, dict, list] for data input
- Optional for nullable parameters
```

---

## Data Flow Architecture

### Standard Agent Workflow

```
┌─────────────────────────────────────────┐
│            User Input Data              │
│  (polars, pandas, dict, list)           │
└──────────────┬──────────────────────────┘
               │
               ↓
        ┌──────────────┐
        │  to_polars() │  ← Conversion layer
        └──────┬───────┘
               │
               ↓
        ┌──────────────────┐
        │  Agent.execute() │  ← Domain logic
        │  - Process data  │
        │  - Persist to DB │
        └──────┬───────────┘
               │
               ↓
        ┌──────────────────┐
        │ Agent.run()      │  ← Orchestration
        │ - Call execute() │
        │ - Gen notebook   │
        │ - Return results │
        └──────┬───────────┘
               │
               ↓
        ┌─────────────────────────────────┐
        │        Results Dictionary       │
        │  - status: "success"            │
        │  - result: transformed data     │
        │  - notebook_path: /path/to/nb   │
        │  - duckdb_tables: [table names] │
        └─────────────────────────────────┘
```

### DuckDB Persistence Pattern

```
Agent.execute()
├─ Store input: persist_to_duckdb("original_data", input_df)
├─ Process
├─ Store intermediate: persist_to_duckdb("processed_data", proc_df)
├─ Store output: persist_to_duckdb("final_data", output_df)
└─ Generate queries for notebook

Notebook Access:
├─ duckdb.query('SELECT * FROM original_data').pl()
├─ duckdb.query('SELECT * FROM processed_data').pl()
└─ duckdb.query('SELECT * FROM final_data').pl()
```

### marimo Notebook Pattern

```
Agent.generate_notebook()
├─ Add setup cell (imports, DB connection)
├─ Add data overview section
│  ├─ Load data from DuckDB
│  ├─ Show shape and columns
│  └─ Display statistics
├─ Add analysis section (agent-specific)
├─ Add recommendations
└─ Add conclusions
```

---

## Agent Design Pattern

### 1. Inheritance Model

```python
BaseAgentModern (abstract)
│
├─ execute(data) → Dict[str, Any]  # Must implement
├─ run(data) → Dict[str, Any]      # Inherited
├─ generate_notebook() → str       # Optional override
└─ lifecycle methods (setup, cleanup)

Concrete Agents (DataCleaningAgentModern, etc.)
│
└─ Override execute() with domain logic
└─ Optionally override generate_notebook()
```

### 2. Method Naming Convention

```
Public API Methods:
├─ execute() - Core agent logic (implementing class)
├─ run() - Orchestration (inherited from base)
├─ method() - User-facing transformations

Private Helper Methods:
├─ _helper() - Internal implementation
├─ _analyze() - Analysis operations
└─ _process() - Processing operations

Utility Methods (inherited):
├─ persist_to_duckdb() - Save data
├─ load_from_duckdb() - Load data
└─ setup_notebook() - Initialize notebook
```

### 3. Configuration Pattern

```python
class AgentModern(BaseAgentModern):
    def __init__(self, name, **config):
        super().__init__(name)
        self.null_threshold = config.get('null_threshold', 0.5)
        self.outlier_method = config.get('outlier_method', 'iqr')
        self.config = {
            'null_threshold': self.null_threshold,
            'outlier_method': self.outlier_method
        }

# Usage
agent = DataCleaningAgentModern(
    name="Cleaner",
    null_threshold=0.7,
    outlier_method="zscore"
)
```

---

## Integration Points

### 1. Agent Chaining

```python
# Sequential processing
with DataCleaningAgentModern("Step1") as cleaner:
    clean_results = cleaner.run(raw_data)
    clean_df = clean_results["result"]["cleaned_data"]

with DataVisualizationAgentModern("Step2") as viz:
    viz_results = viz.run(clean_df)

with DataWranglingAgentModern("Step3") as wrangler:
    wrang_df = wrangler.pivot(clean_df, ...)
    wrang_results = wrangler.run(wrang_df)
```

### 2. DuckDB Shared State

```python
# Agents can access each other's results
cleaner = DataCleaningAgentModern("Cleaner")
cleaner_results = cleaner.run(df1)

# Other agent accesses cleaner's output
wrangler = DataWranglingAgentModern("Wrangler")
clean_data = wrangler.load_from_duckdb("cleaned_data")
wrang_results = wrangler.run(clean_data)
```

### 3. Notebook Integration

```python
# Each agent generates a notebook
results = agent.run(data)

# Notebook location
notebook_path = results["notebook_path"]

# Open in marimo
# marimo edit /path/to/notebook.py
```

---

## Type System

### Type Hints Everywhere

```python
from typing import Any, Dict, List, Optional, Union

def process(
    data: Union[pl.DataFrame, pd.DataFrame, dict, list],
    columns: Union[str, List[str]],
    threshold: Optional[float] = None
) -> Dict[str, Any]:
    ...
```

### Input Normalization

```python
# All inputs normalized to polars
from ai_data_science_team.utils import to_polars

# Any of these work:
df = to_polars(pandas_df)
df = to_polars({"col": [1, 2, 3]})
df = to_polars([{"a": 1}, {"a": 2}])
df = to_polars(polars_df)

# All produce: pl.DataFrame
```

---

## Error Handling Strategy

### Three Levels

1. **Input Validation**
   ```python
   df = to_polars(data)  # Fails fast if invalid
   ```

2. **Processing Errors**
   ```python
   try:
       result = self._process(df)
   except Exception as e:
       logger.error(f"Processing failed: {e}")
       return {"status": "error", "message": str(e)}
   ```

3. **Cleanup Guarantee**
   ```python
   try:
       results = agent.run(data)
   finally:
       agent.close()  # Always executes
   ```

### Context Manager Pattern (Recommended)

```python
with AgentModern("name") as agent:
    results = agent.run(data)
    # agent.close() called automatically
```

---

## Performance Characteristics

### Benchmarks (Approximate)

| Operation | Polars | Pandas | Speedup |
|-----------|--------|--------|---------|
| Read CSV (100k rows) | 50ms | 200ms | 4x |
| Group & Agg | 30ms | 150ms | 5x |
| Pivot (10 groups) | 20ms | 100ms | 5x |
| Filter & Select | 10ms | 50ms | 5x |

### Memory Usage

Polars typically uses 30-40% less memory than pandas due to:
- Lazy evaluation (no immediate execution)
- Arrow columnar format
- Smart allocations

---

## Testing Strategy

### Test Pyramid

```
              Edge Cases
             /    |    \
       Empty  Nulls  Constants
           \    |    /
        Integration Tests
       /         |         \
   DuckDB   Notebooks   Workflows
         \       |       /
       Unit Tests
   /       |       |       \
Scaling  Encoding  Pivot  Aggregate
```

### Test Coverage

- **Unit**: Individual method functionality
- **Integration**: Multi-method workflows
- **Edge Cases**: Empty data, nulls, single rows
- **End-to-End**: Full pipeline execution

```
Target: 70%+ line coverage
Achieved: 100% test pass rate
Test Ratio: 1.1x (tests to code)
```

---

## Deployment Considerations

### Single-Machine Deployment

```
├─ DuckDB in-memory: `:memory:`
├─ Notebooks in temp directory
└─ Data stays local
```

### Scalable Deployment

```
├─ DuckDB to persistent DB file
├─ Notebooks to shared storage (S3, GCS)
├─ Agent as API service
└─ Results in object storage
```

### Kubernetes Deployment

```
Pod
├─ Agent container
├─ DuckDB volume
├─ marimo server
└─ Logging/monitoring
```

---

## Extensibility

### Creating Custom Agents

```python
from ai_data_science_team.agents import BaseAgentModern
from ai_data_science_team.utils import to_polars

class MyCustomAgent(BaseAgentModern):
    def __init__(self, name, **config):
        super().__init__(name, "My custom agent")
        # Store config
        self.custom_param = config.get('param', 'default')

    def execute(self, data):
        # 1. Convert to polars
        df = to_polars(data)

        # 2. Domain logic
        result = self._custom_logic(df)

        # 3. Persist
        self.persist_to_duckdb("my_table", result)

        # 4. Return results
        return {
            "result": result,
            "shape": result.shape,
            "custom_metric": self._calculate_metric(result)
        }

    def _custom_logic(self, df):
        # Your implementation
        return df

    def generate_notebook(self):
        if not self.notebook:
            self.setup_notebook(
                title=f"{self.name} - Custom Analysis",
                description="Your custom description"
            )

        self.notebook.add_markdown("## Results")
        self.notebook.add_code("# Your code here")

        return str(super().generate_notebook())

# Usage
agent = MyCustomAgent("CustomAgent", param="value")
results = agent.run(data)
```

---

## Future Roadmap

### Planned Enhancements

- [ ] **Parallel Agent Execution** - Run multiple agents concurrently
- [ ] **Agent Composition** - Automatically chain agents
- [ ] **ML Model Integration** - sklearn, xgboost agents
- [ ] **Time Series Support** - Temporal analysis agents
- [ ] **Statistical Testing** - Hypothesis testing agents
- [ ] **Cloud Storage** - S3, GCS, Azure Blob integrations
- [ ] **Distributed Processing** - Spark/Ray support
- [ ] **Real-time Monitoring** - Data quality dashboards

---

## Summary

The framework provides:

1. **Unified Architecture** - All agents follow BaseAgentModern pattern
2. **Type Safety** - Full type hints, mypy compatible
3. **Data Persistence** - DuckDB integration built-in
4. **Observable Results** - Auto-generated marimo notebooks
5. **Composability** - Agents chain together seamlessly
6. **Extensibility** - Easy to create custom agents
7. **Performance** - Modern polars-based data processing
8. **Quality** - Comprehensive test coverage, ruff linting

All built on the modern Python data stack with uv, ruff, polars, duckdb, and marimo.
