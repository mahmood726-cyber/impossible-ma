import pytest

from impossible_ma.truthcert import sign_bundle, verify_bundle, TruthCertError


@pytest.fixture(autouse=True)
def _hmac_env(monkeypatch):
    monkeypatch.setenv("TRUTHCERT_HMAC_KEY", "a" * 64)


def test_sign_and_verify_roundtrip():
    payload = {"case": "k1", "lower": -0.5, "upper": 0.1}
    bundle = sign_bundle(payload)
    assert "signature" in bundle
    assert bundle["payload"] == payload
    verify_bundle(bundle)


def test_verify_rejects_tampered_payload():
    bundle = sign_bundle({"case": "k1", "lower": -0.5, "upper": 0.1})
    bundle["payload"]["upper"] = 999.0
    with pytest.raises(TruthCertError, match="signature"):
        verify_bundle(bundle)


def test_sign_fails_closed_when_no_key(monkeypatch, tmp_path):
    monkeypatch.delenv("TRUTHCERT_HMAC_KEY", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    with pytest.raises(TruthCertError, match="TRUTHCERT_HMAC_KEY"):
        sign_bundle({"x": 1})


def test_signature_differs_by_only_last_char_still_rejected():
    bundle = sign_bundle({"x": 1})
    good = bundle["signature"]
    bad = good[:-1] + ("0" if good[-1] != "0" else "1")
    bundle["signature"] = bad
    with pytest.raises(TruthCertError):
        verify_bundle(bundle)


def test_verify_rejects_unsupported_alg():
    bundle = {"payload": {"x": 1}, "signature": "deadbeef", "alg": "MD5"}
    with pytest.raises(TruthCertError, match="alg"):
        verify_bundle(bundle)
