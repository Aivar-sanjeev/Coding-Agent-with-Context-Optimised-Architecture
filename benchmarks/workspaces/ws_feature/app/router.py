"""Router without /health (agent must add it)."""


def handle(path: str, headers: dict[str, str]) -> tuple[int, str]:  # noqa: ARG001
    if path == "/api/ping":
        return 200, "pong"
    return 404, "not found"
