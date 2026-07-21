import uuid


def _preview_market_buy(client, symbol="RELIANCE", quantity=5):
    return client.post(
        "/api/v1/orders/preview",
        json={
            "exchange": "NSE",
            "symbol": symbol,
            "side": "BUY",
            "quantity": quantity,
            "orderType": "MARKET",
            "product": "DELIVERY",
            "validity": "DAY",
        },
    )


def test_preview_then_confirm_places_order(client):
    preview_resp = _preview_market_buy(client)
    assert preview_resp.status_code == 200
    preview = preview_resp.json()
    assert preview["riskCheck"]["allowed"] is True

    confirm_resp = client.post(
        "/api/v1/orders/confirm",
        json={"previewId": preview["previewId"], "idempotencyKey": str(uuid.uuid4())},
    )
    assert confirm_resp.status_code == 200
    order = confirm_resp.json()
    assert order["status"] == "FILLED"
    assert order["symbol"] == "RELIANCE"
    assert order["side"] == "BUY"
    assert order["quantity"] == 5

    positions = client.get("/api/v1/positions").json()
    assert any(p["symbol"] == "RELIANCE" and p["quantity"] == 5 for p in positions)


def test_confirm_is_idempotent(client):
    preview = _preview_market_buy(client).json()
    idempotency_key = str(uuid.uuid4())

    first = client.post(
        "/api/v1/orders/confirm",
        json={"previewId": preview["previewId"], "idempotencyKey": idempotency_key},
    ).json()
    second = client.post(
        "/api/v1/orders/confirm",
        json={"previewId": preview["previewId"], "idempotencyKey": idempotency_key},
    ).json()

    assert first["id"] == second["id"]

    positions = client.get("/api/v1/positions").json()
    reliance = next(p for p in positions if p["symbol"] == "RELIANCE")
    assert reliance["quantity"] == 5  # not doubled


def test_confirm_with_unknown_preview_id_returns_404(client):
    response = client.post(
        "/api/v1/orders/confirm",
        json={"previewId": str(uuid.uuid4()), "idempotencyKey": str(uuid.uuid4())},
    )
    assert response.status_code == 404


def test_order_value_over_limit_is_rejected_at_preview(client):
    response = _preview_market_buy(client, symbol="MARUTI", quantity=1000)
    assert response.status_code == 200
    risk_check = response.json()["riskCheck"]
    assert risk_check["allowed"] is False
    assert risk_check["code"] == "ORDER_VALUE_LIMIT_EXCEEDED"


def test_cancel_pending_limit_order(client):
    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "exchange": "NSE",
            "symbol": "TCS",
            "side": "BUY",
            "quantity": 1,
            "orderType": "LIMIT",
            "limitPrice": 3700,  # a few % below TCS's seeded market price -> stays pending, still within allowed deviation
            "product": "DELIVERY",
            "validity": "DAY",
        },
    ).json()
    order = client.post(
        "/api/v1/orders/confirm",
        json={"previewId": preview["previewId"], "idempotencyKey": str(uuid.uuid4())},
    ).json()
    assert order["status"] == "PENDING"

    cancel_resp = client.post(f"/api/v1/orders/{order['id']}/cancel")
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] == "CANCELLED"


def test_cancel_unknown_order_404s(client):
    response = client.post(f"/api/v1/orders/{uuid.uuid4()}/cancel")
    assert response.status_code == 404


def test_ambiguous_symbol_rejected_at_preview(client):
    response = _preview_market_buy(client, symbol="Tata", quantity=1)
    assert response.status_code == 200
    risk_check = response.json()["riskCheck"]
    assert risk_check["allowed"] is False
    assert risk_check["code"] == "AMBIGUOUS_SYMBOL"
