# Title: Improve error messages to be more actionable and user-friendly

## Problem Description

Error messages throughout the application are **generic, unhelpful, and don't guide users** toward solutions. Users receive cryptic error messages without context, suggestions, or examples of how to fix the problem.

### Current Examples of Poor Error Messages

**Example 1: Invalid filter condition**
```bash
$ xl filter data.xlsx "age >> 30"
Invalid condition: ParseError
# What does this mean? How do I fix it?
```

**Example 2: Column not found**
```bash
$ xl filter data.xlsx "ag > 30"
Invalid condition: ColumnNotFoundError
# Which column? What are available columns?
```

**Example 3: File not found**
```bash
$ xl filter data.xlsx "age > 30"
File not found: data.xlsx
# Should I check the path? Did I misspell it?
```

**Example 4: Invalid aggregation**
```bash
$ xl group sales.xlsx --by Region --aggregate "Amount:avrage"
Invalid function: InvalidFunctionError
# Did I misspell 'average'? What functions are available?
```

### What Makes Error Messages Poor

1. **No context**: Don't explain WHAT went wrong
2. **No guidance**: Don't explain HOW to fix it
3. **No examples**: Don't show correct usage
4. **Technical jargon**: Use class names instead of plain English
5. **No suggestions**: Don't offer alternatives or similar commands
6. **Missing details**: Don't show relevant information (line numbers, available values, etc.)

### Real-World Impact

**User Story 1: New user frustration**
```
User: $ xl filter sales.xlsx "Amount > 1000"
Output: Invalid condition: QueryFailedError

User thoughts: "What's a QueryFailedError? What did I do wrong?
Is it the column name? The syntax? The value?"
User action: Gives up and uses Excel instead
```

**User Story 2: Wasted time debugging**
```
User: $ xl filter data.xlsx "user_id == 'ABC123'"
Output: Invalid condition: ColumnNotFoundError

User: "But user_id exists! Let me check..."
[10 minutes of debugging]
User: "Oh, it's 'UserID' not 'user_id'! Case sensitivity!"
Could have been saved if error said: "Column 'user_id' not found.
Did you mean 'UserID'?"
```

**User Story 3: Documentation rabbit hole**
```
User: $ xl transform data.xlsx --col "Amount" --expr "log(Amount)"
Output: Invalid expression: InvalidExpressionError

User: "What expressions are supported?"
[Has to search documentation for 10 minutes]
Could have been shown in error message!
```

## Affected Areas

All commands and operations:
- Filter conditions
- Transform expressions
- Aggregation specifications
- File operations
- Column references
- Data validation errors

## Proposed Solution

### 1. Create Error Message Builder

```python
# excel_toolkit/core/errors.py

"""Enhanced error messages with context and guidance."""

from typing import Any, List, Optional
import pandas as pd

class UserFacingError(Exception):
    """Base class for user-facing errors with helpful messages."""

    def __init__(
        self,
        message: str,
        context: str = "",
        suggestions: List[str] | None = None,
        examples: List[str] | None = None
    ):
        self.message = message
        self.context = context
        self.suggestions = suggestions or []
        self.examples = examples or []

    def __str__(self):
        parts = [f"❌ {self.message}"]

        if self.context:
            parts.append(f"\n📋 Context: {self.context}")

        if self.suggestions:
            parts.append("\n💡 Suggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"   {i}. {suggestion}")

        if self.examples:
            parts.append("\n✨ Examples:")
            for example in self.examples:
                parts.append(f"   • {example}")

        return "\n".join(parts)


class ColumnNotFoundError(UserFacingError):
    """Column not found with helpful suggestions."""

    def __init__(self, column: str, available_columns: List[str]):
        # Find similar columns
        similar = find_similar_columns(column, available_columns)

        suggestions = []
        if similar:
            suggestions.append(f"Did you mean: {', '.join(similar)}?")
        suggestions.append(f"Available columns: {', '.join(available_columns[:10])}")
        if len(available_columns) > 10:
            suggestions.append(f"... and {len(available_columns) - 10} more")

        examples = [
            f'xl filter data.xlsx "{column[0].upper()}{column[1:]} > 100"',
        ]

        super().__init__(
            message=f"Column '{column}' not found",
            context=f"The file has {len(available_columns)} columns",
            suggestions=suggestions,
            examples=examples
        )


def find_similar_columns(target: str, columns: List[str], max_distance: int = 2) -> List[str]:
    """Find columns with similar names (for typo correction)."""
    import difflib

    matches = difflib.get_close_matches(
        target.lower(),
        [c.lower() for c in columns],
        n=3,
        cutoff=0.6
    )

    # Return original casing
    return [c for c in columns if c.lower() in matches]
```

### 2. Update Error Handling Throughout

```python
# operations/filtering.py

def apply_filter(df: pd.DataFrame, condition: str) -> Result[pd.DataFrame, FilterError]:
    """Apply filter with enhanced error messages."""

    # Validate columns exist
    columns_in_condition = extract_columns(condition)
    for col in columns_in_condition:
        if col not in df.columns:
            from excel_toolkit.core.errors import ColumnNotFoundError
            raise ColumnNotFoundError(col, list(df.columns))

    # Rest of filtering logic...
```

### 3. Add Command-Specific Error Helpers

```python
# commands/filter.py

def show_filter_error(error: Exception):
    """Show helpful error message for filter command."""

    if isinstance(error, ColumnNotFoundError):
        # Already formatted by ColumnNotFoundError
        typer.echo(str(error), err=True)

    elif isinstance(error, ParseError):
        typer.echo("❌ Invalid filter condition syntax", err=True)
        typer.echo("\n💡 Syntax tips:", err=True)
        typer.echo("   • Comparisons: age > 30, price >= 100", err=True)
        typer.echo("   • Strings: name == 'John'", err=True)
        typer.echo("   • Logical: age > 25 and city == 'Paris'", err=True)
        typer.echo("   • Null checks: value.isna(), value.notna()", err=True)

        typer.echo("\n✨ Examples:", err=True)
        typer.echo("   xl filter data.xlsx 'age > 30'", err=True)
        typer.echo("   xl filter data.csv \"city == 'Paris'\"", err=True)
        typer.echo("   xl filter data.xlsx 'amount > 1000 and status == \"active\"'", err=True)

    elif isinstance(error, QueryFailedError):
        typer.echo("❌ Failed to execute filter condition", err=True)
        typer.echo(f"\n📋 Condition: {error.condition}", err=True)

        # Try to give specific advice
        if "SyntaxError" in str(error):
            typer.echo("\n💡 Check for:", err=True)
            typer.echo("   • Balanced quotes: name == 'John'", err=True)
            typer.echo("   • Balanced parentheses: (age > 30) or (amount < 100)", err=True)
```

### 4. Before/After Examples

**Before:**
```bash
$ xl filter data.xlsx "ag > 30"
Invalid condition: ColumnNotFoundError
```

**After:**
```bash
$ xl filter data.xlsx "ag > 30"
❌ Column 'ag' not found
📋 Context: The file has 5 columns
💡 Suggestions:
   1. Did you mean: age?
   2. Available columns: id, age, name, city, amount
✨ Examples:
   • xl filter data.xlsx "age > 100"
```

**Before:**
```bash
$ xl transform data.xlsx --col Amount --expr "log(Amount)"
Invalid expression: InvalidExpressionError
```

**After:**
```bash
$ xl transform data.xlsx --col Amount --expr "log(Amount)"
❌ Invalid expression: Function 'log' is not supported
📋 Context: Transform expressions support basic math operations
💡 Suggestions:
   1. Use numpy functions: np.log(Amount)
   2. Basic math: Amount * 2, Amount + 100
   3. Available operators: +, -, *, /, **, %
✨ Examples:
   • xl transform data.xlsx --col Amount --expr "Amount * 1.1"
   • xl transform data.xlsx --col Price --expr "Price * 0.9 - 5"
```

### 5. Add Verbose Error Mode

```python
# cli.py

@app.command()
def filter(
    file_path: str,
    condition: str,
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed error messages")
):
    """Filter rows with optional verbose errors."""

    try:
        # ... filtering logic ...
        pass

    except Exception as e:
        if verbose:
            # Show stack trace and technical details
            typer.echo(traceback.format_exc(), err=True)
        else:
            # Show user-friendly message
            show_filter_error(e)
```

## Implementation Priority

1. **High Priority**: Column not found (most common error)
2. **High Priority**: Invalid filter condition syntax
3. **Medium Priority**: Invalid aggregation functions
4. **Medium Priority**: File operation errors
5. **Low Priority**: All other error messages

## Related Issues

- Missing help context (#018)
- No input sanitization (#013)
