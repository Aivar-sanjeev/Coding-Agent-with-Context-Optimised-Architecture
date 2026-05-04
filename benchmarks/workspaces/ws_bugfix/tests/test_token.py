from app.router import handle


def test_ping_requires_valid_bearer_case_sensitive():
    assert handle("/api/ping", {"Authorization": "Bearer SecretToken"}) == 200
