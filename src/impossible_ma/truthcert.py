"""TruthCert HMAC-SHA256 bundle.

Key source: TRUTHCERT_HMAC_KEY env var, or ~/.truthcert_key file (>= 32 bytes).
Never derive the key from bundle contents. Fail closed when no key is available.
Verification uses hmac.compare_digest (constant-time).
"""
import hashlib
import hmac
import json
import os
from pathlib import Path
from typing import Any


class TruthCertError(RuntimeError):
    pass


def _load_key() -> bytes:
    env_key = os.environ.get("TRUTHCERT_HMAC_KEY")
    if env_key:
        return env_key.encode("utf-8")
    keyfile = Path.home() / ".truthcert_key"
    if keyfile.exists() and keyfile.stat().st_size >= 32:
        return keyfile.read_bytes().strip()
    raise TruthCertError(
        "No TRUTHCERT_HMAC_KEY env var and no ~/.truthcert_key file "
        "(>= 32 bytes). Set TRUTHCERT_HMAC_KEY or create the keyfile. "
        "Key MUST NOT be derived from bundle contents."
    )


def _canonical(payload: Any) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sign_bundle(payload: dict) -> dict:
    key = _load_key()
    sig = hmac.new(key, _canonical(payload), hashlib.sha256).hexdigest()
    return {"payload": payload, "signature": sig, "alg": "HMAC-SHA256"}


def verify_bundle(bundle: dict) -> None:
    if bundle.get("alg") != "HMAC-SHA256":
        raise TruthCertError(f"unsupported alg: {bundle.get('alg')!r}")
    key = _load_key()
    expected = hmac.new(key, _canonical(bundle["payload"]), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, bundle["signature"]):
        raise TruthCertError("signature does not match payload (tampered or wrong key)")
