from app.router import handle


def test_health_ok():
    status, body = handle("/health", {})
    assert status == 200
    assert "ok" in body.lower()
