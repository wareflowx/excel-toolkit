# Title: GroupBy operations consume excessive memory with many unique groups

## Problem Description

The GroupBy operation in `excel_toolkit/operations/aggregating.py` can consume excessive memory when dealing with datasets that have many unique groups (e.g., 500k rows with 100k unique groups). The current implementation creates in-memory hash tables that can grow very large.

### Current Behavior

In `operations/aggregating.py` (line 241):
```python
df.groupby(by=group_columns)
```

This creates:
1. A hash table mapping group keys to row indices
2. Intermediate aggregation results for each group
3. MultiIndex column structures for multiple aggregations

### Memory Impact

The memory usage of GroupBy depends heavily on the **number of unique groups**:

| Rows | Unique Groups | Memory Usage | Performance |
|------|--------------|--------------|-------------|
| 50k | 10 | 50-100MB | ✅ Fast (1-2s) |
| 50k | 1,000 | 100-200MB | ✅ Fast (2-5s) |
| 500k | 100 | 500MB-1GB | ✅ Fast (5-10s) |
| 500k | 10,000 | 1-2GB | ⚠️ Medium (10-30s) |
| 500k | 100,000 | 2-5GB | ❌ Slow (30-60s) |
| 500k | 400,000 | 5-10GB | 💀 May crash |

### Real-World Scenarios

**Scenario 1: E-commerce orders grouped by user_id**
```
500k orders × 400k unique users
GroupBy hash table: 400k entries × 64 bytes = 25MB
Intermediate results: 400k groups × multiple aggregations = 500MB-2GB
Total: 1-3GB
Time: 30-60 seconds
```

**Scenario 2: Transaction logs grouped by (date, store, product)**
```
500k transactions × 50k unique (date, store, product) combinations
GroupBy hash table: 50k entries × 128 bytes (compound key) = 6.4MB
Intermediate results: 50k groups × 10 aggregations = 1-2GB
Total: 1.5-3GB
Time: 15-30 seconds
```

**Scenario 3: High-cardinality grouping (worst case)**
```
500k rows grouped by unique_id
GroupBy: 500k groups
Result: 500k rows (one per group)
Memory: 3-5GB for hash tables + intermediates
Time: 60+ seconds or crash
```

## Affected Files

- `excel_toolkit/operations/aggregating.py` (lines 241-258)
- `excel_toolkit/commands/group.py`
- `excel_toolkit/commands/aggregate.py`

## Specific Issues

### 1. No Streaming GroupBy

Current implementation loads everything, groups everything, then writes. There's no incremental processing.

### 2. MultiIndex Column Overhead

When aggregating multiple columns:
```python
# Line 244-258: Creates MultiIndex columns
df.groupby(by=group_columns).agg({
    'Revenue': ['sum', 'mean'],
    'Profit': ['sum', 'mean']
})
```

This creates hierarchical column structures that consume extra memory.

### 3. No Group Cardinality Validation

No warning when grouping by high-cardinality columns that could create millions of groups.

### 4. String GroupBy is Slow

Grouping by string columns (e.g., user_id, email) is slower than numeric grouping due to:
- String hashing
- String comparison overhead
- Memory allocation for string objects

## Proposed Solutions

### 1. Add Group Cardinality Validation

```python
def validate_groupby_cardinality(df: pd.DataFrame, group_columns: list[str]):
    """Validate that groupby won't create too many groups."""

    for col in group_columns:
        unique_count = df[col].nunique()
        total_rows = len(df)

        # Warn if more than 50% unique values
        if unique_count > total_rows * 0.5:
            print(f"WARNING: Column '{col}' has {unique_count} unique values ({unique_count/total_rows*100:.1f}%)")
            print(f"This will create {unique_count} groups and may be slow")

        # Error if more than 90% unique (probably not what user wants)
        if unique_count > total_rows * 0.9:
            raise ValueError(
                f"Column '{col}' has {unique_count} unique values ({unique_count/total_rows*100:.1f}%). "
                f"This is likely too many groups for meaningful aggregation."
            )
```

### 2. Implement Streaming GroupBy for Known Groups

```python
def groupby_streaming(df: pd.DataFrame, group_columns: list[str], output_path: Path):
    """Perform GroupBy in chunks when group set is known in advance."""

    # Get unique groups first (sample if too many)
    unique_groups = df[group_columns].drop_duplicates()

    if len(unique_groups) > 10000:
        print("Too many groups for streaming, using standard GroupBy")
        return df.groupby(group_columns).agg(...)

    # Process each group separately
    results = []
    for group in unique_groups:
        mask = (df[group_columns] == group).all(axis=1)
        group_df = df[mask]

        # Aggregate this group
        result = aggregate_group(group_df)
        results.append(result)

    return pd.concat(results)
```

### 3. Optimize Data Types Before GroupBy

```python
def optimize_for_groupby(df: pd.DataFrame, group_columns: list[str]):
    """Optimize data types to reduce GroupBy memory usage."""

    # Convert strings to categorical if low cardinality
    for col in group_columns:
        if df[col].dtype == 'object':
            unique_count = df[col].nunique()
            if unique_count < len(df) * 0.5:  # Less than 50% unique
                df[col] = df[col].astype('category')

    # Downcast numeric columns
    for col in df.select_dtypes(include=['int64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='integer')

    for col in df.select_dtypes(include=['float64']).columns:
        df[col] = pd.to_numeric(df[col], downcast='float')

    return df
```

### 4. Lazy GroupBy with Dask

```python
import dask.dataframe as dd

def groupby_lazy(df_path: Path, group_columns: list[str]):
    """Use Dask for out-of-core GroupBy."""

    ddf = dd.read_csv(df_path)
    result = ddf.groupby(group_columns).agg(...).compute()
    return result
```

### 5. Add Progress Indicators

```python
from tqdm import tqdm

def groupby_with_progress(df, group_columns, agg_specs):
    """Show progress during GroupBy operation."""

    unique_groups = df[group_columns].drop_duplicates()
    results = []

    for group in tqdm(unique_groups, desc="Grouping"):
        mask = (df[group_columns] == group).all(axis=1)
        group_df = df[mask]
        result = group_df.agg(agg_specs)
        results.append(result)

    return pd.concat(results)
```

## Additional Optimizations

1. **Use `observed=True` for categorical GroupBy**:
   ```python
   df.groupby('category_column', observed=True)  # Only compute observed categories
   ```

2. **Limit number of aggregations**:
   ```python
   MAX_AGGREGATIONS = 10
   if len(agg_specs) > MAX_AGGREGATIONS:
       print(f"WARNING: {len(agg_specs)} aggregations may be slow")
   ```

3. **Sample-based preview**:
   ```python
   # Preview on sample first
   sample = df.sample(min(10000, len(df)))
   sample_result = sample.groupby(group_columns).agg(...)
   print(f"Sample result: {len(sample_result)} groups")
   ```

## Related Issues

- File loading memory issues (#001)
- Memory monitoring needed (#006)
