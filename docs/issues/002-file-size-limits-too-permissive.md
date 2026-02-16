# Title: File size limits are too permissive and can cause system crashes

## Problem Description

The current file size limits in `excel_toolkit/core/const.py` allow files that, when loaded into memory, can overwhelm typical systems and cause crashes or severe performance degradation.

### Current Limits

In `const.py` (lines 26-27):
```python
MAX_FILE_SIZE_MB = 500
WARNING_FILE_SIZE_MB = 100
```

### The Problem

These limits refer to **file size on disk**, not memory usage. However, when pandas loads an Excel/CSV file, the memory usage is typically **2-4x the file size** due to:
- Pandas DataFrame overhead
- Python object overhead
- String data expansion
- Index creation
- Type conversions

### Real-World Examples

| File on Disk | Memory Usage | Safe? |
|--------------|--------------|-------|
| 50MB | 100-200MB | ✅ Yes |
| 100MB | 200-400MB | ⚠️ Warning threshold |
| 200MB | 400-800MB | ❌ No warning, but risky |
| 500MB | 1-2GB | ❌ At MAX limit, can crash 8GB systems |
| 500MB (multi-sheet) | 2-4GB | 💀 Approaches MAX limit |

### Impact Scenarios

**Scenario 1**: User has 8GB RAM, 4GB available
- Opens a 500MB Excel file with 3 sheets
- Memory usage: 500MB × 3 sheets × 3 (overhead) = **4.5GB**
- Result: System crash or severe swapping

**Scenario 2**: Merge operation with 3 files
- Each file: 300MB on disk
- Total memory: 300MB × 3 files × 3 (overhead) = **2.7GB**
- Plus merge operation overhead: **3-4GB total**
- May exceed available memory

## Affected Files

- `excel_toolkit/core/const.py` (lines 26-27)
- `excel_toolkit/core/file_handlers.py` (size checks at lines 99-100, 308-309)

## Proposed Solution

Update file size limits to be more conservative and aligned with actual memory usage:

```python
# More conservative limits based on actual memory impact
MAX_FILE_SIZE_MB = 100  # ~300-400MB in memory
WARNING_FILE_SIZE_MB = 25  # ~75-100MB in memory
```

### Justification

- **100MB file on disk** ≈ 300-400MB in memory (safe for most systems)
- **25MB file on disk** ≈ 75-100MB in memory (reasonable warning threshold)
- Systems with 4GB RAM can still function
- Multi-sheet files won't immediately crash systems

### Alternative Approach

Implement **memory-based limits** instead of file-size limits:

```python
import psutil

def check_available_memory(required_mb: int):
    """Check if enough memory is available."""
    available = psutil.virtual_memory().available / (1024 * 1024)
    if available < required_mb * 3:  # 3x safety factor
        raise MemoryError(f"Not enough memory. Need: {required_mb * 3}MB, Available: {available}MB")
```

## Related Issues

- File loading memory issues (#001)
- Memory monitoring needed (#006)
