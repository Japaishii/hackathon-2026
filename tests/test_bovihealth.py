from fastapi.testclient import TestClient
from app.main import app

def test_brand_and_no_sidebar():
    with TestClient(app) as client:
        html = client.get("/").text
        assert "BoviHealth" in html
        assert '<aside class="app-sidebar"' not in html
        assert 'id="productive_state"' in html

def test_reject_prepartum_lactating():
    with TestClient(app) as client:
        response = client.post("/api/animals", json={"identifier":"TEST-PREPARTO", "productive_state":"lactating", "transition_stage":"prepartum"})
        assert response.status_code == 422
