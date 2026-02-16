# Title: Add memory monitoring to prevent crashes during operations

## Problem Description

The excel-toolkit currently has **no memory monitoring** during operations. When processing large files (50k-500k rows), operations can silently consume all available system memory, leading to:
- Application crashes (MemoryError or SIGKILL)
- System-wide freezing and swapping
- Data loss (crash before writing output)
- Poor user experience (no warnings or feedback)

### Current Behavior

All operations assume:
- There's enough memory available
- Memory won't run out mid-operation
- Nothing needs to be checked

### Real-World Impact

**Scenario 1: Silent crash mid-operation**
```
1. User loads 400MB Excel file (~1.2GB in memory)
2. Performs GroupBy → Memory grows to 2GB
3. Performs Filter → Creates copy → 3GB
4. System has 2GB available
5. Result: SIGKILL, no error message, data lost
```

**Scenario 2: System becomes unresponsive**
```
1. User starts merging 5 large files
2. Memory usage grows to 7GB on 8GB system
3. System starts swapping to disk
4. Everything becomes extremely slow
5. User can't even kill the process
6. 30 minutes later, crash or success (unpredictable)
```

**Scenario 3: No feedback to user**
```
User: xl join huge1.xlsx huge2.xlsx --on id
[Nothing happens for 5 minutes]
[User waits, wondering if it's working]
[Memory grows to 6GB]
[Crashes with generic Python error]
User: "What happened? Is my data corrupted?"
```

## Affected Files

All commands and operations are affected:
- `excel_toolkit/commands/*.py` (all commands)
- `excel_toolkit/operations/*.py` (all operations)
- `excel_toolkit/core/file_handlers.py` (file loading)

## Proposed Solution

### 1. Pre-Operation Memory Check

Check available memory before starting operations:

```python
import psutil

def check_memory_before_operation(operation_name: str, estimated_mb: int):
    """Check if enough memory is available before starting operation."""

    available_mb = psutil.virtual_memory().available / (1024 * 1024)
    total_mb = psutil.virtual_memory().total / (1024 * 1024)
    used_percent = psutil.virtual_memory().percent

    print(f"Memory check: {used_percent:.1f}% used ({available_mb:.0f}MB available)")

    # Require 3x safety margin
    required_mb = estimated_mb * 3

    if available_mb < required_mb:
        raise MemoryError(
            f"Not enough memory for {operation_name}.\n"
            f"Estimated need: {required_mb:.0f}MB\n"
            f"Available: {available_mb:.0f}MB\n"
            f"Please close other applications or use a smaller file."
        )

    if used_percent > 80:
        print(f"WARNING: Memory usage is at {used_percent:.1f}%")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            raise InterruptedError("Operation cancelled by user")
```

### 2. Mid-Operation Memory Monitoring

Monitor memory during long operations:

```python
def monitor_memory_during_operation(func):
    """Decorator to monitor memory during operation execution."""

    def wrapper(*args, **kwargs):
        process = psutil.Process()
        initial_memory = process.memory_info().rss / (1024 * 1024)

        print(f"Starting operation (memory: {initial_memory:.0f}MB)")

        try:
            result = func(*args, **kwargs)

            final_memory = process.memory_info().rss / (1024 * 1024)
            delta = final_memory - initial_memory

            print(f"Operation completed (memory: {final_memory:.0f}MB, delta: {delta:+.0f}MB)")

            return result

        except MemoryError:
            current_memory = process.memory_info().rss / (1024 * 1024)
            print(f"ERROR: Out of memory (current: {current_memory:.0f}MB)")
            print("Please try with a smaller file or fewer operations")
            raise

    return wrapper
```

### 3. Memory Estimation by Operation

```python
def estimate_memory_requirement(operation: str, **kwargs) -> int:
    """Estimate memory requirement for an operation in MB."""

    # Base file size
    file_size_mb = kwargs.get('file_size_mb', 0)

    # Operation-specific multipliers
    multipliers = {
        'read': 3.0,          # pandas overhead
        'filter': 2.0,        # creates copy
        'sort': 2.0,          # creates copy
        'groupby': 4.0,       # hash table + intermediates
        'merge': 3.0 * kwargs.get('num_files', 1),  # all files in memory
        'join': 3.0 * 2,      # both datasets
        'transform': 2.0,     # creates copy
        'aggregate': 4.0,     # hash table + intermediates
    }

    multiplier = multipliers.get(operation, 2.0)
    return int(file_size_mb * multiplier)
```

### 4. Graceful Degradation

When memory is running low, switch to safer strategies:

```python
def operation_with_fallback(file_path: Path):
    """Try normal operation, fall back to streaming if memory is low."""

    available_mb = psutil.virtual_memory().available / (1024 * 1024)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)

    if available_mb < file_size_mb * 2:
        print("Low memory detected, using streaming mode...")
        return operation_streaming(file_path)
    else:
        return operation_normal(file_path)
```

### 5. Memory Limit Configuration

Add configuration options in `const.py`:

```python
# Memory limits
MAX_MEMORY_USAGE_PERCENT = 85  # Warn when usage exceeds this
REQUIRED_MEMORY_MARGIN = 3.0   # Require 3x estimated memory
ENABLE_MEMORY_MONITORING = True
```

## Implementation Plan

### Phase 1: Basic Checks (High Priority)
1. Add `psutil` to dependencies
2. Implement `check_memory_before_operation()`
3. Add checks to file loading operations
4. Add checks to merge/join operations

### Phase 2: Mid-Operation Monitoring (Medium Priority)
1. Implement `monitor_memory_during_operation` decorator
2. Add to long-running operations (GroupBy, Join, Merge)
3. Show progress updates with memory usage

### Phase 3: Advanced Features (Low Priority)
1. Implement memory estimation for each operation type
2. Add graceful degradation strategies
3. Add configuration options

## Error Messages

### Good: Clear and Actionable
```
ERROR: Not enough memory for merge operation.

Details:
- File 1: 200MB (~600MB in memory)
- File 2: 250MB (~750MB in memory)
- Total required: ~1.4GB
- Available: 800MB

Suggestions:
1. Close other applications to free memory
2. Process files individually instead of merging
3. Use a machine with more RAM
```

### Bad: Generic Python Error
```
MemoryError: Unable to allocate 1.4 GiB for an array with shape
(500000, 20) and data type float64
```

## Dependencies

Add to `pyproject.toml`:
```toml
dependencies = [
    "psutil>=5.9.0",  # For memory monitoring
    ...
]
```

## Related Issues

- File loading memory issues (#001)
- File size limits too permissive (#002)
- Merge operations memory issues (#003)
- Join Cartesian product danger (#004)
