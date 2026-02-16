# Title: Implement streaming/chunking for file loading to handle large files (50k-500k rows)

## Problem Description

The current file loading implementation in `excel_toolkit/core/file_handlers.py` loads entire files into memory at once without any streaming or chunking capabilities. This creates significant memory issues when processing large Excel/CSV files with 50k-500k rows.

### Current Behavior

In `file_handlers.py`:
- Line 110: `pd.read_excel()` loads the entire Excel file into memory
- Line 149: `read_all_sheets()` loads ALL sheets simultaneously
- Line 313: `pd.read_csv()` loads the entire CSV file into memory

### Memory Impact

For a 500k row file with 20 columns:
- **Memory usage**: 500MB - 2GB depending on data types
- **Load time**: 10-30 seconds
- The file is completely loaded before any operation can begin
- No possibility to process data incrementally

### Real-World Impact

When processing a 500MB Excel file:
- File size on disk: 500MB
- Memory usage after loading: 2-4GB (pandas overhead)
- For multi-sheet files: memory usage multiplies by number of sheets
- Systems with 8GB RAM can crash or experience severe swapping

## Affected Files

- `excel_toolkit/core/file_handlers.py` (lines 110, 149, 313)
- `excel_toolkit/core/const.py` (file size limits)

## Proposed Solution

Implement chunked reading for large files:

```python
# For large files, read in chunks
chunks = pd.read_excel(file_path, chunksize=50000)
for chunk in chunks:
    process_chunk(chunk)
    # Write results incrementally
```

Benefits:
- Process files without loading everything into memory
- Handle files larger than available RAM
- Enable incremental processing and writing
- Better user feedback during long operations

## Alternative Approaches

1. Use `dtype` parameter to optimize memory during loading
2. Implement lazy loading with Polars instead of pandas
3. Use Dask for out-of-core computation

## Additional Context

This is especially critical for:
- **Merge operations**: Loading multiple large files simultaneously
- **Multi-sheet Excel files**: All sheets loaded at once
- **Servers/constrained environments**: Limited memory available

The current `MAX_FILE_SIZE_MB = 500` limit is misleading because a 500MB file on disk can easily consume 2-4GB in memory.

## Related Issues

- File size limits too permissive (#002)
- Memory monitoring needed (#006)
- Merge operations memory issues (#003)
