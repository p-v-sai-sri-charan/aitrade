import uuid


def test_kill_switch_blocks_new_orders(client):
    settings_resp = client.get("/api/v1/settings").json()
    settings_resp["tradingKillSwitch"] = True
    update = client.put("/api/v1/settings", json={"tradingKillSwitch": True})
    assert update.status_code == 200
    assert update.json()["tradingKillSwitch"] is True

    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "exchange": "NSE",
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 1,
            "orderType": "MARKET",
            "product": "DELIVERY",
            "validity": "DAY",
        },
    ).json()
    assert preview["riskCheck"]["allowed"] is False
    assert preview["riskCheck"]["code"] == "TRADING_KILL_SWITCH_ACTIVE"


def test_updating_risk_limits_is_enforced(client):
    client.put(
        "/api/v1/settings",
        json={
            "riskLimits": {
                "maxOrderValue": 1000,
                "maxQuantity": 5000,
                "maxPriceDeviationPct": 5,
                "dailyLossLimit": 25000,
            }
        },
    )
    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "exchange": "NSE",
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 5,
            "orderType": "MARKET",
            "product": "DELIVERY",
            "validity": "DAY",
        },
    ).json()
    assert preview["riskCheck"]["allowed"] is False
    assert preview["riskCheck"]["code"] == "ORDER_VALUE_LIMIT_EXCEEDED"


def test_reset_paper_trading_restores_balance(client):
    preview = client.post(
        "/api/v1/orders/preview",
        json={
            "exchange": "NSE",
            "symbol": "RELIANCE",
            "side": "BUY",
            "quantity": 5,
            "orderType": "MARKET",
            "product": "DELIVERY",
            "validity": "DAY",
        },
    ).json()
    client.post(
        "/api/v1/orders/confirm",
        json={"previewId": preview["previewId"], "idempotencyKey": str(uuid.uuid4())},
    )

    portfolio_before = client.get("/api/v1/portfolio").json()
    assert len(portfolio_before["positions"]) == 1

    client.post("/api/v1/settings/reset-paper-trading")

    portfolio_after = client.get("/api/v1/portfolio").json()
    assert portfolio_after["positions"] == []
    orders_after = client.get("/api/v1/orders").json()
    assert orders_after == []
