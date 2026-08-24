def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_list_leads_returns_seed_data(client):
    resp = client.get("/api/leads")
    assert resp.status_code == 200
    names = {lead["name"] for lead in resp.json()}
    assert names == {"Test Foundation", "Test Community Org"}


def test_list_leads_filters_by_category(client):
    resp = client.get("/api/leads", params={"category": "funder"})
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 1
    assert leads[0]["name"] == "Test Foundation"


def test_list_leads_search_matches_focus_area(client):
    resp = client.get("/api/leads", params={"q": "youth"})
    assert resp.status_code == 200
    leads = resp.json()
    assert len(leads) == 1
    assert leads[0]["name"] == "Test Community Org"


def test_list_leads_search_is_case_insensitive(client):
    resp = client.get("/api/leads", params={"q": "FOOD ACCESS"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1


def test_get_lead_by_id(client):
    lead_id = client.get("/api/leads").json()[0]["id"]
    resp = client.get(f"/api/leads/{lead_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == lead_id


def test_get_lead_missing_returns_404(client):
    resp = client.get("/api/leads/999999")
    assert resp.status_code == 404


def test_patch_status_updates_and_persists(client):
    lead_id = client.get("/api/leads", params={"category": "partner"}).json()[0]["id"]

    resp = client.patch(f"/api/leads/{lead_id}", json={"status": "contacted"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "contacted"

    # confirm it actually persisted, not just echoed back
    refetched = client.get(f"/api/leads/{lead_id}").json()
    assert refetched["status"] == "contacted"


def test_patch_status_rejects_unknown_value(client):
    lead_id = client.get("/api/leads").json()[0]["id"]
    resp = client.patch(f"/api/leads/{lead_id}", json={"status": "not-a-real-status"})
    assert resp.status_code == 422


def test_patch_missing_lead_returns_404(client):
    resp = client.patch("/api/leads/999999", json={"status": "contacted"})
    assert resp.status_code == 404


def test_stats(client):
    resp = client.get("/api/stats")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert body["funders"] == 1
    assert body["partners"] == 1
    assert body["by_status"] == {"drafted": 1, "new": 1}
