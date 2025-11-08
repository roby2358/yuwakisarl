from fastapi.testclient import TestClient

from app.main import create_app


def test_index_serves_html():
    app = create_app()
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "<!DOCTYPE html>" in response.text

