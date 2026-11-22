from app.services.fraud_engine import severity


def test_severity_boundaries():
    assert severity(29) == "LOW"
    assert severity(30) == "MEDIUM"
    assert severity(60) == "HIGH"
    assert severity(80) == "CRITICAL"
