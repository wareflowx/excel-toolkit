# Title: Join operations can create Cartesian products and crash systems

## Problem Description

The join command in `excel_toolkit/commands/join.py` has no protection against **Cartesian product explosions**. When joining large datasets with non-unique keys or using inappropriate join types, the result can grow exponentially and crash the system.

### Current Behavior

When joining two DataFrames:
1. Both datasets are **fully loaded into memory**
2. Join operation creates potentially massive result sets
3. No validation or warnings about result size

### The Cartesian Product Danger

A Cartesian product (CROSS JOIN) occurs when:
- Every row in DataFrame A matches every row in DataFrame B
- Result size = rows(A) × rows(B)

### Real-World Scenarios

**Scenario 1: Accidental Cartesian Product**
```python
# Left: 500,000 rows
# Right: 500,000 rows
# Join on non-unique key with duplicates

Result: 500,000 × 500,000 = 250,000,000,000 rows (250 billion!)
Memory required: ~500TB 💀
System: Crashes immediately
```

**Scenario 2: Many-to-Many Join Without Understanding**
```python
# Left: Sales data (100k rows, 50k unique customer_ids)
# Right: Customer info (50k rows, 10k unique customer_ids)
# Join on: customer_id

# If customer_id is not unique in either:
# Result could be 100k × 50k = 5 billion rows
# Memory: 10-100GB
System: Crashes or hangs for hours
```

**Scenario 3: Inner Join with Low Cardinality**
```python
# Left: 500k rows, column "status" has 5 unique values
# Right: 300k rows, column "status" has 5 unique values
# Join on: status

# Approximate result: (500k/5) × (300k/5) × 5 = 30 million rows
# Memory: 2-3GB (manageable but slow)
```

## Affected Files

- `excel_toolkit/commands/join.py`
- `excel_toolkit/operations/joining.py`

## Proposed Solutions

### 1. Pre-Join Validation

Check join key uniqueness before joining:

```python
def validate_join_safety(left_df: pd.DataFrame, right_df: pd.DataFrame, on: str):
    """Validate that join won't create Cartesian product."""

    left_unique = left_df[on].nunique()
    right_unique = right_df[on].nunique()
    left_total = len(left_df)
    right_total = len(right_df)

    # Warn if many-to-many
    if left_unique < left_total and right_unique < right_total:
        estimated_size = (left_total / left_unique) * (right_total / right_unique)
        print(f"WARNING: Many-to-many join detected!")
        print(f"Estimated result size: {estimated_size:,.0f} rows")

        if estimated_size > 10_000_000:
            response = input("This may crash your system. Continue? (y/N): ")
            if response.lower() != 'y':
                raise InterruptedError("Join cancelled by user")
```

### 2. Result Size Limit

```python
MAX_JOIN_RESULT_ROWS = 10_000_000  # 10 million

def join_with_limit(left_df, right_df, on, how='inner'):
    """Perform join with size limit."""

    # Sample to estimate result size
    left_sample = left_df.sample(min(1000, len(left_df)))
    right_sample = right_df.sample(min(1000, len(right_df)))
    sample_result = left_sample.merge(right_sample, on=on, how=how)

    # Extrapolate
    estimated_size = (len(sample_result) *
                     len(left_df) / len(left_sample) *
                     len(right_df) / len(right_sample))

    if estimated_size > MAX_JOIN_RESULT_ROWS:
        raise MemoryError(
            f"Join would create ~{estimated_size:,.0f} rows. "
            f"Maximum allowed: {MAX_JOIN_RESULT_ROWS:,}"
        )

    return left_df.merge(right_df, on=on, how=how)
```

### 3. Chunked Join for Large Results

```python
def join_chunked(left_df, right_df, on, how='inner', chunksize=50000):
    """Perform join in chunks for large datasets."""

    results = []

    # Process left DataFrame in chunks
    for left_chunk in np.array_split(left_df, len(left_df) // chunksize):
        # Join with entire right DataFrame
        joined_chunk = left_chunk.merge(right_df, on=on, how=how)

        # Write chunk to disk immediately
        results.append(joined_chunk)

    return pd.concat(results, ignore_index=True)
```

### 4. Warn About Join Types

```python
JOIN_TYPE_WARNINGS = {
    'cross': "CROSS JOIN creates a Cartesian product (rows(A) × rows(B))",
    'outer': "OUTER JOIN can create very large result sets",
    'left': "Safe if right key is unique",
    'inner': "Safest option for most cases"
}
```

## Additional Safeguards

1. **Key cardinality check**:
   ```python
   left_cardinality = left_df[on].nunique() / len(left_df)
   right_cardinality = right_df[on].nunique() / len(right_df)

   if left_cardinality < 0.1 and right_cardinality < 0.1:
       print("WARNING: Both DataFrames have low cardinality on join key")
   ```

2. **Memory requirement estimation**:
   ```python
   def estimate_join_memory(left_rows, right_rows, columns):
       row_est = left_rows * right_rows / max(left_df[on].nunique(), right_df[on].nunique())
       bytes_per_row = columns * 8  # Rough estimate
       return row_est * bytes_per_row
   ```

3. **Sample-based preview**:
   ```python
   # Show sample of join result before full operation
   sample = left_df.head(1000).merge(right_df.head(1000), on=on, how=how)
   print(f"Sample result: {len(sample)} rows from 1000 × 1000")
   ```

## Related Issues

- File loading memory issues (#001)
- Memory monitoring needed (#006)
- GroupBy performance issues (#005)
