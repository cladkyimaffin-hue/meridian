from dataclasses import replace
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import load_settings
from app.main import create_app

DATA = Path(__file__).parent / "data"


def client():
    return TestClient(create_app(replace(load_settings(), queries_dir=str(DATA))))


def test_health_and_menu():
    c = client()
    assert c.get("/healthz").json() == {"status": "ok", "queries": 1}
    menu = c.get("/api/menu").json()
    assert menu[0]["groups"][0]["queries"][0]["id"] == "sample.one"


def test_meta_and_options_and_404():
    c = client()
    meta = c.get("/api/queries/sample.one").json()
    assert [v["name"] for v in meta["variables"]] == ["zone", "tovar", "date_from", "date_to"]
    assert c.get("/api/queries/sample.one/options/zone").json()[0]["value"] == "A"
    assert c.get("/api/queries/нет").status_code == 404


def test_run_without_db_credentials_is_clean_error():
    r = client().post("/api/queries/sample.one/run", json={"params": {}})
    assert r.status_code == 400 and "MSSQL_HOST" in r.json()["error"]
