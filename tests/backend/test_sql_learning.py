from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

import backend.domain.sql_learning as sql_learning
from backend.domain.sql_learning import (
    SqlColumn,
    SqlExerciseFixture,
    SqlFixtureError,
    SqlSandboxLimits,
    SqlTable,
    fixture_from_mapping,
    grade_sql_query,
    fixture_from_mapping,
)


def _people_fixture(
    *,
    order_sensitive: bool = False,
    limits: SqlSandboxLimits | None = None,
) -> SqlExerciseFixture:
    return SqlExerciseFixture(
        tables=(
            SqlTable(
                name="people",
                columns=(
                    SqlColumn("id", "INTEGER", nullable=False),
                    SqlColumn("name", "TEXT", nullable=False),
                    SqlColumn("team", "TEXT", nullable=False),
                    SqlColumn("score", "REAL"),
                ),
                rows=(
                    (1, "Ada", "core", 9.5),
                    (2, "Bob", "core", None),
                    (3, "Ada", "core", 7.0),
                    (4, "Chen", "web", 8.0),
                ),
            ),
        ),
        expected_columns=("name",),
        expected_rows=(("Ada",), ("Bob",), ("Ada",)),
        order_sensitive=order_sensitive,
        required_tables=("people",),
        required_clauses=("where",),
        required_where_columns=("people.team",),
        limits=limits or SqlSandboxLimits(),
    )


def _people_mapping() -> dict[str, object]:
    return {
        "schema": [
            {
                "name": "people",
                "columns": [
                    {"name": "id", "type": "INTEGER", "nullable": False},
                    {"name": "name", "type": "TEXT", "nullable": False},
                    {"name": "team", "type": "TEXT", "nullable": False},
                ],
            }
        ],
        "seed_rows": {
            "people": [
                {"id": 1, "name": "Ada", "team": "core"},
                {"id": 2, "name": "Bob", "team": "core"},
                {"id": 3, "name": "Ada", "team": "core"},
                {"id": 4, "name": "Chen", "team": "web"},
            ]
        },
        "expected_columns": ["name"],
        "expected_rows": [["Ada"], ["Bob"], ["Ada"]],
        "order_sensitive": False,
        "required_semantics": {
            "tables": ["people"],
            "clauses": ["where"],
            "where_columns": ["people.team"],
        },
        "limits": {},
    }


def test_correct_equivalent_and_wrong_queries_are_scored_deterministically():
    fixture = _people_fixture()

    direct = grade_sql_query(
        fixture,
        "SELECT name FROM people WHERE team = 'core'",
    )
    equivalent = grade_sql_query(
        fixture,
        """
        WITH filtered AS (
            SELECT name, id FROM people WHERE team IN ('core')
        )
        SELECT name FROM filtered ORDER BY id DESC
        """,
    )
    wrong = grade_sql_query(
        fixture,
        "SELECT name FROM people WHERE team = 'web'",
    )

    assert direct["passed"] is True
    assert direct["score"] == 1.0
    assert equivalent["passed"] is True
    assert equivalent["score"] == 1.0
    assert wrong["passed"] is False
    assert wrong["score"] == 0.0
    assert wrong["error_code"] == "wrong_result"
    assert "结果行" in wrong["feedback"]


def test_order_is_only_compared_when_the_exercise_requires_it():
    unordered = grade_sql_query(
        _people_fixture(order_sensitive=False),
        "SELECT name FROM people WHERE team = 'core' ORDER BY name DESC",
    )
    ordered = grade_sql_query(
        _people_fixture(order_sensitive=True),
        "SELECT name FROM people WHERE team = 'core' ORDER BY name DESC",
    )

    assert unordered["passed"] is True
    assert ordered["passed"] is False
    assert ordered["differences"]["rows_match"] is False


def test_null_empty_results_and_duplicate_rows_are_preserved():
    null_fixture = SqlExerciseFixture(
        tables=_people_fixture().tables,
        expected_columns=("name",),
        expected_rows=(("Bob",),),
        required_tables=("people",),
        required_clauses=("where",),
    )
    empty_fixture = SqlExerciseFixture(
        tables=_people_fixture().tables,
        expected_columns=("name",),
        expected_rows=(),
        required_tables=("people",),
        required_clauses=("where",),
    )
    duplicate_fixture = _people_fixture()

    null_result = grade_sql_query(
        null_fixture,
        "SELECT name FROM people WHERE score IS NULL",
    )
    empty_result = grade_sql_query(
        empty_fixture,
        "SELECT name FROM people WHERE score < 0",
    )
    missing_duplicate = grade_sql_query(
        duplicate_fixture,
        "SELECT DISTINCT name FROM people WHERE team = 'core'",
    )

    assert null_result["passed"] is True
    assert null_result["rows"] == [["Bob"]]
    assert empty_result["passed"] is True
    assert empty_result["rows"] == []
    assert missing_duplicate["passed"] is False


def test_aggregate_and_join_semantics_are_required():
    fixture = SqlExerciseFixture(
        tables=(
            SqlTable(
                name="teams",
                columns=(
                    SqlColumn("id", "INTEGER", nullable=False),
                    SqlColumn("name", "TEXT", nullable=False),
                ),
                rows=((1, "core"), (2, "web")),
            ),
            SqlTable(
                name="work_items",
                columns=(
                    SqlColumn("team_id", "INTEGER", nullable=False),
                    SqlColumn("points", "INTEGER", nullable=False),
                ),
                rows=((1, 2), (1, 3), (2, 7)),
            ),
        ),
        expected_columns=("team", "total_points"),
        expected_rows=(("core", 5), ("web", 7)),
        order_sensitive=False,
        required_tables=("teams", "work_items"),
        required_clauses=("join", "group_by"),
        required_functions=("sum",),
        required_group_by_columns=("teams.name",),
        required_join_columns=("teams.id", "work_items.team_id"),
    )

    correct = grade_sql_query(
        fixture,
        """
        SELECT t.name AS team, SUM(w.points) AS total_points
        FROM teams AS t
        JOIN work_items AS w ON w.team_id = t.id
        GROUP BY t.name
        """,
    )
    coincidental_without_join = grade_sql_query(
        fixture,
        """
        SELECT 'core' AS team, 5 AS total_points
        UNION ALL
        SELECT 'web', 7
        """,
    )

    assert correct["passed"] is True
    assert correct["used_tables"] == ["teams", "work_items"]
    assert "sum" in correct["used_functions"]
    assert coincidental_without_join["passed"] is False
    assert coincidental_without_join["error_code"] == "missing_semantics"
    assert "join" in coincidental_without_join["semantic_failures"]


def test_count_star_reads_only_the_known_fixture_table():
    fixture = SqlExerciseFixture(
        tables=_people_fixture().tables,
        expected_columns=("count",),
        expected_rows=((4,),),
        required_tables=("people",),
        required_functions=("count",),
    )

    result = grade_sql_query(fixture, "SELECT COUNT(*) AS count FROM people")

    assert result["passed"] is True
    assert result["used_tables"] == ["people"]


def test_syntax_errors_return_learner_friendly_feedback():
    result = grade_sql_query(
        _people_fixture(),
        "SELECT name FORM people WHERE team = 'core'",
    )

    assert result["passed"] is False
    assert result["score"] == 0.0
    assert result["error_code"] == "sql_syntax"
    assert "语法" in result["feedback"]


@pytest.mark.parametrize(
    ("sql", "expected_code"),
    (
        ("SELECT 1; SELECT 2", "multiple_statements"),
        ("PRAGMA table_info(people)", "sql_not_select"),
        ("ATTACH DATABASE 'other.db' AS other", "sql_not_select"),
        ("INSERT INTO people VALUES (5, 'Dan', 'core', 1)", "sql_not_select"),
        ("UPDATE people SET score = 10", "sql_not_select"),
        ("DELETE FROM people", "sql_not_select"),
        ("DROP TABLE people", "sql_not_select"),
        ("SELECT load_extension('unsafe')", "sql_forbidden"),
        ("SELECT random()", "sql_forbidden"),
        ("SELECT date('now')", "sql_forbidden"),
        ("SELECT zeroblob(1024)", "sql_forbidden"),
        ("SELECT name FROM sqlite_master", "sql_forbidden"),
    ),
)
def test_multiple_statements_and_unsafe_operations_are_rejected(sql, expected_code):
    result = grade_sql_query(_people_fixture(), sql)

    assert result["passed"] is False
    assert result["score"] == 0.0
    assert result["error_code"] == expected_code


def test_recursive_queries_and_vm_budget_exhaustion_are_stopped():
    recursive = grade_sql_query(
        _people_fixture(),
        """
        WITH RECURSIVE counter(value) AS (
            SELECT 1
            UNION ALL
            SELECT value + 1 FROM counter WHERE value < 10
        )
        SELECT value AS name FROM counter WHERE value > 0
        """,
    )
    limited_fixture = SqlExerciseFixture(
        tables=(
            SqlTable(
                name="numbers",
                columns=(SqlColumn("value", "INTEGER", nullable=False),),
                rows=tuple((value,) for value in range(40)),
            ),
        ),
        expected_columns=("total",),
        expected_rows=((0,),),
        required_tables=("numbers",),
        required_functions=("sum",),
        limits=SqlSandboxLimits(
            timeout_seconds=1.0,
            max_vm_steps=2_000,
            progress_ops=100,
        ),
    )
    exhausted = grade_sql_query(
        limited_fixture,
        """
        SELECT SUM(a.value * b.value * c.value * d.value) AS total
        FROM numbers a
        CROSS JOIN numbers b
        CROSS JOIN numbers c
        CROSS JOIN numbers d
        """,
    )

    assert recursive["passed"] is False
    assert recursive["error_code"] == "recursive_query"
    assert exhausted["passed"] is False
    assert exhausted["error_code"] == "resource_limit"
    assert "限制" in exhausted["feedback"]


def test_wall_clock_timeout_is_enforced_independently_of_the_vm_budget(monkeypatch):
    clock = iter((0.0, 0.02, 0.04, 0.06))
    monkeypatch.setattr(sql_learning.time, "monotonic", lambda: next(clock))
    fixture = SqlExerciseFixture(
        tables=(
            SqlTable(
                name="numbers",
                columns=(SqlColumn("value", "INTEGER", nullable=False),),
                rows=tuple((value,) for value in range(20)),
            ),
        ),
        expected_columns=("total",),
        expected_rows=((0,),),
        limits=SqlSandboxLimits(
            timeout_seconds=0.01,
            max_vm_steps=1_000_000,
            progress_ops=1,
        ),
    )

    timed_out = grade_sql_query(
        fixture,
        """
        SELECT SUM(a.value * b.value * c.value) AS total
        FROM numbers a
        CROSS JOIN numbers b
        CROSS JOIN numbers c
        """,
    )

    assert timed_out["passed"] is False
    assert timed_out["error_code"] == "resource_limit"


def test_result_row_column_and_byte_limits_are_enforced():
    rows_fixture = SqlExerciseFixture(
        tables=_people_fixture().tables,
        expected_columns=("id",),
        expected_rows=((1,),),
        limits=SqlSandboxLimits(max_rows=2),
    )
    columns_fixture = SqlExerciseFixture(
        tables=(
            SqlTable(
                name="pairs",
                columns=(
                    SqlColumn("id", "INTEGER", nullable=False),
                    SqlColumn("name", "TEXT", nullable=False),
                ),
                rows=((1, "Ada"),),
            ),
        ),
        expected_columns=("id",),
        expected_rows=((1,),),
        limits=SqlSandboxLimits(max_columns=2),
    )
    bytes_fixture = SqlExerciseFixture(
        tables=(
            SqlTable(
                name="messages",
                columns=(SqlColumn("body", "TEXT", nullable=False),),
                rows=(("x" * 120,),),
            ),
        ),
        expected_columns=("body",),
        expected_rows=(("x" * 120,),),
        limits=SqlSandboxLimits(max_result_bytes=64),
    )

    too_many_rows = grade_sql_query(rows_fixture, "SELECT id FROM people")
    too_many_columns = grade_sql_query(
        columns_fixture,
        "SELECT id, name, id AS repeated_id FROM pairs",
    )
    too_many_bytes = grade_sql_query(bytes_fixture, "SELECT body FROM messages")

    assert too_many_rows["error_code"] == "result_row_limit"
    assert too_many_columns["error_code"] == "result_column_limit"
    assert too_many_bytes["error_code"] == "result_size_limit"


def test_sandbox_never_connects_to_or_changes_an_application_database(tmp_path):
    application_db = tmp_path / "app.db"
    connection = sqlite3.connect(application_db)
    connection.execute("CREATE TABLE sentinel (value TEXT NOT NULL)")
    connection.execute("INSERT INTO sentinel VALUES ('keep-me')")
    connection.commit()
    connection.close()
    before = hashlib.sha256(application_db.read_bytes()).hexdigest()

    result = grade_sql_query(
        _people_fixture(),
        f"ATTACH DATABASE '{application_db.as_posix()}' AS application",
    )

    after = hashlib.sha256(application_db.read_bytes()).hexdigest()
    connection = sqlite3.connect(application_db)
    value = connection.execute("SELECT value FROM sentinel").fetchone()[0]
    connection.close()

    assert result["passed"] is False
    assert result["error_code"] == "sql_not_select"
    assert after == before
    assert value == "keep-me"


@pytest.mark.parametrize(
    "table",
    (
        SqlTable(
            name='people"; DROP TABLE people; --',
            columns=(SqlColumn("id", "INTEGER"),),
        ),
        SqlTable(
            name="people",
            columns=(SqlColumn("unsafe name", "TEXT"),),
        ),
        SqlTable(
            name="people",
            columns=(SqlColumn("id", "INTEGER PRIMARY KEY"),),
        ),
    ),
)
def test_fixture_schema_accepts_only_validated_identifiers_and_types(table):
    fixture = SqlExerciseFixture(
        tables=(table,),
        expected_columns=("id",),
        expected_rows=(),
    )

    with pytest.raises(SqlFixtureError):
        grade_sql_query(fixture, "SELECT id FROM people")


@pytest.mark.parametrize(
    "sql",
    (
        "SELECT name AS x FROM pragma_table_info('people') WHERE 0",
        "SELECT value AS x FROM json_each('[1]') WHERE 0",
        "SELECT name AS x FROM pragma_database_list WHERE 0",
    ),
)
def test_table_valued_pragmas_and_virtual_tables_are_not_fixture_tables(sql):
    fixture = SqlExerciseFixture(
        tables=_people_fixture().tables,
        expected_columns=("x",),
        expected_rows=(),
    )

    result = grade_sql_query(fixture, sql)

    assert result["passed"] is False
    assert result["error_code"] == "sql_forbidden"


def test_hard_coded_rows_cannot_fake_a_required_filter_semantic():
    fixture = _people_mapping()

    result = grade_sql_query(
        fixture,
        """
        WITH answer(name) AS (VALUES ('Ada'), ('Bob'), ('Ada'))
        SELECT answer.name
        FROM answer
        CROSS JOIN people
        WHERE people.id = 1
        """,
    )

    assert result["passed"] is False
    assert result["error_code"] == "missing_semantics"
    assert "where_column:people.team" in result["semantic_failures"]


def test_quoted_required_filter_identifier_remains_valid():
    result = grade_sql_query(
        _people_mapping(),
        "SELECT name FROM people WHERE \"team\" = 'core'",
    )

    assert result["passed"] is True


def test_persisted_fixture_limits_cannot_exceed_absolute_sandbox_caps():
    fixture = _people_mapping()
    fixture["limits"] = {"max_rows": 10_000}

    with pytest.raises(SqlFixtureError, match="absolute sandbox limit"):
        fixture_from_mapping(fixture)


@pytest.mark.parametrize(
    "limits",
    (
        SqlSandboxLimits(max_rows=201),
        SqlSandboxLimits(timeout_seconds=float("nan")),
        SqlSandboxLimits(timeout_seconds=float("inf")),
    ),
)
def test_typed_fixture_cannot_bypass_absolute_sandbox_caps(limits):
    fixture = _people_fixture(limits=limits)

    with pytest.raises(SqlFixtureError):
        grade_sql_query(fixture, "SELECT name FROM people WHERE team = 'core'")


def test_persisted_fixture_hash_is_verified_when_present():
    fixture = _people_mapping()
    raw = json.dumps(
        fixture,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    fixture["fixture_hash"] = hashlib.sha256(raw).hexdigest()
    fixture["expected_rows"] = [["tampered"]]

    with pytest.raises(SqlFixtureError, match="fixture_hash"):
        fixture_from_mapping(fixture)


def test_persisted_fixture_shape_is_converted_by_schema_column_order():
    fixture = fixture_from_mapping(
        {
            "schema": [
                {
                    "name": "people",
                    "columns": [
                        {"name": "id", "type": "INTEGER", "nullable": False},
                        {"name": "name", "data_type": "TEXT", "nullable": False},
                    ],
                }
            ],
            "seed_rows": {
                "people": [
                    {"name": "Ada", "id": 1},
                    {"name": "Bob", "id": 2},
                ]
            },
            "expected_columns": ["name"],
            "expected_rows": [["Ada"]],
            "order_sensitive": False,
            "required_semantics": {
                "tables": ["people"],
                "clauses": ["where"],
                "functions": [],
            },
            "limits": {"max_rows": 10, "max_bytes": 4_096},
        }
    )

    result = grade_sql_query(
        fixture,
        "SELECT name FROM people WHERE id = 1",
    )

    assert fixture.tables[0].rows == ((1, "Ada"), (2, "Bob"))
    assert fixture.limits.max_result_bytes == 4_096
    assert result["passed"] is True
