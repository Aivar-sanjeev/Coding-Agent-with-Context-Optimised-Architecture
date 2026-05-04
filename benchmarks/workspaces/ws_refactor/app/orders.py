"""Order processing (monolithic until refactored)."""


def process_order(raw: dict) -> dict:
    if not isinstance(raw, dict):
        raise TypeError("raw must be dict")
    items = raw.get("items") or []
    if not isinstance(items, list) or not items:
        raise ValueError("items required")
    currency = str(raw.get("currency") or "USD")
    subtotal = 0.0
    normalized = []
    for it in items:
        qty = int(it.get("qty", 1))
        price = float(it.get("price", 0.0))
        name = str(it.get("name", "item"))
        line = round(qty * price, 2)
        subtotal += line
        normalized.append({"name": name, "qty": qty, "price": price, "line_total": line})
    discount_pct = float(raw.get("discount_pct") or 0.0)
    if discount_pct < 0 or discount_pct > 0.5:
        raise ValueError("invalid discount")
    discount = round(subtotal * discount_pct, 2)
    taxable = round(subtotal - discount, 2)
    tax_rate = float(raw.get("tax_rate") or 0.0)
    if tax_rate < 0 or tax_rate > 0.25:
        raise ValueError("invalid tax_rate")
    tax = round(taxable * tax_rate, 2)
    total = round(taxable + tax, 2)
    return {
        "currency": currency,
        "items": normalized,
        "subtotal": round(subtotal, 2),
        "discount": discount,
        "tax": tax,
        "total": total,
    }
