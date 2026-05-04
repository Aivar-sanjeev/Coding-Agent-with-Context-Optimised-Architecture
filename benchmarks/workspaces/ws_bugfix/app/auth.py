"""Token validation (case-sensitive bearer)."""


def validate(headers: dict[str, str]) -> bool:
    auth = headers.get("Authorization", "")
    return auth == "Bearer SecretToken"
