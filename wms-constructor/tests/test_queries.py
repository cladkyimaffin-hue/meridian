import datetime as dt
from pathlib import Path

import pytest

from app.queries import QueryError, bind, load_registry, placeholders, validate_sql

DATA = Path(__file__).parent / "data"


@pytest.mark.parametrize("sql", [
    "SELECT 1",
    "select 1;",
    "WITH a AS (SELECT 1 AS x) SELECT * FROM a",
    "SELECT N'Удалить; UPDATE' AS x",           # опасные слова внутри литерала
    "SELECT 1 AS [Delete], 2 AS [Update]",       # внутри [идентификатора]
    "SELECT 1 -- DROP TABLE t",                  # в комментарии
    "SELECT rct_CreateDate FROM dbo.T WITH (NOLOCK)",
    ";WITH occ AS (SELECT 1 AS x) SELECT * FROM occ",   # ведущая ; (идиома T-SQL)
])
def test_validate_ok(sql):
    validate_sql(sql)


@pytest.mark.parametrize("sql", [
    "DELETE FROM dbo.T",
    "UPDATE dbo.T SET a=1",
    "SELECT 1; DROP TABLE t",
    "SELECT 1 -- c\n; SELECT 2",
    "SELECT * INTO #t FROM dbo.T",
    "EXEC sp_who",
    "SELECT * FROM OPENROWSET('x','y','z')",
    "  INSERT INTO t VALUES (1)",
    "",
])
def test_validate_rejects(sql):
    with pytest.raises(QueryError):
        validate_sql(sql)


def test_placeholders_ignore_literals():
    sql = "SELECT 1 WHERE a = :x AND t = '12:30' AND b = :y AND c = :x -- :z"
    assert placeholders(sql) == ["x", "y"]


def test_registry_and_bind():
    reg = load_registry(DATA)
    q = reg.queries["sample.one"]
    sec = reg.section_of(q)
    assert q.params == ["zone", "tovar", "date_from", "date_to"]
    sql, args = bind(q, sec.variables, {
        "zone": ["A", "-"], "tovar": "ab", "date_from": "2026-11-01", "date_to": "2026-11-20"})
    assert "IN (?,?)" in sql
    assert "'12:30; UPDATE'" in sql              # литерал не тронут
    assert args == ["A", "-", "ab", "ab", dt.date(2026, 11, 1), dt.date(2026, 11, 20)]


def test_bind_empty_list_and_bad_date():
    reg = load_registry(DATA)
    q = reg.queries["sample.one"]
    sec = reg.section_of(q)
    sql, args = bind(q, sec.variables, {"zone": [], "tovar": "", "date_from": "2026-11-01", "date_to": "2026-11-02"})
    assert "IN (NULL)" in sql
    with pytest.raises(QueryError):
        bind(q, sec.variables, {"date_from": "не дата"})


def test_load_reports_all_errors(tmp_path):
    (tmp_path / "bad.yaml").write_text(
        "section: s\nqueries:\n"
        "  - {id: a, title: A, sql: 'DELETE FROM t'}\n"
        "  - {id: b, title: B, sql: 'SELECT :nope'}\n", encoding="utf-8")
    with pytest.raises(QueryError) as e:
        load_registry(tmp_path)
    assert "запрос a" in str(e.value) and "запрос b" in str(e.value)


def test_relative_date_default():
    from app.queries import Variable, resolve_default
    v = Variable("date_from", "С даты", "date", default="-90d")
    assert resolve_default(v) == (dt.date.today() - dt.timedelta(days=90)).isoformat()
    assert resolve_default(Variable("date_to", "По", "date")) == dt.date.today().isoformat()
