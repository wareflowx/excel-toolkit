# Title: Add comprehensive examples and context to command help messages

## Problem Description

Command help messages lack **practical examples** and **usage context**, making it difficult for users to discover features and understand how to use complex operations correctly.

### Current Help Output

```bash
$ xl group --help

Usage: xl group [OPTIONS] DATA_PATH

  Group and aggregate data by specified columns.

Options:
  --by TEXT               Columns to group by
  --aggregate TEXT        Aggregation specifications
  --output TEXT           Output file path
  --help                  Show this message and exit
```

**Problems**:
- No examples of how to use `--aggregate`
- No explanation of aggregation syntax
- No real-world usage scenarios
- No mention of common pitfalls

### What's Missing

1. **No examples**: Most commands have 0 examples
2. **No syntax explanations**: Complex options not explained
3. **No use cases**: When to use this command?
4. **No common patterns**: How users typically combine commands
5. **No troubleshooting**: Common errors and fixes

### Real-World Impact

**Scenario 1: User can't figure out aggregation syntax**
```bash
$ xl group sales.xlsx --by Region --aggregate "Amount:sum"
Error: Invalid format

User: "What's the correct format? Let me try..."
[Tries 5 different combinations]
$ xl group sales.xlsx --by Region --aggregate "Amount sum"
$ xl group sales.xlsx --by Region --aggregate "sum(Amount)"
$ xl group sales.xlsx --by Region --aggregate "Amount:sum,mean"

Finally gets it right after 10 minutes of trial and error.
```

**Scenario 2: User doesn't know multi-column grouping is possible**
```bash
User wants to group by Region AND Product
Doesn't know if it's supported
Has to read source code to find out

Could have been shown in help!
```

**Scenario 3: User doesn't know about output formats**
```bash
$ xl filter data.xlsx "age > 30"
[Shows table]

User: "Can I save this? How? What formats?"
Help doesn't show examples of --output option
```

## Affected Commands

All commands, especially complex ones:
- `group` (aggregation syntax)
- `aggregate` (aggregation syntax)
- `join` (join types, column selection)
- `pivot` (multi-dimensional pivots)
- `transform` (expression syntax)
- `validate` (validation spec syntax)
- `convert` (format options)

## Proposed Solution

### 1. Add Comprehensive Examples to Help

```python
# commands/group.py

@app.command()
def group(
    data_path: str = typer.Argument(..., help="Path to input file"),
    by: str = typer.Option(..., "--by", help="Columns to group by"),
    aggregate: str = typer.Option(..., "--aggregate", help="Aggregation specifications"),
    output: str | None = typer.Option(None, "--output", "-o", help="Output file path"),
    ...
):
    """
    Group and aggregate data by specified columns.

    The aggregate command combines rows with the same group values and
    calculates summary statistics (sum, mean, count, etc.) for each group.

    **AGGREGATION SYNTAX:**

    The --aggregate option uses the format: "column:function1,function2,..."

    Multiple aggregations are separated by commas:
        "Revenue:sum,mean"           → Sum and mean of Revenue
        "Sales:sum,count"            → Sum and count of Sales
        "Amount:sum,Profit:mean"     → Multiple columns

    Available functions: sum, mean/avg, median, min, max, count, std, var

    **EXAMPLES:**

    Single column, single aggregation:
        $ xl group sales.xlsx --by Region --aggregate "Revenue:sum"

    Single column, multiple aggregations:
        $ xl group sales.xlsx --by Region --aggregate "Revenue:sum,mean,count"

    Multiple group columns:
        $ xl group sales.xlsx --by "Region,Product" --aggregate "Revenue:sum"

    Multiple aggregations on multiple columns:
        $ xl group sales.xlsx --by Region --aggregate "Revenue:sum,mean,Profit:sum"

    Group by month (date extraction):
        $ xl group sales.xlsx --by "Date:month" --aggregate "Revenue:sum"

    Save to file:
        $ xl group sales.xlsx --by Region --aggregate "Revenue:sum" --output summary.xlsx

    **COMMON USE CASES:**

    Summarize sales by region:
        $ xl group sales.xlsx --by Region --aggregate "Amount:sum"

    Count customers per city:
        $ xl group customers.xlsx --by City --aggregate "CustomerID:count"

    Average order value by customer:
        $ xl group orders.xlsx --by CustomerID --aggregate "OrderValue:mean"

    **TROUBLESHOOTING:**

    Error "Invalid function":
        → Check function name (use: sum, mean, median, min, max, count, std, var)

    Error "Column not found":
        → Check column name is exact (case-sensitive)
        → Use xl info data.xlsx to see available columns

    Error "No valid specifications":
        → Check format is "column:function" (colon required)
    """
    # ... implementation ...
```

### 2. Add Usage Tips After Errors

```python
def group(...):
    """Group command with helpful errors."""

    try:
        # Parse aggregation specs
        agg_specs = parse_aggregations(aggregate)

    except ParseError as e:
        typer.echo("❌ Invalid aggregation specification", err=True)
        typer.echo(f"\n📋 Your input: {aggregate}", err=True)

        typer.echo("\n💡 Correct format:", err=True)
        typer.echo("   column:function1,function2,...", err=True)

        typer.echo("\n✨ Examples:", err=True)
        typer.echo('   "Revenue:sum"              → Sum of Revenue column', err=True)
        typer.echo('   "Sales:sum,mean"            → Sum and mean of Sales', err=True)
        typer.echo('   "Amount:sum,Profit:mean"    → Multiple columns', err=True)

        typer.echo("\n📚 Available functions:", err=True)
        typer.echo("   sum, mean, median, min, max, count, std, var", err=True)

        raise typer.Exit(1)
```

### 3. Add "Did you know?" Tips

```python
# After successful operation
if output:
    typer.echo(f"✓ Saved to {output}")
    typer.echo("\n💡 Did you know?")
    typer.echo("   • You can chain multiple operations: xl filter ... | xl group ...")
    typer.echo("   • Use --format=json for JSON output instead of Excel")
    typer.echo("   • Run 'xl info' to see file information before processing")
```

### 4. Create Example Gallery

```bash
$ xl examples

# Shows a gallery of examples

Excel Toolkit Examples
======================

DATA FILTERING:
  xl filter sales.xlsx "Amount > 1000"
  xl filter data.csv "age > 30 and city == 'Paris'"
  xl filter data.xlsx "status.isna()" --output clean.xlsx

DATA TRANSFORMATION:
  xl transform sales.xlsx --col Amount --expr "Amount * 1.1" --output adjusted.xlsx
  xl transform data.xlsx --col Name --expr "Name.strip().lower()"

DATA AGGREGATION:
  xl group sales.xlsx --by Region --aggregate "Revenue:sum"
  xl group sales.xlsx --by "Region,Product" --aggregate "Revenue:sum,mean,count"

DATA JOINING:
  xl join orders.xlsx customers.xlsx --on CustomerID --how inner
  xl join left.xlsx right.xlsx --on "ID,Date" --how left

DATA VALIDATION:
  xl validate data.xlsx --columns "age:int:0-120,email:email"

FILE CONVERSIONS:
  xl convert data.csv --output data.xlsx
  xl convert report.xlsx --output report.csv --format csv

[Press 'q' to quit, or run 'xl examples filter' for filtering examples]
```

### 5. Add Interactive Help

```python
@app.command()
def explain(
    command: str = typer.Argument(..., help="Command to explain")
):
    """Show detailed explanation and examples for a command."""

    explanations = {
        "group": """
GROUP COMMAND - Detailed Explanation
=====================================

PURPOSE:
    Combine rows with identical values and calculate summary statistics.

WHEN TO USE:
    • Summarizing data by category (sales by region)
    • Computing statistics per group (average order per customer)
    • Creating pivot-table-like summaries
    • Reducing detailed data to aggregated totals

SYNTAX:
    xl group FILE --by COLUMNS --aggregate SPECS

PARAMETERS:
    --by            Which columns to group by (comma-separated)
                    Can be multiple: --by "Region,Product"

    --aggregate     What to calculate for each group
                    Format: "Column:func1,func2,..."

    --output        Where to save results (optional)
                    If not provided, displays on screen

STEP-BY-STEP EXAMPLES:

1. Start simple - total sales per region:
   $ xl group sales.xlsx --by Region --aggregate "Amount:sum"

   Output:
       Region    | Amount_sum
       ----------|------------
       North     |     45000
       South     |     52000
       East      |     38000

2. Add more aggregations - sum AND count:
   $ xl group sales.xlsx --by Region --aggregate "Amount:sum,count"

   Output:
       Region    | Amount_sum | Amount_count
       ----------|------------|-------------
       North     |     45000  |         450
       South     |     52000  |         520

3. Multiple groups - by region AND product:
   $ xl group sales.xlsx --by "Region,Product" --aggregate "Amount:sum"

4. Multiple columns - revenue AND profit:
   $ xl group sales.xlsx --by Region --aggregate "Revenue:sum,Profit:sum"

COMMON FUNCTIONS:
    sum     → Total (add all values)
    mean    → Average (sum / count)
    median  → Middle value when sorted
    min     → Smallest value
    max     → Largest value
    count   → Number of rows
    std     → Standard deviation (spread)
    var     → Variance

COMMON ERRORS:

Error: "Column not found"
→ Check column name matches exactly (case-sensitive)
→ Use: xl info data.xlsx to see available columns

Error: "Invalid function"
→ Function name must be one of: sum, mean, median, min, max, count, std, var
→ Check spelling: 'avg' should be 'mean'

Error: "No valid specifications"
→ Format must be "column:function" (colon required)
→ Wrong: "Amount sum"
→ Right: "Amount:sum"
        """
    }

    typer.echo(explanations.get(command, f"No explanation for '{command}'"))
```

## Implementation Priority

1. **High Priority**: Add examples to complex commands (group, join, pivot, validate)
2. **High Priority**: Improve error messages with syntax tips
3. **Medium Priority**: Add `xl explain` command
4. **Medium Priority**: Add `xl examples` gallery
5. **Low Priority**: Add "Did you know?" tips

## Related Issues

- Poor error messages (#017)
