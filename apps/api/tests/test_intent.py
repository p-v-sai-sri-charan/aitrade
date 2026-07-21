def test_parse_hinglish_limit_buy(client):
    response = client.post(
        "/api/v1/intent/parse",
        json={"transcript": "Reliance ke 10 shares 2950 limit price par buy karo."},
    )
    assert response.status_code == 200
    data = response.json()
    intent = data["intent"]
    assert intent["intent"] == "PLACE_ORDER"
    assert intent["symbol"] == "RELIANCE"
    assert intent["side"] == "BUY"
    assert intent["quantity"] == 10
    assert intent["orderType"] == "LIMIT"
    assert intent["limitPrice"] == 2950
    assert intent["missingFields"] == []
    assert data["provider"] == "mock"


def test_parse_ambiguous_company_name_requires_disambiguation(client):
    response = client.post(
        "/api/v1/intent/parse",
        json={"transcript": "Tata ka share buy karo 5 shares"},
    )
    assert response.status_code == 200
    intent = response.json()["intent"]
    assert intent["intent"] == "PLACE_ORDER"
    assert len(intent["ambiguousSymbolCandidates"]) > 1
    assert "symbol" in intent["missingFields"]


def test_parse_english_view_portfolio(client):
    response = client.post("/api/v1/intent/parse", json={"transcript": "show my portfolio"})
    assert response.status_code == 200
    intent = response.json()["intent"]
    assert intent["intent"] == "VIEW_PORTFOLIO"
    assert intent["requiresConfirmation"] is False


def test_parse_unknown_symbol_flagged_missing(client):
    response = client.post(
        "/api/v1/intent/parse",
        json={"transcript": "Buy 10 shares of Zzzznotarealcompany"},
    )
    assert response.status_code == 200
    intent = response.json()["intent"]
    assert "symbol" in intent["missingFields"]


def test_parse_rejects_empty_transcript(client):
    response = client.post("/api/v1/intent/parse", json={"transcript": ""})
    assert response.status_code == 422


def test_parse_writes_audit_log(client):
    client.post(
        "/api/v1/intent/parse",
        json={"transcript": "Infosys ke 3 shares market price par buy karo."},
    )
    logs = client.get("/api/v1/audit-logs").json()
    assert len(logs) >= 1
    assert logs[0]["originalTranscript"].startswith("Infosys")
