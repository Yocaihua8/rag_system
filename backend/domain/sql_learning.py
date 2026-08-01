"""Deterministic, read-only SQLite grading for project-linked learning exercises.

The sandbox deliberately has no dependency on ``KnowledgeStore`` and accepts no
database path.  Every grading run builds a fresh database from a validated,
structured fixture and reopens that database in read-only mode before executing
learner SQL.
"""

from __future__ import annotations

import json
import hashlib
import math
import re
import sqlite3
import tempfile
import time
from collections import Counter
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from urllib.parse import quote


_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,63}$")
_ALLOWED_DATA_TYPES = frozenset({"INTEGER", "REAL", "TEXT", "BLOB", "NUMERIC"})
_ALLOWED_REQUIRED_CLAUSES = frozenset(
    {"where", "join", "group_by", "having", "order_by", "distinct"}
)
_SAFE_FUNCTIONS = frozenset(
    {
        "abs",
        "avg",
        "coalesce",
        "count",
        "glob",
        "ifnull",
        "instr",
        "length",
        "like",
        "lower",
        "ltrim",
        "max",
        "min",
        "nullif",
        "replace",
        "round",
        "rtrim",
        "substr",
        "substring",
        "sum",
        "total",
        "trim",
        "typeof",
        "upper",
    }
)
_SQL_KEYWORDS = frozenset(
    {
        "all",
        "and",
        "as",
        "asc",
        "between",
        "by",
        "case",
        "collate",
        "cross",
        "desc",
        "distinct",
        "else",
        "end",
        "from",
        "full",
        "having",
        "in",
        "inner",
        "is",
        "join",
        "left",
        "like",
        "not",
        "null",
        "on",
        "or",
        "outer",
        "right",
        "select",
        "then",
        "when",
        "where",
    }
)


class SqlFixtureError(ValueError):
    """Raised when trusted exercise data cannot form a safe fixture."""


@dataclass(frozen=True)
class SqlSandboxLimits:
    max_sql_chars: int = 10_000
    timeout_seconds: float = 1.0
    max_vm_steps: int = 1_000_000
    progress_ops: int = 1_000
    max_rows: int = 200
    max_columns: int = 32
    max_result_bytes: int = 256 * 1024
    max_tables: int = 8
    max_seed_rows: int = 1_000


@dataclass(frozen=True)
class SqlColumn:
    name: str
    data_type: str = "TEXT"
    nullable: bool = True


@dataclass(frozen=True)
class SqlTable:
    name: str
    columns: tuple[SqlColumn, ...]
    rows: tuple[tuple[Any, ...], ...] = ()


@dataclass(frozen=True)
class SqlExerciseFixture:
    tables: tuple[SqlTable, ...]
    expected_columns: tuple[str, ...]
    expected_rows: tuple[tuple[Any, ...], ...]
    order_sensitive: bool = False
    required_tables: tuple[str, ...] = ()
    required_clauses: tuple[str, ...] = ()
    required_functions: tuple[str, ...] = ()
    required_columns: tuple[str, ...] = ()
    required_where_columns: tuple[str, ...] = ()
    required_group_by_columns: tuple[str, ...] = ()
    required_join_columns: tuple[str, ...] = ()
    limits: SqlSandboxLimits = field(default_factory=SqlSandboxLimits)


def fixture_from_mapping(data: Mapping[str, Any]) -> SqlExerciseFixture:
    """Build a typed fixture from persisted structured JSON."""

    _verify_fixture_hash(data)
    limits_data = dict(data.get("limits") or {})
    if "max_bytes" in limits_data and "max_result_bytes" not in limits_data:
        limits_data["max_result_bytes"] = limits_data["max_bytes"]
    limits = SqlSandboxLimits(
        **{
            key: limits_data[key]
            for key in SqlSandboxLimits.__dataclass_fields__
            if key in limits_data
        }
    )
    _validate_absolute_limits(limits)
    table_data = data.get("tables") or data.get("schema") or ()
    seed_rows = data.get("seed_rows") or {}
    tables: list[SqlTable] = []
    for table in table_data:
        columns = tuple(
            SqlColumn(
                name=str(column["name"]),
                data_type=str(
                    column.get("data_type", column.get("type", "TEXT"))
                ),
                nullable=bool(column.get("nullable", True)),
            )
            for column in table.get("columns", ())
        )
        table_name = str(table["name"])
        raw_rows = table.get("rows")
        if raw_rows is None:
            raw_rows = seed_rows.get(table_name, ())
        ordered_rows: list[tuple[Any, ...]] = []
        column_names = tuple(column.name for column in columns)
        for row in raw_rows:
            if isinstance(row, Mapping):
                if set(row) != set(column_names):
                    raise SqlFixtureError(
                        f"seed row keys do not match schema for table {table_name}"
                    )
                ordered_rows.append(tuple(row[name] for name in column_names))
            else:
                ordered_rows.append(tuple(row))
        tables.append(
            SqlTable(
                name=table_name,
                columns=columns,
                rows=tuple(ordered_rows),
            )
        )
    required_semantics = data.get("required_semantics") or {}
    return SqlExerciseFixture(
        tables=tuple(tables),
        expected_columns=tuple(str(item) for item in data.get("expected_columns", ())),
        expected_rows=tuple(tuple(row) for row in data.get("expected_rows", ())),
        order_sensitive=bool(data.get("order_sensitive", False)),
        required_tables=tuple(
            str(item)
            for item in required_semantics.get(
                "tables",
                data.get("required_tables", ()),
            )
        ),
        required_clauses=tuple(
            str(item)
            for item in required_semantics.get(
                "clauses",
                data.get("required_clauses", ()),
            )
        ),
        required_functions=tuple(
            str(item)
            for item in required_semantics.get(
                "functions",
                data.get("required_functions", ()),
            )
        ),
        required_columns=tuple(
            str(item)
            for item in required_semantics.get(
                "columns",
                data.get("required_columns", ()),
            )
        ),
        required_where_columns=tuple(
            str(item)
            for item in required_semantics.get(
                "where_columns",
                data.get("required_where_columns", ()),
            )
        ),
        required_group_by_columns=tuple(
            str(item)
            for item in required_semantics.get(
                "group_by_columns",
                data.get("required_group_by_columns", ()),
            )
        ),
        required_join_columns=tuple(
            str(item)
            for item in required_semantics.get(
                "join_columns",
                data.get("required_join_columns", ()),
            )
        ),
        limits=limits,
    )


def _verify_fixture_hash(data: Mapping[str, Any]) -> None:
    provided = str(data.get("fixture_hash") or "").strip()
    if not provided:
        return
    payload = {
        str(key): value
        for key, value in data.items()
        if str(key) != "fixture_hash"
    }
    try:
        raw = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise SqlFixtureError("fixture_hash payload is not JSON-safe") from exc
    actual = hashlib.sha256(raw).hexdigest()
    if not _constant_time_text_equal(provided.casefold(), actual):
        raise SqlFixtureError("fixture_hash does not match fixture content")


def _constant_time_text_equal(left: str, right: str) -> bool:
    if len(left) != len(right):
        return False
    difference = 0
    for left_char, right_char in zip(left.encode(), right.encode()):
        difference |= left_char ^ right_char
    return difference == 0


def _validate_absolute_limits(limits: SqlSandboxLimits) -> None:
    absolute = SqlSandboxLimits()
    for field_name in (
        "max_sql_chars",
        "max_vm_steps",
        "progress_ops",
        "max_rows",
        "max_columns",
        "max_result_bytes",
        "max_tables",
        "max_seed_rows",
    ):
        value = getattr(limits, field_name)
        maximum = getattr(absolute, field_name)
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise SqlFixtureError(f"{field_name} must be a positive integer")
        if value > maximum:
            raise SqlFixtureError(
                f"{field_name} exceeds the absolute sandbox limit"
            )
    if (
        not isinstance(limits.timeout_seconds, (int, float))
        or isinstance(limits.timeout_seconds, bool)
        or not math.isfinite(float(limits.timeout_seconds))
        or limits.timeout_seconds <= 0
    ):
        raise SqlFixtureError("timeout_seconds must be finite and positive")
    if limits.timeout_seconds > absolute.timeout_seconds:
        raise SqlFixtureError(
            "timeout_seconds exceeds the absolute sandbox limit"
        )


def grade_sql_query(
    fixture: SqlExerciseFixture | Mapping[str, Any],
    sql: str,
) -> dict[str, Any]:
    """Execute one learner SELECT and compare its result deterministically."""

    if isinstance(fixture, Mapping):
        fixture = fixture_from_mapping(fixture)
    if not isinstance(fixture, SqlExerciseFixture):
        raise TypeError("fixture must be SqlExerciseFixture or a mapping")
    _validate_fixture(fixture)
    if not isinstance(sql, str):
        return _failure("invalid_sql", "提交内容必须是 SQL 文本。")

    limits = fixture.limits
    if not sql.strip():
        return _failure("empty_sql", "请先输入一条只读 SELECT 查询。")
    if "\x00" in sql:
        return _failure("invalid_sql", "SQL 中不能包含空字符。")
    if len(sql) > limits.max_sql_chars:
        return _failure(
            "sql_length_limit",
            f"SQL 超过 {limits.max_sql_chars} 个字符的限制。",
        )

    tokens = _tokenize_sql(sql)
    if not tokens:
        return _failure("empty_sql", "请先输入一条只读 SELECT 查询。")
    first_word = next((token for token in tokens if _is_word(token)), "")
    if first_word not in {"select", "with"}:
        return _failure(
            "sql_not_select",
            "本练习只允许执行单条只读 SELECT 查询。",
        )
    if first_word == "with" and _with_is_explicitly_recursive(tokens):
        return _failure(
            "recursive_query",
            "本练习不允许递归查询，请改用非递归 SELECT。",
        )

    with tempfile.TemporaryDirectory(prefix="ki-sql-learning-") as directory:
        database_path = Path(directory) / "exercise.sqlite3"
        _build_database(database_path, fixture)
        return _execute_and_grade(database_path, fixture, sql, tokens)


def _validate_fixture(fixture: SqlExerciseFixture) -> None:
    limits = fixture.limits
    _validate_absolute_limits(limits)
    integer_limits = {
        "max_sql_chars": limits.max_sql_chars,
        "max_vm_steps": limits.max_vm_steps,
        "progress_ops": limits.progress_ops,
        "max_rows": limits.max_rows,
        "max_columns": limits.max_columns,
        "max_result_bytes": limits.max_result_bytes,
        "max_tables": limits.max_tables,
        "max_seed_rows": limits.max_seed_rows,
    }
    if any(not isinstance(value, int) or value <= 0 for value in integer_limits.values()):
        raise SqlFixtureError("all integer sandbox limits must be positive")
    if limits.progress_ops > limits.max_vm_steps:
        raise SqlFixtureError("progress_ops cannot exceed max_vm_steps")
    if not fixture.tables:
        raise SqlFixtureError("a SQL exercise requires at least one table")
    if len(fixture.tables) > limits.max_tables:
        raise SqlFixtureError("fixture exceeds the table limit")
    if not fixture.expected_columns:
        raise SqlFixtureError("expected_columns cannot be empty")
    if len(fixture.expected_columns) > limits.max_columns:
        raise SqlFixtureError("expected result exceeds the column limit")
    if len(fixture.expected_rows) > limits.max_rows:
        raise SqlFixtureError("expected result exceeds the row limit")
    if any(not isinstance(name, str) or not name.strip() for name in fixture.expected_columns):
        raise SqlFixtureError("expected column names must be non-empty strings")

    seen_tables: set[str] = set()
    columns_by_table: dict[str, set[str]] = {}
    total_rows = 0
    for table in fixture.tables:
        _validate_identifier(table.name, "table")
        folded_table = table.name.casefold()
        if folded_table.startswith("sqlite_") or folded_table in seen_tables:
            raise SqlFixtureError(f"unsafe or duplicate table name: {table.name}")
        seen_tables.add(folded_table)
        if not table.columns:
            raise SqlFixtureError(f"table {table.name} has no columns")
        if len(table.columns) > limits.max_columns:
            raise SqlFixtureError(f"table {table.name} exceeds the column limit")
        seen_columns: set[str] = set()
        for column in table.columns:
            _validate_identifier(column.name, "column")
            folded_column = column.name.casefold()
            if folded_column in seen_columns:
                raise SqlFixtureError(
                    f"table {table.name} has duplicate column {column.name}"
                )
            seen_columns.add(folded_column)
            data_type = column.data_type.strip().upper()
            if data_type not in _ALLOWED_DATA_TYPES:
                raise SqlFixtureError(
                    f"unsupported type {column.data_type} for {table.name}.{column.name}"
                )
        columns_by_table[folded_table] = seen_columns
        total_rows += len(table.rows)
        for row in table.rows:
            if len(row) != len(table.columns):
                raise SqlFixtureError(f"row width does not match table {table.name}")
            for column, value in zip(table.columns, row):
                if value is None and not column.nullable:
                    raise SqlFixtureError(
                        f"NULL is not allowed for {table.name}.{column.name}"
                    )
                if not _is_supported_value(value):
                    raise SqlFixtureError(
                        f"unsupported seed value type in table {table.name}"
                    )
    if total_rows > limits.max_seed_rows:
        raise SqlFixtureError("fixture exceeds the seed row limit")

    for row in fixture.expected_rows:
        if len(row) != len(fixture.expected_columns):
            raise SqlFixtureError("expected row width does not match expected columns")
        if any(not _is_supported_value(value) for value in row):
            raise SqlFixtureError("expected result contains an unsupported value")

    required_tables = {item.casefold() for item in fixture.required_tables}
    if not required_tables.issubset(seen_tables):
        raise SqlFixtureError("required_tables must refer to fixture tables")
    required_clauses = {item.casefold() for item in fixture.required_clauses}
    if not required_clauses.issubset(_ALLOWED_REQUIRED_CLAUSES):
        raise SqlFixtureError("required_clauses contains an unsupported clause")
    required_functions = {item.casefold() for item in fixture.required_functions}
    if not required_functions.issubset(_SAFE_FUNCTIONS):
        raise SqlFixtureError("required_functions contains an unsafe function")
    for field_name, values in (
        ("required_columns", fixture.required_columns),
        ("required_where_columns", fixture.required_where_columns),
        ("required_group_by_columns", fixture.required_group_by_columns),
        ("required_join_columns", fixture.required_join_columns),
    ):
        _validate_required_columns(field_name, values, columns_by_table)


def _validate_required_columns(
    field_name: str,
    values: Iterable[str],
    columns_by_table: Mapping[str, set[str]],
) -> None:
    for value in values:
        parts = str(value).strip().casefold().split(".")
        if len(parts) != 2 or not all(_IDENTIFIER_RE.fullmatch(part) for part in parts):
            raise SqlFixtureError(
                f"{field_name} must contain table.column identifiers"
            )
        table_name, column_name = parts
        if column_name not in columns_by_table.get(table_name, set()):
            raise SqlFixtureError(
                f"{field_name} refers to an unknown fixture column"
            )


def _validate_identifier(value: str, kind: str) -> None:
    if not isinstance(value, str) or not _IDENTIFIER_RE.fullmatch(value):
        raise SqlFixtureError(f"invalid {kind} identifier: {value!r}")


def _is_supported_value(value: Any) -> bool:
    if isinstance(value, float) and not math.isfinite(value):
        return False
    return value is None or isinstance(value, (str, bytes, int, float))


def _quote_identifier(value: str) -> str:
    return f'"{value}"'


def _build_database(path: Path, fixture: SqlExerciseFixture) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute("PRAGMA synchronous=OFF")
        for table in fixture.tables:
            column_sql = []
            for column in table.columns:
                definition = (
                    f"{_quote_identifier(column.name)} "
                    f"{column.data_type.strip().upper()}"
                )
                if not column.nullable:
                    definition += " NOT NULL"
                column_sql.append(definition)
            connection.execute(
                f"CREATE TABLE {_quote_identifier(table.name)} "
                f"({', '.join(column_sql)})"
            )
            if table.rows:
                placeholders = ", ".join("?" for _ in table.columns)
                connection.executemany(
                    f"INSERT INTO {_quote_identifier(table.name)} "
                    f"VALUES ({placeholders})",
                    table.rows,
                )
        connection.commit()
    finally:
        connection.close()


def _read_only_uri(path: Path) -> str:
    normalized = quote(path.resolve().as_posix(), safe="/:")
    return f"file:{normalized}?mode=ro&immutable=1"


def _execute_and_grade(
    path: Path,
    fixture: SqlExerciseFixture,
    sql: str,
    tokens: Sequence[str],
) -> dict[str, Any]:
    limits = fixture.limits
    connection = sqlite3.connect(
        _read_only_uri(path),
        uri=True,
        isolation_level=None,
        timeout=0.05,
    )
    budget = {
        "steps": 0,
        "started": time.monotonic(),
        "reason": "",
    }
    authorization = {
        "denied": "",
        "recursive": False,
        "tables": set(),
        "columns": set(),
        "functions": set(),
    }
    allowed_tables = {
        table.name.casefold(): {
            column.name.casefold()
            for column in table.columns
        }
        for table in fixture.tables
    }
    try:
        try:
            connection.enable_load_extension(False)
        except (AttributeError, sqlite3.Error):
            pass
        _apply_connection_limits(connection, limits)
        connection.execute("PRAGMA query_only=ON")
        connection.execute("PRAGMA temp_store=MEMORY")
        try:
            connection.execute("PRAGMA trusted_schema=OFF")
        except sqlite3.Error:
            pass

        connection.set_authorizer(
            _make_authorizer(authorization, allowed_tables)
        )

        def progress() -> int:
            budget["steps"] += limits.progress_ops
            if budget["steps"] > limits.max_vm_steps:
                budget["reason"] = "steps"
                return 1
            if time.monotonic() - budget["started"] > limits.timeout_seconds:
                budget["reason"] = "timeout"
                return 1
            return 0

        connection.set_progress_handler(progress, limits.progress_ops)
        cursor = connection.cursor()
        try:
            cursor.execute(sql)
        except sqlite3.ProgrammingError as exc:
            if "one statement" in str(exc).casefold():
                return _failure(
                    "multiple_statements",
                    "一次只能提交一条 SELECT 查询，请移除其他语句。",
                )
            return _sql_error(exc, budget, authorization)
        except sqlite3.Error as exc:
            return _sql_error(exc, budget, authorization)

        columns = tuple(
            str(description[0] or "") for description in (cursor.description or ())
        )
        if len(columns) > limits.max_columns:
            return _failure(
                "result_column_limit",
                f"查询返回超过 {limits.max_columns} 列，请缩小结果范围。",
                columns=columns[: limits.max_columns],
                truncated=True,
            )

        rows: list[tuple[Any, ...]] = []
        public_rows: list[list[Any]] = []
        result_bytes = len(
            json.dumps(
                {"columns": list(columns), "rows": []},
                ensure_ascii=False,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        while True:
            try:
                batch = cursor.fetchmany(min(64, limits.max_rows + 1))
            except sqlite3.Error as exc:
                return _sql_error(exc, budget, authorization)
            if not batch:
                break
            for row in batch:
                if len(rows) >= limits.max_rows:
                    return _failure(
                        "result_row_limit",
                        f"查询返回超过 {limits.max_rows} 行，请增加过滤或聚合条件。",
                        columns=columns,
                        rows=public_rows,
                        truncated=True,
                    )
                typed_row = tuple(row)
                public_row = [_public_value(value) for value in typed_row]
                result_bytes += 1 + len(
                    json.dumps(
                        public_row,
                        ensure_ascii=False,
                        separators=(",", ":"),
                    ).encode("utf-8")
                )
                if result_bytes > limits.max_result_bytes:
                    return _failure(
                        "result_size_limit",
                        f"查询结果超过 {limits.max_result_bytes} 字节限制，请缩小结果范围。",
                        columns=columns,
                        rows=public_rows,
                        truncated=True,
                    )
                rows.append(typed_row)
                public_rows.append(public_row)

        used_tables = sorted(authorization["tables"])
        used_columns = sorted(authorization["columns"])
        used_functions = sorted(authorization["functions"])
        semantic_failures = _semantic_failures(
            fixture,
            tokens,
            used_tables,
            used_columns,
            used_functions,
        )
        columns_match = _normalized_columns(columns) == _normalized_columns(
            fixture.expected_columns
        )
        rows_match = _rows_match(
            rows,
            fixture.expected_rows,
            order_sensitive=fixture.order_sensitive,
        )
        differences = {
            "columns_match": columns_match,
            "rows_match": rows_match,
        }
        if columns_match and rows_match and not semantic_failures:
            return {
                "passed": True,
                "score": 1.0,
                "evaluator": "sql_sandbox",
                "error_code": "",
                "feedback": "查询结果和必要语义均正确。",
                "columns": list(columns),
                "rows": public_rows,
                "row_count": len(rows),
                "truncated": False,
                "semantic_failures": [],
                "differences": differences,
                "used_tables": used_tables,
                "used_columns": used_columns,
                "used_functions": used_functions,
            }
        if columns_match and rows_match:
            return _failure(
                "missing_semantics",
                "结果值虽然匹配，但缺少题目要求的查询语义。",
                columns=columns,
                rows=public_rows,
                semantic_failures=semantic_failures,
                differences=differences,
                used_tables=used_tables,
                used_columns=used_columns,
                used_functions=used_functions,
            )
        if not columns_match:
            feedback = "结果列与题目要求不一致，请检查列的数量、顺序或别名。"
        else:
            feedback = "结果行与题目要求不一致，请检查筛选、聚合和重复行。"
        return _failure(
            "wrong_result",
            feedback,
            columns=columns,
            rows=public_rows,
            semantic_failures=semantic_failures,
            differences=differences,
            used_tables=used_tables,
            used_columns=used_columns,
            used_functions=used_functions,
        )
    finally:
        connection.close()


def _apply_connection_limits(
    connection: sqlite3.Connection,
    limits: SqlSandboxLimits,
) -> None:
    setlimit = getattr(connection, "setlimit", None)
    if setlimit is None:
        return
    optional_limits = (
        ("SQLITE_LIMIT_SQL_LENGTH", limits.max_sql_chars),
        ("SQLITE_LIMIT_LENGTH", max(1_024, limits.max_result_bytes)),
        ("SQLITE_LIMIT_COLUMN", max(32, limits.max_columns)),
        ("SQLITE_LIMIT_ATTACHED", 0),
        ("SQLITE_LIMIT_COMPOUND_SELECT", 20),
        ("SQLITE_LIMIT_EXPR_DEPTH", 50),
    )
    for constant_name, value in optional_limits:
        constant = getattr(sqlite3, constant_name, None)
        if constant is not None:
            setlimit(constant, value)


def _make_authorizer(
    state: dict[str, Any],
    allowed_tables: Mapping[str, set[str]],
):
    allowed_actions = {
        getattr(sqlite3, "SQLITE_SELECT", -1),
        getattr(sqlite3, "SQLITE_READ", -2),
        getattr(sqlite3, "SQLITE_FUNCTION", -3),
    }
    read_action = getattr(sqlite3, "SQLITE_READ", -2)
    function_action = getattr(sqlite3, "SQLITE_FUNCTION", -3)
    recursive_action = getattr(sqlite3, "SQLITE_RECURSIVE", -4)

    def authorize(
        action: int,
        argument_one: str | None,
        argument_two: str | None,
        database_name: str | None,
        _trigger_name: str | None,
    ) -> int:
        if action == recursive_action:
            state["recursive"] = True
            state["denied"] = "recursive query"
            return sqlite3.SQLITE_DENY
        if action not in allowed_actions:
            state["denied"] = f"operation {action}"
            return sqlite3.SQLITE_DENY
        if action == read_action:
            table = (argument_one or "").casefold()
            column = (argument_two or "").casefold()
            if (
                table not in allowed_tables
                or (
                    database_name != "main"
                    and not (
                        database_name is None
                        and not column
                    )
                )
                or (
                    column
                    and column not in allowed_tables[table]
                )
            ):
                state["denied"] = f"table {argument_one or ''}".strip()
                return sqlite3.SQLITE_DENY
            state["tables"].add(table)
            state["columns"].add(
                f"{table}.{column}" if column else f"{table}.*"
            )
        elif action == function_action:
            function = (argument_two or argument_one or "").casefold()
            if function not in _SAFE_FUNCTIONS:
                state["denied"] = f"function {function}".strip()
                return sqlite3.SQLITE_DENY
            state["functions"].add(function)
        return sqlite3.SQLITE_OK

    return authorize


def _sql_error(
    exc: sqlite3.Error,
    budget: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> dict[str, Any]:
    message = str(exc)
    folded = message.casefold()
    if budget.get("reason") or "interrupted" in folded:
        return _failure(
            "resource_limit",
            "查询超过执行时间或计算步数限制，请简化查询。",
        )
    if authorization.get("recursive"):
        return _failure(
            "recursive_query",
            "本练习不允许递归查询，请改用非递归 SELECT。",
        )
    if authorization.get("denied"):
        return _failure(
            "sql_forbidden",
            "查询使用了本练习禁止的表、函数或操作。",
        )
    if "one statement" in folded:
        return _failure(
            "multiple_statements",
            "一次只能提交一条 SELECT 查询，请移除其他语句。",
        )
    if "too many columns" in folded:
        return _failure(
            "result_column_limit",
            "查询返回列数超过安全限制，请缩小结果范围。",
        )
    if "string or blob too big" in folded:
        return _failure(
            "result_size_limit",
            "查询结果超过大小限制，请缩小结果范围。",
        )
    concise = message.strip().splitlines()[0][:160] if message.strip() else "未知错误"
    return _failure(
        "sql_syntax",
        f"SQL 语法或名称有误：{concise}",
    )


def _failure(
    error_code: str,
    feedback: str,
    *,
    columns: Iterable[str] = (),
    rows: Sequence[Sequence[Any]] = (),
    truncated: bool = False,
    semantic_failures: Sequence[str] = (),
    differences: Mapping[str, bool] | None = None,
    used_tables: Sequence[str] = (),
    used_columns: Sequence[str] = (),
    used_functions: Sequence[str] = (),
) -> dict[str, Any]:
    public_rows = [
        [_public_value(value) for value in row]
        for row in rows
    ]
    return {
        "passed": False,
        "score": 0.0,
        "evaluator": "sql_sandbox",
        "error_code": error_code,
        "feedback": feedback,
        "columns": list(columns),
        "rows": public_rows,
        "row_count": len(public_rows),
        "truncated": truncated,
        "semantic_failures": list(semantic_failures),
        "differences": dict(
            differences
            or {
                "columns_match": False,
                "rows_match": False,
            }
        ),
        "used_tables": list(used_tables),
        "used_columns": list(used_columns),
        "used_functions": list(used_functions),
    }


def _semantic_failures(
    fixture: SqlExerciseFixture,
    tokens: Sequence[str],
    used_tables: Sequence[str],
    used_columns: Sequence[str],
    used_functions: Sequence[str],
) -> list[str]:
    failures: list[str] = []
    used_table_set = {item.casefold() for item in used_tables}
    used_column_set = {item.casefold() for item in used_columns}
    used_function_set = {item.casefold() for item in used_functions}
    clauses = _clause_set(tokens)
    for table in fixture.required_tables:
        if table.casefold() not in used_table_set:
            failures.append(f"table:{table.casefold()}")
    for clause in fixture.required_clauses:
        normalized = clause.casefold()
        if normalized not in clauses:
            failures.append(normalized)
    for function in fixture.required_functions:
        normalized = function.casefold()
        if normalized not in used_function_set:
            failures.append(f"function:{normalized}")
    for column in fixture.required_columns:
        normalized = column.casefold()
        if normalized not in used_column_set:
            failures.append(f"column:{normalized}")
    clause_columns = {
        "where": _clause_identifier_set(tokens, "where"),
        "group_by": _clause_identifier_set(tokens, "group_by"),
        "join": _clause_identifier_set(tokens, "join"),
    }
    for prefix, values in (
        ("where_column", fixture.required_where_columns),
        ("group_by_column", fixture.required_group_by_columns),
        ("join_column", fixture.required_join_columns),
    ):
        clause_name = {
            "where_column": "where",
            "group_by_column": "group_by",
            "join_column": "join",
        }[prefix]
        identifiers = clause_columns[clause_name]
        for value in values:
            normalized = value.casefold()
            column_name = normalized.rsplit(".", 1)[-1]
            if (
                normalized not in used_column_set
                or column_name not in identifiers
            ):
                failures.append(f"{prefix}:{normalized}")
    return failures


def _clause_identifier_set(
    tokens: Sequence[str],
    clause_name: str,
) -> set[str]:
    start = _clause_start(tokens, clause_name)
    if start < 0:
        return set()
    boundaries = {
        "where",
        "group",
        "having",
        "order",
        "limit",
        "offset",
        "union",
        "intersect",
        "except",
        "returning",
    }
    if clause_name == "join":
        boundaries.add("join")
    identifiers: set[str] = set()
    for token in tokens[start:]:
        if _is_word(token) and token in boundaries:
            break
        if _is_word(token) and token not in _SQL_KEYWORDS:
            identifiers.add(token)
    return identifiers


def _clause_start(tokens: Sequence[str], clause_name: str) -> int:
    if clause_name == "where":
        marker = ("where",)
    elif clause_name == "group_by":
        marker = ("group", "by")
    else:
        marker = ("on",)
    for index in range(0, len(tokens) - len(marker) + 1):
        if tuple(tokens[index : index + len(marker)]) == marker:
            return index + len(marker)
    return -1


def _clause_set(tokens: Sequence[str]) -> set[str]:
    clauses: set[str] = set()
    words = [token for token in tokens if _is_word(token)]
    for index, word in enumerate(words):
        if word in {"where", "join", "having", "distinct"}:
            clauses.add(word)
        if word == "group" and index + 1 < len(words) and words[index + 1] == "by":
            clauses.add("group_by")
        if word == "order" and index + 1 < len(words) and words[index + 1] == "by":
            clauses.add("order_by")
    return clauses


def _normalized_columns(columns: Iterable[str]) -> tuple[str, ...]:
    return tuple(str(column).strip().casefold() for column in columns)


def _rows_match(
    actual: Sequence[Sequence[Any]],
    expected: Sequence[Sequence[Any]],
    *,
    order_sensitive: bool,
) -> bool:
    actual_rows = [tuple(_canonical_value(value) for value in row) for row in actual]
    expected_rows = [
        tuple(_canonical_value(value) for value in row) for row in expected
    ]
    if order_sensitive:
        return actual_rows == expected_rows
    return Counter(actual_rows) == Counter(expected_rows)


def _canonical_value(value: Any) -> tuple[str, str]:
    if value is None:
        return ("null", "")
    if isinstance(value, bytes):
        return ("blob", value.hex())
    if isinstance(value, (bool, int)):
        return ("number", str(int(value)))
    if isinstance(value, float):
        if math.isnan(value):
            return ("number", "nan")
        if math.isinf(value):
            return ("number", "infinity" if value > 0 else "-infinity")
        try:
            decimal = Decimal(str(value))
            normalized = decimal.normalize()
            if normalized == 0:
                normalized = Decimal(0)
            return ("number", format(normalized, "f"))
        except InvalidOperation:
            return ("number", repr(value))
    return ("text", str(value))


def _public_value(value: Any) -> Any:
    if isinstance(value, bytes):
        return {"type": "blob", "hex": value.hex()}
    if isinstance(value, float) and not math.isfinite(value):
        return {
            "type": "number",
            "value": "Infinity" if value > 0 else "-Infinity"
            if value < 0
            else "NaN",
        }
    return value


def _tokenize_sql(sql: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    length = len(sql)
    while index < length:
        character = sql[index]
        if character.isspace():
            index += 1
            continue
        if sql.startswith("--", index):
            newline = sql.find("\n", index + 2)
            index = length if newline == -1 else newline + 1
            continue
        if sql.startswith("/*", index):
            closing = sql.find("*/", index + 2)
            index = length if closing == -1 else closing + 2
            continue
        if character == "'":
            index = _skip_quoted(sql, index, "'", doubled_escape=True)
            tokens.append("<literal>")
            continue
        if character in {'"', "`"}:
            end = _skip_quoted(
                sql,
                index,
                character,
                doubled_escape=True,
            )
            raw_identifier = sql[index + 1 : max(index + 1, end - 1)]
            raw_identifier = raw_identifier.replace(
                character * 2,
                character,
            )
            tokens.append(
                raw_identifier.casefold()
                if _IDENTIFIER_RE.fullmatch(raw_identifier)
                else "<identifier>"
            )
            index = end
            continue
        if character == "[":
            closing = sql.find("]", index + 1)
            if closing == -1:
                tokens.append("<identifier>")
                index = length
                continue
            raw_identifier = sql[index + 1 : closing]
            tokens.append(
                raw_identifier.casefold()
                if _IDENTIFIER_RE.fullmatch(raw_identifier)
                else "<identifier>"
            )
            index = closing + 1
            continue
        match = re.match(r"[A-Za-z_][A-Za-z0-9_$]*", sql[index:])
        if match:
            token = match.group(0)
            tokens.append(token.casefold())
            index += len(token)
            continue
        tokens.append(character)
        index += 1
    return tokens


def _skip_quoted(
    value: str,
    start: int,
    quote_character: str,
    *,
    doubled_escape: bool,
) -> int:
    index = start + 1
    while index < len(value):
        if value[index] == quote_character:
            if (
                doubled_escape
                and index + 1 < len(value)
                and value[index + 1] == quote_character
            ):
                index += 2
                continue
            return index + 1
        index += 1
    return len(value)


def _is_word(token: str) -> bool:
    return bool(re.fullmatch(r"[a-z_][a-z0-9_$]*", token))


def _with_is_explicitly_recursive(tokens: Sequence[str]) -> bool:
    words = [token for token in tokens if _is_word(token)]
    return len(words) >= 2 and words[0] == "with" and words[1] == "recursive"
