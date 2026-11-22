from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_round_trip():
    digest = hash_password("StrongPassword123!")
    assert verify_password("StrongPassword123!", digest)
    assert not verify_password("wrong", digest)


def test_jwt_round_trip():
    token = create_access_token("00000000-0000-0000-0000-000000000001", "analyst@aml.local", "ANALYST")
    payload = decode_access_token(token)
    assert payload["email"] == "analyst@aml.local"
    assert payload["role"] == "ANALYST"
