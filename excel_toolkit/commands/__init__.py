"""Commands module for Excel CLI Toolkit.

This module contains all CLI commands for the toolkit.
Each command is a separate module that can be imported and tested.
"""

# Command imports
from excel_toolkit.commands.append import app as append_app
from excel_toolkit.commands.append import append
from excel_toolkit.commands.clean import app as clean_app
from excel_toolkit.commands.clean import clean
from excel_toolkit.commands.convert import app as convert_app
from excel_toolkit.commands.convert import convert
from excel_toolkit.commands.count import app as count_app
from excel_toolkit.commands.count import count
from excel_toolkit.commands.dedupe import app as dedupe_app
from excel_toolkit.commands.dedupe import dedupe
from excel_toolkit.commands.export import app as export_app
from excel_toolkit.commands.export import export
from excel_toolkit.commands.fill import app as fill_app
from excel_toolkit.commands.fill import fill
from excel_toolkit.commands.filter import app as filter_app
from excel_toolkit.commands.filter import filter
from excel_toolkit.commands.group import app as group_app
from excel_toolkit.commands.group import group
from excel_toolkit.commands.head import app as head_app
from excel_toolkit.commands.head import head
from excel_toolkit.commands.info import app as info_app
from excel_toolkit.commands.info import info
from excel_toolkit.commands.join import app as join_app
from excel_toolkit.commands.join import join
from excel_toolkit.commands.merge import app as merge_app
from excel_toolkit.commands.merge import merge
from excel_toolkit.commands.rename import app as rename_app
from excel_toolkit.commands.rename import rename
from excel_toolkit.commands.search import app as search_app
from excel_toolkit.commands.search import search
from excel_toolkit.commands.select import app as select_app
from excel_toolkit.commands.select import select
from excel_toolkit.commands.sort import app as sort_app
from excel_toolkit.commands.sort import sort
from excel_toolkit.commands.stats import app as stats_app
from excel_toolkit.commands.stats import stats
from excel_toolkit.commands.strip import app as strip_app
from excel_toolkit.commands.strip import strip
from excel_toolkit.commands.tail import app as tail_app
from excel_toolkit.commands.tail import tail
from excel_toolkit.commands.transform import app as transform_app
from excel_toolkit.commands.transform import transform
from excel_toolkit.commands.unique import app as unique_app
from excel_toolkit.commands.unique import unique
from excel_toolkit.commands.validate import app as validate_app
from excel_toolkit.commands.validate import validate

__all__ = [
    "info",
    "info_app",
    "head",
    "head_app",
    "filter",
    "filter_app",
    "sort",
    "sort_app",
    "stats",
    "stats_app",
    "validate",
    "validate_app",
    "clean",
    "clean_app",
    "select",
    "select_app",
    "dedupe",
    "dedupe_app",
    "fill",
    "fill_app",
    "group",
    "group_app",
    "unique",
    "unique_app",
    "transform",
    "transform_app",
    "rename",
    "rename_app",
    "search",
    "search_app",
    "convert",
    "convert_app",
    "merge",
    "merge_app",
    "join",
    "join_app",
    "tail",
    "tail_app",
    "count",
    "count_app",
    "append",
    "append_app",
    "strip",
    "strip_app",
    "export",
    "export_app",
]
