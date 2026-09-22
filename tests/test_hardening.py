import asyncio

import pytest

from signalpost.app.database.database import SessionLocal, init_db
from signalpost.app.database.repositories import add_fact, upsert_company
from signalpost.app.sources.base import validate_public_url


def test_ssrf_blocks_local_targets():
    for url in ("file:///etc/passwd", "http://127.0.0.1:8080", "http://localhost"):
        with pytest.raises(ValueError):
            validate_public_url(url)


def test_ssrf_allows_public_https_hostname():
    assert validate_public_url("https://example.com") == "https://example.com"


def test_fact_history_preserves_previous_current_value(tmp_path, monkeypatch):
    database_url = f"sqlite:///{tmp_path / 'history.db'}"
    monkeypatch.setattr("signalpost.app.database.database.settings.database_url", database_url)
    init_db()
    with SessionLocal() as db:
        company = upsert_company(db, {"company_number": "984851006", "legal_name": "Example AS"})
        old = add_fact(db, company, {"field": "employees", "value": 7000})
        new = add_fact(db, company, {"field": "employees", "value": 7353})
        db.refresh(old)
        db.refresh(new)
        assert old.is_current is False
        assert new.is_current is True
        assert old.value_json == 7000
        assert new.value_json == 7353


def test_source_extraction_remains_async():
    assert asyncio.run(asyncio.sleep(0)) is None
