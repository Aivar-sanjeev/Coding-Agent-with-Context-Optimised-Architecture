import pytest

from app.orders import process_order


def test_happy_path():
    out = process_order(
        {
            "currency": "USD",
            "items": [
                {"name": "a", "qty": 2, "price": 10},
                {"name": "b", "qty": 1, "price": 5},
            ],
            "discount_pct": 0.1,
            "tax_rate": 0.2,
        }
    )
    assert out["currency"] == "USD"
    assert out["subtotal"] == 25.0
    assert out["discount"] == 2.5
    assert out["tax"] == 4.5
    assert out["total"] == 27.0
    assert len(out["items"]) == 2


def test_validation():
    with pytest.raises(ValueError):
        process_order({"items": []})
