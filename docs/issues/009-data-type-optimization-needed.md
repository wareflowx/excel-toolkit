# Title: Optimize pandas data types during file loading to reduce memory usage

## Problem Description

The excel-toolkit does not optimize pandas data types when loading files. Pandas defaults to `int64`, `float64`, and `object` (string) types, which consume significantly more memory than necessary. For large files (50k-500k rows), this can double or triple memory usage.

### Current Behavior

In `file_handlers.py`:
```python
# Line 110: Loads with default dtypes
df = pd.read_excel(path, sheet_name=sheet_name, header=header, engine=engine, **kwargs)

# Line 313: Loads with default dtypes
df = pd.read_csv(path, encoding=encoding, delimiter=delimiter, header=header, **kwargs)
```

No dtype optimization is performed during loading.

### Memory Impact by Data Type

| Data Type | Memory per Element | For 500k Rows |
|-----------|-------------------|---------------|
| `int64` (default) | 8 bytes | 4MB per column |
| `int32` | 4 bytes | 2MB per column (50% savings) |
| `int16` | 2 bytes | 1MB per column (75% savings) |
| `int8` | 1 byte | 0.5MB per column (87.5% savings) |
| `float64` (default) | 8 bytes | 4MB per column |
| `float32` | 4 bytes | 2MB per column (50% savings) |
| `object` (string) | Variable | 8-16 bytes average |
| `category` | Variable | 1-4 bytes (50-90% savings) |

### Real-World Examples

**Scenario 1: E-commerce data with 20 columns**
```
500k rows × 20 columns with default dtypes:
- 5 integer columns (int64): 5 × 4MB = 20MB
- 5 float columns (float64): 5 × 4MB = 20MB
- 10 string columns (object): 10 × 8MB = 80MB
Total: 120MB

With optimized dtypes:
- 5 integer columns (int16/int32): 5 × 2MB = 10MB
- 5 float columns (float32): 5 × 2MB = 10MB
- 10 string columns (category for low-cardinality): 10 × 2MB = 20MB
Total: 40MB (67% savings)
```

**Scenario 2: User activity log**
```
500k rows with columns:
- user_id: int64 (range: 1 to 500,000) → Could be int32 (2MB vs 4MB)
- action_id: int64 (range: 1 to 50) → Could be int8 (0.5MB vs 4MB)
- timestamp: object → Could be datetime64 (4MB vs 8MB)
- status: int64 (0/1) → Could be bool (0.5MB vs 4MB)
- page_url: object (100k unique URLs) → Could be category (4MB vs 8MB)

Default dtypes: 28MB
Optimized dtypes: 11MB (61% savings)
```

**Scenario 3: Sales data**
```
500k rows:
- quantity: int64 (range: 1 to 1000) → int16 (1MB vs 4MB)
- price: float64 → float32 (2MB vs 4MB)
- discount: float64 (0-1) → float32 (2MB vs 4MB)
- customer_id: int64 (50k unique) → int32 (2MB vs 4MB)
- region: object (10 unique) → category (0.5MB vs 4MB)
- product_category: object (50 unique) → category (1MB vs 4MB)

Default dtypes: 24MB
Optimized dtypes: 8.5MB (65% savings)
```

## Affected Files

- `excel_toolkit/core/file_handlers.py` (lines 110, 313)
- Potentially: New utility module for dtype optimization

## Proposed Solution

### 1. Auto-Detect Optimal Types

```python
def optimize_dtypes(df: pd.DataFrame) -> dict[str, str]:
    """Automatically detect optimal dtypes for DataFrame columns."""

    dtype_mapping = {}

    for col in df.columns:
        col_dtype = df[col].dtype

        # Skip if already optimized
        if col_dtype in ['category', 'bool', 'datetime64[ns]']:
            continue

        # Integer columns
        if pd.api.types.is_integer_dtype(col_dtype):
            cmin = df[col].min()
            cmax = df[col].max()

            if cmin >= 0:  # Unsigned integers
                if cmax < 255:
                    dtype_mapping[col] = 'uint8'
                elif cmax < 65535:
                    dtype_mapping[col] = 'uint16'
                elif cmax < 4294967295:
                    dtype_mapping[col] = 'uint32'
            else:  # Signed integers
                if cmin > -128 and cmax < 127:
                    dtype_mapping[col] = 'int8'
                elif cmin > -32768 and cmax < 32767:
                    dtype_mapping[col] = 'int16'
                elif cmin > -2147483648 and cmax < 2147483647:
                    dtype_mapping[col] = 'int32'

        # Float columns
        elif pd.api.types.is_float_dtype(col_dtype):
            dtype_mapping[col] = 'float32'

        # Object (string) columns
        elif col_dtype == 'object':
            unique_count = df[col].nunique()
            total_count = len(df)

            # Use category if < 50% unique values
            if unique_count / total_count < 0.5:
                dtype_mapping[col] = 'category'

    return dtype_mapping
```

### 2. Apply During File Loading

```python
def read_excel_optimized(path: Path, **kwargs) -> Result[pd.DataFrame, FileHandlerError]:
    """Read Excel file with dtype optimization."""

    # First pass: read sample to detect dtypes
    sample_df = pd.read_excel(path, nrows=10000)

    # Detect optimal dtypes from sample
    dtype_mapping = optimize_dtypes(sample_df)

    print(f"Optimizing {len(dtype_mapping)} columns:")
    for col, dtype in dtype_mapping.items():
        print(f"  {col}: {dtype}")

    # Second pass: read full file with optimized dtypes
    try:
        df = pd.read_excel(path, dtype=dtype_mapping, **kwargs)
        return ok(df)
    except Exception as e:
        return err(FileHandlerError(str(e)))
```

### 3. Add CLI Option for Dtype Optimization

```python
@app.command()
def info(
    file_path: Path,
    optimize_types: bool = typer.Option(False, "--optimize-types", help="Optimize data types")
):
    """Show file information with optional dtype optimization."""

    if optimize_types:
        print("Loading file with dtype optimization...")
        df = read_excel_optimized(file_path)
    else:
        df = read_excel(file_path)
```

### 4. Memory Savings Report

```python
def report_memory_savings(df_original: pd.DataFrame, df_optimized: pd.DataFrame):
    """Report memory savings from dtype optimization."""

    original_memory = df_original.memory_usage(deep=True).sum() / (1024**2)
    optimized_memory = df_optimized.memory_usage(deep=True).sum() / (1024**2)
    savings = original_memory - optimized_memory
    savings_percent = (savings / original_memory) * 100

    print(f"\nMemory Usage:")
    print(f"  Original:  {original_memory:.1f} MB")
    print(f"  Optimized: {optimized_memory:.1f} MB")
    print(f"  Savings:   {savings:.1f} MB ({savings_percent:.1f}%)")
```

### 5. Fallback for Failed Optimization

```python
def safe_optimize_dtypes(df: pd.DataFrame) -> pd.DataFrame:
    """Safely optimize dtypes with fallback."""

    try:
        dtype_mapping = optimize_dtypes(df)
        return df.astype(dtype_mapping)
    except Exception as e:
        print(f"Warning: Dtype optimization failed: {e}")
        print("Falling back to default dtypes")
        return df
```

### 6. Categorical Type for Strings

String columns with low cardinality benefit greatly from the `category` dtype:

```python
def should_be_categorical(series: pd.Series, threshold: float = 0.5) -> bool:
    """Determine if a series should use category dtype."""

    if series.dtype != 'object':
        return False

    unique_ratio = series.nunique() / len(series)
    return unique_ratio < threshold

# Examples:
# - "status" column with 5 unique values: category (95% memory reduction)
# - "country" column with 50 unique values out of 500k: category (90% reduction)
# - "user_id" with 400k unique values: object (category would be worse)
```

### 7. Type Inference from Column Names

```python
def infer_dtype_from_column_name(col_name: str, series: pd.Series) -> str | None:
    """Infer optimal dtype based on column name patterns."""

    col_lower = col_name.lower()

    # Boolean patterns
    if col_lower in ['is_active', 'is_deleted', 'is_verified', 'enabled', 'disabled']:
        if series.isin([0, 1, True, False]).all():
            return 'bool'

    # ID columns (likely can be smaller than int64)
    if '_id' in col_lower or col_lower.endswith('_id'):
        if series.max() < 4294967295:  # Max uint32
            return 'uint32'

    # Date/time columns
    if 'date' in col_lower or 'time' in col_lower:
        if series.dtype == 'object':
            return 'datetime64[ns]'

    # Percentage/ratio columns
    if col_lower in ['percent', 'ratio', 'rate', 'discount', 'commission']:
        if series.max() <= 1.0 and series.min() >= 0.0:
            return 'float32'

    return None  # No inference possible
```

## Implementation Strategy

### Phase 1: Basic Optimization (High Priority)
1. Implement `optimize_dtypes()` function
2. Add to file loading with sampling
3. Show memory savings report

### Phase 2: Advanced Features (Medium Priority)
1. Add CLI option `--optimize-types`
2. Implement column name inference
3. Add smart categorical detection

### Phase 3: User Control (Low Priority)
1. Allow user to specify dtype mapping
2. Save dtype mapping for reuse
3. Add `--dtype` option to override auto-detection

## Expected Impact

For a typical 500k row dataset:

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| File size on disk | 50MB | 50MB | No change |
| Memory usage | 150MB | 75MB | **50% reduction** |
| Load time | 10s | 11s | +10% (detection overhead) |
| Operation speed | Baseline | Baseline | No change |

The 10% slower load time is acceptable for 50% memory savings.

## Special Cases to Handle

1. **Mixed types in columns**: Fall back to object dtype
2. **NaN values**: Some dtypes don't support NaN (e.g., int64)
3. **String to category**: Only if < 50% unique values
4. **Boolean detection**: Check only 0/1/True/False values
5. **Datetime parsing**: Handle various formats

## Related Issues

- File loading memory issues (#001)
- File size limits too permissive (#002)
- All other memory-related issues benefit from dtype optimization
