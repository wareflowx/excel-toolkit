# Title: Merge operations load all files into memory simultaneously, causing crashes

## Problem Description

The merge command in `excel_toolkit/commands/merge.py` loads all input files into memory **before** performing the merge operation. This is extremely dangerous when dealing with multiple large files (50k-500k rows each).

### Current Behavior

When merging multiple files:
1. **All files are loaded into memory simultaneously**
2. Then they are concatenated
3. Then the result is written

### Memory Impact Formula

```
Total Memory = (File1_size × 3) + (File2_size × 3) + ... + (FileN_size × 3) + Merge_overhead
```

The multiplier of 3 accounts for pandas overhead.

### Real-World Scenarios

**Scenario 1: Merging 3 medium files**
- 3 files × 200MB each on disk
- Memory usage: 200MB × 3 × 3 = **1.8GB minimum**
- With merge overhead: **2-2.5GB**
- Usable, but risky on 8GB systems

**Scenario 2: Merging 5 large files**
- 5 files × 300MB each on disk
- Memory usage: 300MB × 5 × 3 = **4.5GB minimum**
- With merge overhead: **5-6GB**
- Likely to crash or cause severe swapping

**Scenario 3: Merging many small files**
- 20 files × 50MB each on disk
- Total on disk: 1GB
- Memory usage: 50MB × 20 × 3 = **3GB minimum**
- Result: 5 million rows, hard to manage

## Affected Files

- `excel_toolkit/commands/merge.py`
- Potentially affects append operations too

## Proposed Solution

Implement **streaming merge** that processes files incrementally:

```python
def merge_files_streaming(file_paths: list[Path], output_path: Path):
    """Merge files one at a time, writing incrementally."""

    # Read first file
    result = pd.read_excel(file_paths[0])

    # Process remaining files one at a time
    for file_path in file_paths[1:]:
        chunk = pd.read_excel(file_path)

        # Concatenate with previous result
        result = pd.concat([result, chunk], ignore_index=True)

        # Write intermediate results to disk
        result.to_excel(output_path, index=False)

    return result
```

### Benefits

- Only keep 2 files in memory at a time (current result + next file)
- Write incrementally to avoid losing progress on crash
- Can merge unlimited number of files
- Better memory predictability

### Alternative: Chunked Merge

```python
def merge_files_chunked(file_paths: list[Path], output_path: Path, chunksize: int = 50000):
    """Merge files in chunks."""

    # Initialize writer
    writer = pd.ExcelWriter(output_path, engine='openpyxl')

    for file_path in file_paths:
        # Read file in chunks
        for chunk in pd.read_excel(file_path, chunksize=chunksize):
            # Process and write chunk
            chunk.to_excel(writer, index=False)

    writer.close()
```

## Additional Safeguards

1. **Memory check before merge**:
   ```python
   total_estimated_memory = sum(file_sizes) * 3
       if total_estimated_memory > available_memory:
           raise MemoryError("Cannot merge: not enough memory")
   ```

2. **Limit number of files**:
   ```python
   MAX_MERGE_FILES = 10
   if len(file_paths) > MAX_MERGE_FILES:
       raise ValueError(f"Cannot merge more than {MAX_MERGE_FILES} files at once")
   ```

3. **Row limit warning**:
   ```python
   MAX_RESULT_ROWS = 1_000_000
   if total_rows > MAX_RESULT_ROWS:
       print(f"Warning: Result will have {total_rows} rows")
   ```

## Related Issues

- File loading memory issues (#001)
- File size limits too permissive (#002)
- Memory monitoring needed (#006)
