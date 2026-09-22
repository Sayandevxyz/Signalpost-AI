from fastapi.testclient import TestClient

from signalpost.app.main import app


client = TestClient(app)


def test_health_and_root():
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/").status_code == 200


def test_research_and_lookup_are_deterministic():
    response = client.post("/research", json={"company_number": "912 345 678"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["company"]["company_number"] == "912345678"
    assert payload["research"]["status"] in {"complete", "partial"}
    assert isinstance(payload["facts"], list)
    assert all(fact["evidence"] for fact in payload["facts"])

    run_id = payload["research"]["run_id"]
    assert client.get(f"/research/{run_id}").status_code == 200
    assert client.get("/companies/912345678").status_code == 200


def test_invalid_company_number_is_rejected():
    assert client.post("/research", json={"company_number": "123"}).status_code == 422
    assert client.get("/research/does-not-exist").status_code == 404
