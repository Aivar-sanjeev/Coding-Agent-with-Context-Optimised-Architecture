"""Request shaping (intentionally buggy for benchmark)."""


def apply(headers: dict[str, str]) -> dict[str, str]:
    """
    Enrich headers before auth.

    Bug: lowercases Authorization, which breaks case-sensitive bearer tokens.
    """
    h = dict(headers)
    if "Authorization" in h:
        h["Authorization"] = h["Authorization"].lower()
    return h
