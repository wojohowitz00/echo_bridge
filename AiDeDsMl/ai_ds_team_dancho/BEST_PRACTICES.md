# Best Practices Guide

Proven patterns and practices for working with the AI Data Science Team framework.

## Table of Contents

1. [Code Organization](#code-organization)
2. [Agent Usage](#agent-usage)
3. [Data Handling](#data-handling)
4. [Error Handling](#error-handling)
5. [Performance](#performance)
6. [Testing](#testing)
7. [Deployment](#deployment)

---

## Code Organization

### Project Structure

```
project/
├─ data/
│  ├─ raw/              # Original data
│  ├─ processed/        # Cleaned data
│  └─ features/         # Engineered features
├─ notebooks/           # marimo notebooks (auto-generated)
├─ scripts/
│  ├─ 01_clean.py       # Data cleaning
│  ├─ 02_analyze.py     # EDA
│  ├─ 03_wrangle.py     # Transformation
│  └─ 04_engineer.py    # Feature engineering
├─ models/              # Trained models
├─ config.py            # Configuration
└─ requirements.txt     # Dependencies
```

### Pipeline Script Pattern

```python
# scripts/01_clean.py
"""Data cleaning pipeline."""

import logging
from pathlib import Path
import polars as pl
from ai_data_science_team.agents import DataCleaningAgentModern

logger = logging.getLogger(__name__)

def main():
    """Run cleaning pipeline."""
    # Load data
    raw_data_path = Path("data/raw/data.csv")
    df = pl.read_csv(raw_data_path)
    logger.info(f"Loaded {df.shape} from {raw_data_path}")

    # Clean
    with DataCleaningAgentModern("Cleaner") as agent:
        results = agent.run(df)

    # Save
    clean_df = results["result"]["cleaned_data"]
    output_path = Path("data/processed/clean.csv")
    clean_df.write_csv(output_path)
    logger.info(f"Saved clean data to {output_path}")

    # Report
    print(f"Cleaning complete:")
    print(f"  Original: {results['original_shape']}")
    print(f"  Cleaned: {results['cleaned_shape']}")
    print(f"  Notebook: {results['notebook_path']}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
```

### Configuration Management

```python
# config.py
"""Project configuration."""

from dataclasses import dataclass

@dataclass
class CleaningConfig:
    """Data cleaning configuration."""
    null_threshold: float = 0.5
    outlier_method: str = "iqr"
    remove_duplicates: bool = True

@dataclass
class VisualizationConfig:
    """Data visualization configuration."""
    max_dimensions: int = 20

@dataclass
class Config:
    """Application configuration."""
    data_path: str = "data/raw"
    output_path: str = "data/processed"
    notebook_path: str = "notebooks"

    cleaning: CleaningConfig = CleaningConfig()
    visualization: VisualizationConfig = VisualizationConfig()

# Usage
config = Config()
agent = DataCleaningAgentModern(
    "Cleaner",
    null_threshold=config.cleaning.null_threshold
)
```

---

## Agent Usage

### ✅ Correct Pattern

```python
from ai_data_science_team.agents import DataCleaningAgentModern
import polars as pl

# 1. Use context managers
with DataCleaningAgentModern("Cleaner") as agent:
    # 2. Check input
    assert df.shape[0] > 0, "Empty DataFrame"

    # 3. Run agent
    results = agent.run(df)

    # 4. Validate output
    assert results["status"] == "success"
    clean_df = results["result"]["cleaned_data"]

    # 5. Use results
    clean_df.write_csv("clean.csv")

    # Automatic cleanup happens here
```

### ❌ Anti-Pattern

```python
# DON'T do this:
agent = DataCleaningAgentModern("Cleaner")
results = agent.run(df)
# Forgot to close!

# DON'T do this either:
results = agent.run(df)
if results["status"] == "success":
    processed_df = results["result"]["cleaned_data"]
    # What if status is "error"?
```

### Agent Composition

```python
def pipeline(raw_data):
    """Complete data science pipeline."""
    with DataCleaningAgentModern("Cleaner") as cleaner:
        clean_results = cleaner.run(raw_data)
        assert clean_results["status"] == "success"
        clean_df = clean_results["result"]["cleaned_data"]

    with DataWranglingAgentModern("Wrangler") as wrangler:
        # Process cleaned data
        agg_df = wrangler.group_and_aggregate(
            clean_df,
            group_by=["customer_id"],
            aggregations={"amount": ["sum", "mean"]}
        )

    with FeatureEngineeringAgentModern("FE") as fe:
        # Engineer features
        fe_results = fe.run(agg_df)
        features_df = fe_results["result"]["feature_engineered_data"]

    return features_df
```

---

## Data Handling

### Input Validation

```python
import polars as pl
from typing import Union

def validate_input(data: Union[pl.DataFrame, dict, list]) -> pl.DataFrame:
    """Validate and convert input data."""
    from ai_data_science_team.utils import to_polars

    df = to_polars(data)

    # Validate
    assert df.shape[0] > 0, "Empty DataFrame"
    assert len(df.columns) > 0, "No columns"

    return df
```

### Memory-Efficient Processing

```python
import polars as pl

# For large files, use lazy evaluation
def process_large_file(filepath: str):
    """Process large CSV without loading entirely."""
    # Lazy load
    df_lazy = pl.scan_csv(filepath)

    # Apply transformations (lazy)
    result = (
        df_lazy
        .filter(pl.col("amount") > 100)
        .select(["id", "amount", "date"])
        .group_by("id")
        .agg(pl.col("amount").sum())
        .collect()  # Execute when ready
    )

    return result
```

### Type Safety

```python
from typing import Dict, List, Optional, Union
import polars as pl

def process_columns(
    df: pl.DataFrame,
    numeric_cols: Optional[List[str]] = None,
    categorical_cols: Union[str, List[str], None] = None
) -> Dict[str, pl.DataFrame]:
    """Process specific columns with type hints."""

    # Normalize inputs
    if categorical_cols is None:
        categorical_cols = []
    elif isinstance(categorical_cols, str):
        categorical_cols = [categorical_cols]

    numeric_cols = numeric_cols or []

    return {
        "numeric": df.select(numeric_cols),
        "categorical": df.select(categorical_cols)
    }
```

---

## Error Handling

### Structured Exception Handling

```python
import logging
from contextlib import contextmanager
from typing import Generator, Any

logger = logging.getLogger(__name__)

@contextmanager
def handle_agent_errors(agent_name: str) -> Generator[None, None, None]:
    """Context manager for agent error handling."""
    try:
        yield
    except ValueError as e:
        logger.error(f"{agent_name}: Invalid input - {e}")
        raise
    except Exception as e:
        logger.error(f"{agent_name}: Unexpected error - {e}")
        raise
    finally:
        logger.debug(f"{agent_name}: Cleanup complete")

# Usage
with handle_agent_errors("DataCleaner"):
    with DataCleaningAgentModern("Cleaner") as agent:
        results = agent.run(df)
```

### Result Validation

```python
def validate_results(results: dict, expected_keys: list) -> bool:
    """Validate agent results."""
    # Check status
    if results.get("status") != "success":
        raise RuntimeError(f"Agent failed: {results.get('error')}")

    # Check required keys
    for key in expected_keys:
        if key not in results:
            raise KeyError(f"Missing required key: {key}")

    # Check data
    if results.get("result") is None:
        raise ValueError("Result data is None")

    return True

# Usage
results = agent.run(df)
validate_results(results, ["status", "result", "notebook_path"])
```

---

## Performance

### Profiling

```python
import time
import logging

logger = logging.getLogger(__name__)

def profile_agent(agent_name: str):
    """Decorator to profile agent execution."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            logger.info(f"{agent_name}: Starting...")

            result = func(*args, **kwargs)

            elapsed = time.time() - start
            logger.info(f"{agent_name}: Completed in {elapsed:.2f}s")

            return result
        return wrapper
    return decorator

# Usage
@profile_agent("DataCleaner")
def run_cleaning(df):
    with DataCleaningAgentModern("Cleaner") as agent:
        return agent.run(df)
```

### Batch Processing

```python
import polars as pl
from typing import Generator

def batch_dataframe(df: pl.DataFrame, batch_size: int) -> Generator[pl.DataFrame, None, None]:
    """Yield DataFrame in batches."""
    for i in range(0, df.height, batch_size):
        yield df.slice(i, batch_size)

# Usage
for batch in batch_dataframe(large_df, batch_size=10000):
    with DataCleaningAgentModern(f"Batch_{batch_size}") as agent:
        results = agent.run(batch)
```

### Lazy Evaluation

```python
import polars as pl

# Instead of:
df = pl.read_csv("large_file.csv")  # Load entire file
filtered = df.filter(pl.col("amount") > 100)

# Do this:
df = pl.scan_csv("large_file.csv")  # Lazy load
filtered = df.filter(pl.col("amount") > 100).collect()  # Execute
```

---

## Testing

### Agent Testing Pattern

```python
import pytest
import polars as pl
from ai_data_science_team.agents import DataCleaningAgentModern

class TestDataCleaning:
    """Tests for DataCleaningAgentModern."""

    @pytest.fixture
    def agent(self):
        """Create agent for testing."""
        return DataCleaningAgentModern("Test")

    @pytest.fixture
    def sample_data(self):
        """Create sample test data."""
        return pl.DataFrame({
            "id": [1, 2, 3, 4],
            "value": [10, None, 30, 1000],
            "category": ["A", "B", "A", "C"]
        })

    def test_null_detection(self, agent, sample_data):
        """Test null detection."""
        null_report = agent._analyze_nulls(sample_data)

        assert null_report["null_counts"]["value"] == 1
        assert "value" in null_report["columns_exceeding_threshold"]

    def test_full_pipeline(self, agent, sample_data):
        """Test complete cleaning pipeline."""
        results = agent.execute(sample_data)

        assert results["status"] == "success"
        assert results["cleaned_data"].height < sample_data.height
```

### Mocking External Dependencies

```python
from unittest.mock import patch, MagicMock
import polars as pl

def test_with_mock_duckdb():
    """Test agent with mocked DuckDB."""
    with patch('duckdb.connect') as mock_db:
        # Setup mock
        mock_db.return_value.register.return_value = None

        # Run test
        with DataCleaningAgentModern("Test") as agent:
            results = agent.run(sample_df)

        # Verify calls
        mock_db.assert_called()
```

---

## Deployment

### Docker Containerization

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN pip install uv && uv sync

# Copy application
COPY ai_data_science_team/ ./ai_data_science_team/

# Run application
CMD ["python", "-m", "ai_data_science_team.pipeline"]
```

### Environment Configuration

```python
# config_env.py
"""Environment-based configuration."""

import os
from pathlib import Path

class Config:
    """Base configuration."""
    DEBUG = False
    DATA_PATH = Path("data")
    NOTEBOOK_PATH = Path("notebooks")
    DB_PATH = ":memory:"

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    DB_PATH = "dev.db"

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    DB_PATH = os.getenv("DB_PATH", "prod.db")

# Load based on environment
ENV = os.getenv("ENVIRONMENT", "development")
if ENV == "production":
    config = ProductionConfig()
else:
    config = DevelopmentConfig()
```

### Logging Configuration

```python
import logging
import sys

def setup_logging(level=logging.INFO):
    """Configure application logging."""
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler('app.log')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Root logger
    root = logging.getLogger()
    root.setLevel(level)
    root.addHandler(console)
    root.addHandler(file_handler)

# Usage
if __name__ == "__main__":
    setup_logging()
    logger = logging.getLogger(__name__)
```

---

## Common Pitfalls & Solutions

### Pitfall 1: Not Closing Agents

```python
# ❌ Bad - Resource leak
agent = DataCleaningAgentModern("Cleaner")
results = agent.run(df)

# ✅ Good - Explicit cleanup
try:
    agent = DataCleaningAgentModern("Cleaner")
    results = agent.run(df)
finally:
    agent.close()

# ✅ Best - Context manager
with DataCleaningAgentModern("Cleaner") as agent:
    results = agent.run(df)
```

### Pitfall 2: Ignoring Error Status

```python
# ❌ Bad - Assumes success
results = agent.run(df)
data = results["result"]["cleaned_data"]  # May be None!

# ✅ Good - Check status
results = agent.run(df)
if results["status"] == "success":
    data = results["result"]["cleaned_data"]
else:
    logger.error(f"Agent failed: {results.get('error')}")
```

### Pitfall 3: Memory Issues with Large Data

```python
# ❌ Bad - Load entire file
df = pl.read_csv("huge_file.csv")
results = agent.run(df)

# ✅ Good - Process in chunks
for chunk in batch_dataframe(huge_df, batch_size=10000):
    results = agent.run(chunk)
    # Process results
```

### Pitfall 4: Mutating Original Data

```python
# ❌ Bad - Modifies original
df["new_col"] = 0
results = agent.run(df)

# ✅ Good - Clone before mutation
df_copy = df.clone()
df_copy["new_col"] = 0
results = agent.run(df_copy)
```

---

## Quick Checklist

Before deploying to production:

- [ ] Error handling implemented
- [ ] Input validation added
- [ ] Logging configured
- [ ] Unit tests written
- [ ] Integration tests passed
- [ ] Performance profiled
- [ ] Resource cleanup verified
- [ ] Documentation updated
- [ ] Security review completed
- [ ] Monitoring configured

---

## Summary

Key principles:

1. **Always use context managers** for agent lifecycle
2. **Validate inputs and outputs** at every step
3. **Use type hints** for clarity
4. **Log everything** for debugging
5. **Test thoroughly** before deployment
6. **Profile performance** with real data
7. **Handle errors gracefully**
8. **Clean up resources** properly

Follow these practices and you'll have robust, maintainable data science code!
