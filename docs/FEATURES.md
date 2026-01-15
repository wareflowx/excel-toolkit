# Excel CLI Toolkit - Features

## Overview

The Excel CLI Toolkit is a command-line interface tool designed for efficient data manipulation and analysis of Excel files. It provides a comprehensive set of operations for data wrangling, cleaning, transformation, and analysis that can be executed directly from the terminal without requiring scripting or programming knowledge.

This toolkit is particularly optimized for automated execution by AI systems while remaining fully accessible to human users. All operations are designed to be idempotent, predictable, and non-interactive.

## Core Design Principles

- **Non-interactive operations**: All commands are executed with explicit flags and parameters
- **Predictable output**: Operations either modify files in-place or create new output files
- **Clear exit codes**: Proper status codes for programmatic error handling
- **Pipeline support**: Commands can be chained together for complex workflows
- **Format agnostic**: Supports multiple formats including XLSX, CSV, JSON, and Parquet

## Feature Categories

### 1. Data Filtering and Selection

#### Filter
Filter rows based on specified criteria using comparison operators, regular expressions, or value matching.

```bash
xl filter data.xlsx --where "Amount > 1000" --output filtered.xlsx
xl filter data.xlsx --where "Region =~ 'North|South'" --output regional.xlsx
```

#### Select
Extract specific columns from a dataset, reducing the file to only the required fields.

```bash
xl select data.xlsx --columns "Name,Email,Phone" --output contacts.xlsx
```

#### Unique
Extract unique values from a specified column or identify unique rows across multiple columns.

```bash
xl unique data.xlsx --column "Category" --output categories.xlsx
```

#### Search
Search for specific values or patterns across the entire workbook or specific sheets.

```bash
xl search data.xlsx --pattern "ERROR" --column "Status"
```

### 2. Data Sorting and Organization

#### Sort
Sort data by one or multiple columns in ascending or descending order.

```bash
xl sort data.xlsx --by "Date" --descending --output sorted.xlsx
xl sort data.xlsx --by "Region,Amount" --output multi-sorted.xlsx
```

#### Group
Group data by specified columns and perform aggregations on value columns.

```bash
xl group sales.xlsx --by "Region" --aggregate "Amount:sum,Quantity:avg" --output grouped.xlsx
```

#### Pivot
Create pivot table-like summaries by specifying row, column, and value dimensions.

```bash
xl pivot data.xlsx --rows "Date" --columns "Product" --values "Sales:sum" --output pivot.xlsx
```

### 3. Data Cleaning and Quality

#### Clean
Clean data by removing whitespace, standardizing case, and fixing common formatting issues.

```bash
xl clean data.xlsx --trim --lowercase --columns "Email,Name" --output cleaned.xlsx
```

#### Deduplicate
Identify and remove duplicate rows based on specified key columns or across all columns.

```bash
xl dedupe data.xlsx --by "Email" --keep "first" --output unique.xlsx
xl dedupe data.xlsx --keep "last" --output no-duplicates.xlsx
```

#### Fill
Fill missing values with specified constants, statistical measures, or forward/backward fill.

```bash
xl fill data.xlsx --column "Age" --value "0" --output filled.xlsx
xl fill data.xlsx --column "Price" --strategy "median" --output filled.xlsx
```

#### Strip
Remove empty rows, rows with missing values in critical columns, or rows matching specific patterns.

```bash
xl strip-rows data.xlsx --empty --output clean.xlsx
xl strip-rows data.xlsx --where "Email is null" --output valid.xlsx
```

### 4. Data Transformation

#### Transform
Apply mathematical or string operations to columns.

```bash
xl transform data.xlsx --column "Price" --multiply "1.1" --output with-tax.xlsx
xl transform data.xlsx --column "Name" --operation "uppercase" --output upper.xlsx
```

#### Rename
Rename columns to more meaningful names or standardize naming conventions.

```bash
xl rename data.xlsx --mapping "old_name:new_name,first_name:fname" --output renamed.xlsx
```

#### Convert
Convert between different file formats while preserving data types and structure.

```bash
xl convert data.xlsx --output data.csv
xl convert data.csv --output data.xlsx
xl convert data.xlsx --output data.json
```

### 5. Data Combination

#### Merge
Combine multiple files or sheets vertically (stacking rows) or horizontally (joining columns).

```bash
xl merge file1.xlsx file2.xlsx file3.xlsx --output combined.xlsx
xl merge *.xlsx --output all-data.xlsx
```

#### Join
Join two datasets based on common columns, supporting inner, left, right, and outer joins.

```bash
xl join customers.xlsx orders.xlsx --on "customer_id" --type "left" --output merged.xlsx
xl join left.xlsx right.xlsx --left-on "id" --right-on "user_id" --output joined.xlsx
```

#### Append
Add data from one file to another, either creating new rows or new sheets.

```bash
xl append main.xlsx new-data.xlsx --output updated.xlsx
```

### 6. Data Analysis

#### Stats
Calculate statistical summaries including mean, median, standard deviation, minimum, maximum, and quartiles.

```bash
xl stats data.xlsx --column "Sales" --output statistics.json
xl stats data.xlsx --all-columns --output summary.txt
```

#### Count
Count occurrences of unique values in specified columns.

```bash
xl count data.xlsx --column "Status" --output counts.xlsx
xl count data.xlsx --by "Region,Category" --output multi-counts.xlsx
```

#### Aggregate
Perform custom aggregations (sum, average, count, min, max) on grouped data.

```bash
xl aggregate sales.xlsx --group "Region" --functions "Revenue:sum,Orders:count" --output summary.xlsx
```

#### Compare
Compare two files or sheets to identify differences, additions, and deletions.

```bash
xl diff old.xlsx new.xlsx --output changes.xlsx
xl compare expected.xlsx actual.xlsx --output differences.xlsx
```

### 7. Data Inspection

#### Info
Display metadata about the file including sheet names, column names, data types, and row counts.

```bash
xl info data.xlsx
xl info data.xlsx --format json
```

#### Head
Display the first N rows of a file for quick inspection.

```bash
xl head data.xlsx --rows 10
xl head data.xlsx --rows 5 --sheet "Summary"
```

#### Tail
Display the last N rows of a file.

```bash
xl tail data.xlsx --rows 10
```

#### Validate
Validate data against specified rules such as data types, value ranges, or pattern matching.

```bash
xl validate data.xlsx --rules "Email:email,Age:int:0-120" --output report.json
```

### 8. Data Export and Reporting

#### Export
Export data to various formats with customizable options.

```bash
xl export data.xlsx --format csv --delimiter "," --output data.csv
xl export data.xlsx --format json --orient "records" --output data.json
```

#### Template
Apply predefined templates for common data operations and reporting formats.

```bash
xl template clean-csv input.csv --output cleaned.xlsx
xl template sales-report data.xlsx --output report.xlsx
```

### 9. Batch Operations

#### Batch Process
Process multiple files using the same operation or workflow.

```bash
xl batch clean *.xlsx --operation "clean,trim" --output-dir cleaned/
xl batch process folder/ --pipeline "filter,group,sort" --output results/
```

## Advanced Features

### Pipeline Support
Commands can be chained together using standard Unix pipes for complex data transformations.

```bash
xl filter sales.xlsx --where "Amount > 100" | \
  xl group --by "Region" --aggregate "Amount:sum" | \
  xl sort --by "Amount" --descending \
  --output final.xlsx
```

### Variable Substitution
Support for variable placeholders in commands, enabling dynamic parameter replacement.

```bash
xl filter data.xlsx --where "{column} > {value}" --output result.xlsx
```

### Dry Run Mode
Preview operations without modifying any files using the dry-run flag.

```bash
xl transform data.xlsx --column "Price" --multiply "1.1" --dry-run
```

### Sheet Operations
Specify target sheets for multi-sheet workbooks.

```bash
xl filter data.xlsx --sheet "Q1" --where "Amount > 1000" --output q1-filtered.xlsx
```

### Performance Options
Control memory usage and processing speed for large files.

```bash
xl process large-file.xlsx --chunk-size 10000 --threads 4
```

## Command Structure

All commands follow a consistent structure:

```
xl <command> [input-file(s)] [options] --output <output-file>
```

### Common Options

- `--output, -o`: Specify output file path
- `--sheet, -s`: Target specific sheet
- `--columns, -cols`: Specify column names
- `--where`: Filter conditions
- `--format`: Output format (xlsx, csv, json, parquet)
- `--dry-run`: Preview without execution
- `--quiet, -q`: Minimal output
- `--verbose, -v`: Detailed logging
- `--help, -h`: Display help information

## Exit Codes

- `0`: Success
- `1`: General error
- `2`: File not found or inaccessible
- `3`: Invalid command syntax
- `4`: Data validation error
- `5`: Insufficient memory or resources

## Technical Specifications

### Supported File Formats

- Excel (.xlsx, .xlsm)
- CSV (with configurable delimiters)
- JSON (multiple structures)
- Apache Parquet
- ODS (OpenDocument Spreadsheet)

### Data Type Support

- Numeric (integer, float, currency)
- Text/string
- DateTime
- Boolean
- Formulas (evaluated to values)

### Limitations

- Maximum file size: System dependent (memory-mapped for large files)
- Maximum columns: 16,384 (Excel limitation)
- Maximum rows per sheet: 1,048,576 (Excel limitation)
- Formula complexity: Evaluated formulas only, no VBA macros

## Use Cases

### Data Cleaning Workflows
- Remove duplicates and standardize formatting
- Fill missing values and correct inconsistent data
- Validate data quality and generate reports

### Business Intelligence
- Aggregate and summarize transactional data
- Create regional or temporal breakdowns
- Generate periodic reports automatically

### Data Migration
- Convert legacy formats to modern standards
- Transform data between different systems
- Merge data from multiple sources

### Financial Analysis
- Filter and categorize financial transactions
- Calculate running totals and period comparisons
- Generate summary reports and dashboards

### Data Science Preparation
- Clean and preprocess datasets for analysis
- Create feature engineering pipelines
- Export data for machine learning workflows
