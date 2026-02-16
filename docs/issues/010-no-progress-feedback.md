# Title: Add progress indicators for long-running operations on large files

## Problem Description

When processing large files (50k-500k rows), operations can take 30 seconds to several minutes with **no feedback to the user**. Users don't know if:
- The operation is running or frozen
- How much progress has been made
- How much time remains
- If the operation will succeed or fail

### Current Behavior

```bash
$ xl filter large_file.xlsx --where "Amount > 1000" --output filtered.xlsx

[Nothing happens for 45 seconds]

# User wonders: Is it working? Did it crash? Should I wait?
```

### Real-World Impact

**Scenario 1: User doesn't know if it's working**
```
User: xl group sales_500k.xlsx --by region --aggregate "amount:sum" --output result.xlsx
[Waits 2 minutes with no feedback]
User: "Is it frozen? Let me try Ctrl+C..."
[Ctrl+C]
[Actually it was working, would have finished in 30 more seconds]
User frustration: High
```

**Scenario 2: No indication of remaining time**
```
User: xl join huge1.xlsx huge2.xlsx --on id --how inner --output result.xlsx
[Nothing... waits... waits...]
User thoughts:
- "Will this take 1 minute or 1 hour?"
- "Should I cancel and try a different approach?"
- "Is my system frozen?"

After 5 minutes: Still no feedback
```

**Scenario 3: Pipeline operations**
```bash
xl filter data.xlsx --where "Amount > 1000" | \
  xl sort --by Date | \
  xl group --by Region --aggregate "Amount:sum" \
  --output final.xlsx

[No feedback for each step]
[User has no idea which step is running]
[If one step fails, unclear where]
```

## Affected Operations

All operations that process large files:
- **File loading**: 10-30s for 500k rows
- **Filtering**: 2-5s per filter
- **GroupBy/Aggregate**: 5-60s depending on groups
- **Join**: 30s+ (can be minutes)
- **Merge**: 30-120s depending on file count
- **Sort**: 5-10s
- **Transform**: 5-15s
- **Pivot**: 10-30s

## Affected Files

- All commands in `excel_toolkit/commands/`
- All operations in `excel_toolkit/operations/`

## Proposed Solution

### 1. Add Progress Bars with tqdm

```python
from tqdm import tqdm

def read_excel_with_progress(path: Path, **kwargs) -> pd.DataFrame:
    """Read Excel file with progress indicator."""

    file_size_mb = path.stat().st_size / (1024 * 1024)

    print(f"Loading file ({file_size_mb:.1f} MB)...")

    # For chunked reading
    if file_size_mb > 50:  # Large file: show progress
        chunks = []
        with tqdm(total=100, desc="Loading", unit="%") as pbar:
            for chunk in pd.read_excel(path, chunksize=50000, **kwargs):
                chunks.append(chunk)
                pbar.update(100 / (file_size_mb / 50))  # Rough estimate

        return pd.concat(chunks, ignore_index=True)
    else:
        # Small file: no progress bar needed
        return pd.read_excel(path, **kwargs)
```

**Output:**
```
Loading file (250.0 MB)...
Loading: 100%|████████████████████| 100/100 [00:15<00:00, 6.52it/s]
```

### 2. Progress for Long Operations

```python
def groupby_with_progress(df: pd.DataFrame, group_columns: list[str]) -> pd.DataFrame:
    """Perform GroupBy with progress indicator."""

    unique_groups = df[group_columns].drop_duplicates()
    total_groups = len(unique_groups)

    if total_groups > 1000:  # Only show progress for large groupings
        results = []

        with tqdm(total=total_groups, desc="Grouping", unit="group") as pbar:
            for group in unique_groups:
                mask = (df[group_columns] == group).all(axis=1)
                group_df = df[mask]
                result = group_df.agg(...)

                results.append(result)
                pbar.update(1)

        return pd.concat(results)
    else:
        # Small grouping: no progress needed
        return df.groupby(group_columns).agg(...)
```

**Output:**
```
Grouping: 45000groups [00:45<00:00, 1000.45groups/s]
```

### 3. Time Estimation

```python
import time

def operation_with_eta(file_path: Path, operation: str):
    """Perform operation with ETA calculation."""

    start_time = time.time()
    file_size = file_path.stat().st_size

    print(f"Starting {operation} on {file_size / (1024**2):.1f} MB file...")

    # Sample first 10% to estimate speed
    sample_start = time.time()
    # ... process first 10% ...
    sample_time = time.time() - sample_start

    # Estimate total time
    estimated_total = sample_time * 10
    print(f"Estimated time: {estimated_total:.0f} seconds")

    # Process remaining with progress
    # ... rest of operation ...
```

**Output:**
```
Starting filter on 250.0 MB file...
Estimated time: 45 seconds
Filtering: 45%|█████████       | 23/50s [00:20<00:25, 1.12it/s]
```

### 4. Step-by-Step Feedback for Pipelines

```python
def pipeline_with_feedback(steps: list[Callable]):
    """Execute pipeline with feedback for each step."""

    for i, step in enumerate(steps, 1):
        step_name = step.__name__
        print(f"\n[{i}/{len(steps)}] Running: {step_name}...")

        start = time.time()
        result = step()
        elapsed = time.time() - start

        print(f"[{i}/{len(steps)}] Completed: {step_name} ({elapsed:.1f}s)")

    return result
```

**Output:**
```
[1/3] Running: filter...
[1/3] Completed: filter (12.3s)

[2/3] Running: sort...
[2/3] Completed: sort (8.7s)

[3/3] Running: group...
[3/3] Completed: group (31.2s)
```

### 5. Verbose Mode

Add a `--verbose` flag for detailed feedback:

```python
@app.command()
def filter(
    file_path: Path,
    where: str,
    output: Path,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed progress")
):
    """Filter rows based on condition."""

    if verbose:
        print(f"Input file: {file_path}")
        print(f"Output file: {output}")
        print(f"Condition: {where}")
        print()

    # Show progress
    if verbose:
        print(f"Loading file ({file_path.stat().st_size / (1024**2):.1f} MB)...")
        start = time.time()

    df = read_file(file_path)

    if verbose:
        elapsed = time.time() - start
        print(f"Loaded {len(df)} rows in {elapsed:.1f}s")
        print(f"Filtering with condition: {where}...")
        start = time.time()

    result = apply_filter(df, where)

    if verbose:
        elapsed = time.time() - start
        print(f"Filtered to {len(result)} rows in {elapsed:.1f}s")
        print(f"Writing to {output}...")
```

**Output with --verbose:**
```
$ xl filter data.xlsx --where "Amount > 1000" --output filtered.xlsx -v

Input file: data.xlsx
Output file: filtered.xlsx
Condition: Amount > 1000

Loading file (250.0 MB)...
Loaded 500000 rows in 12.3s
Filtering with condition: Amount > 1000...
Filtered to 125000 rows in 4.5s
Writing to filtered.xlsx...
Done! Total time: 17.2s
```

### 6. Progress for Known-Length Operations

```python
def merge_with_progress(file_paths: list[Path], output_path: Path):
    """Merge files with progress indicator."""

    total_files = len(file_paths)

    with tqdm(total=total_files, desc="Merging", unit="file") as pbar:
        results = []

        for i, file_path in enumerate(file_paths, 1):
            pbar.set_description(f"Merging file {i}/{total_files}")

            df = pd.read_excel(file_path)
            results.append(df)

            pbar.update(1)

        final_df = pd.concat(results, ignore_index=True)
        final_df.to_excel(output_path, index=False)
```

**Output:**
```
Merging file 3/5: 60%|████████████       | 3/5 [00:30<00:20, 10.5s/file]
```

### 7. Memory Usage Display

```python
import psutil

def show_memory_usage():
    """Display current memory usage."""

    process = psutil.Process()
    memory_mb = process.memory_info().rss / (1024**2)
    percent = psutil.virtual_memory().percent

    print(f"Memory: {memory_mb:.0f} MB ({percent:.0f}%)")
```

**Output:**
```
Memory: 1250 MB (31%)
```

### 8. Cancellation Support

```python
import signal

class CancellableOperation:
    """Operation that can be cancelled by user."""

    def __init__(self):
        self._cancelled = False

        # Handle Ctrl+C gracefully
        signal.signal(signal.SIGINT, self._handle_cancel)

    def _handle_cancel(self, signum, frame):
        print("\n\nCancelling operation...")
        self._cancelled = True

    def run(self, func):
        """Run operation with cancellation support."""

        with tqdm() as pbar:
            result = func(pbar, self._cancelled)
            return result
```

**Output on Ctrl+C:**
```
Filtering: 45%|█████████       | 23/50s [00:20<00:25, 1.12it/s]
^C
Cancelling operation...
Operation cancelled by user. Partial results saved to: filtered_partial.xlsx
```

## Implementation Priority

### High Priority (Immediate Value)
1. Basic progress bars for file loading
2. Progress for long operations (GroupBy, Join, Merge)
3. Verbose mode with timing

### Medium Priority (Nice to Have)
4. ETA estimation
5. Memory usage display
6. Step-by-step pipeline feedback

### Low Priority (Advanced)
7. Cancellation support
8. Real-time progress updates for all operations

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "tqdm>=4.65.0",  # Progress bars
    "psutil>=5.9.0",  # For memory monitoring
    ...
]
```

## Examples of User-Facing Output

### Simple Progress (Default)
```
$ xl filter large.xlsx --where "Amount > 1000" -o filtered.xlsx

Loading: 100%|████████████████████| 500k/500k [00:15<00:00]
Filtering: 500k rows [00:05<00:00, 100k rows/s]
Writing: 125k rows [00:03<00:00, 41.6k rows/s]
Done! Total time: 23.5s
```

### Verbose Mode
```
$ xl filter large.xlsx --where "Amount > 1000" -o filtered.xlsx -v

Starting operation...
  Input: large.xlsx (250.0 MB)
  Output: filtered.xlsx
  Condition: Amount > 1000

[1/3] Loading file...
  Rows: 500,000
  Time: 15.2s
  Memory: 1,250 MB (31%)

[2/3] Filtering data...
  Input rows: 500,000
  Output rows: 125,000 (25% retained)
  Time: 5.1s
  Memory: 1,500 MB (38%)

[3/3] Writing to file...
  Rows: 125,000
  Time: 3.2s

✓ Operation completed successfully in 23.5s
```

### Pipeline with Feedback
```
$ xl filter data.xlsx --where "Amount > 1000" | \
    xl sort --by Date | \
    xl group --by Region --aggregate "Amount:sum" \
    --output final.xlsx -v

[Step 1/3] Filtering data.xlsx...
  Rows: 500,000 → 125,000
  Time: 5.2s

[Step 2/3] Sorting by Date...
  Rows: 125,000
  Time: 8.7s

[Step 3/3] Grouping by Region...
  Groups: 50
  Time: 12.3s

✓ Pipeline completed in 26.2s
  Final output: final.xlsx (50 rows)
```

## Related Issues

- Memory monitoring needed (#006) - Progress bars work well with memory monitoring
- All performance issues benefit from better user feedback
