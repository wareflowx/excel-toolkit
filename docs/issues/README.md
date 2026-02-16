# GitHub Issues Template Files

This directory contains draft GitHub issues for performance and memory problems when processing large files (50k-500k rows).

## Overview

These issue files document problems identified during analysis of large file handling in excel-toolkit. Each file is a complete draft ready to be converted into a GitHub issue.

## Issue Files

| # | File | Title | Priority |
|---|------|-------|----------|
| 001 | `001-file-loading-memory-issues.md` | Implement streaming/chunking for file loading | 🔴 High |
| 002 | `002-file-size-limits-too-permissive.md` | File size limits are too permissive | 🔴 High |
| 003 | `003-merge-operations-memory-issues.md` | Merge operations load all files simultaneously | 🔴 High |
| 004 | `004-join-cartesian-product-danger.md` | Join operations can create Cartesian products | 🔴 Critical |
| 005 | `005-groupby-performance-memory-issues.md` | GroupBy consumes excessive memory | 🟡 Medium |
| 006 | `006-memory-monitoring-needed.md` | Add memory monitoring | 🔴 High |
| 007 | `007-filtering-performance-issues.md` | Filtering uses slow query engine | 🟡 Medium |
| 008 | `008-functional-programming-overhead.md` | Functional programming adds overhead | 🟢 Low |
| 009 | `009-data-type-optimization-needed.md` | Optimize pandas data types | 🟡 Medium |
| 010 | `010-no-progress-feedback.md` | Add progress indicators | 🟢 Low |

## How to Create GitHub Issues

### Option 1: Using GitHub CLI (Recommended)

1. **Install GitHub CLI** (if not already installed):
   ```bash
   # Windows (winget)
   winget install GitHub.cli

   # Or download from https://cli.github.com/
   ```

2. **Authenticate with GitHub**:
   ```bash
   gh auth login
   ```

3. **Create an issue from a file**:
   ```bash
   # From the issue file
   gh issue create --body-file docs/issues/001-file-loading-memory-issues.md

   # Or with title
   gh issue create --title "Implement streaming/chunking for file loading" \
       --body-file docs/issues/001-file-loading-memory-issues.md
   ```

4. **Create all issues at once** (PowerShell):
   ```powershell
   Get-ChildItem docs/issues/*.md | Where-Object { $_.Name -ne 'README.md' } | ForEach-Object {
       gh issue create --body-file $_.FullName
   }
   ```

### Option 2: Manual Creation

1. Copy the content of an issue file
2. Go to: https://github.com/wareflowx/excel-toolkit/issues/new
3. Paste the content into the issue body
4. Extract the title from the first line: `# Title: ...`
5. Submit

### Option 3: Using the Web Interface with gh

```bash
# Open in browser with pre-filled content
gh issue create --web --body-file docs/issues/001-file-loading-memory-issues.md
```

## Issue File Format

Each issue file follows this structure:

```markdown
# Title: Issue Title Here

## Problem Description
Detailed explanation of the problem...

### Current Behavior
What happens now...

### Real-World Impact
Examples of how this affects users...

## Affected Files
List of files involved...

## Proposed Solution
Suggested fixes...

## Related Issues
References to other related issues...
```

## Priority Levels

- 🔴 **Critical**: Can cause system crashes or data loss
- 🔴 **High**: Major performance/memory issues affecting usability
- 🟡 **Medium**: Noticeable performance degradation
- 🟢 **Low**: Nice-to-have improvements

## Dependencies

Some issues depend on others:

- Issue #001 (chunking) helps with #003 (merge), #004 (join), #005 (groupby)
- Issue #006 (memory monitoring) is needed before #003, #004, #005
- Issue #009 (dtype optimization) works with #001 (chunking)

## Next Steps

1. Review all issue files
2. Prioritize based on your needs
3. Create issues using GitHub CLI
4. Assign labels after creation (if desired)

## After Creating Issues

Once issues are created on GitHub:
1. You can add labels (bug, enhancement, performance, etc.)
2. Assign to milestones
3. Link issues together using dependencies
4. Create project boards for tracking

## Notes

- These issues are drafts - modify as needed before creating
- The numbering (001-010) is for organization, not official GitHub issue numbers
- Remove this README file from the list when creating issues
