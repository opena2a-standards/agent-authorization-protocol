#!/usr/bin/env python3
"""Generate the AAP token examples (AAP-SPEC section 9) deterministically.

Every token example in AAP-SPEC.md and examples/tokens/ is produced by this
script, never hand-authored. The construction mirrors the reference
implementation (Secretless src/broker/cpi/assertion.ts) byte-for-byte:

    signing input = BASE64URL(UTF8(JSON(header))) || "." || BASE64URL(UTF8(JSON(claims)))
    signature     = Ed25519(signing input)
    token         = signing input || "." || BASE64URL(signature)

JSON serialization is compact (no whitespace), members in the pinned order
below, matching Node's JSON.stringify of the reference's literal objects.
Ed25519 signing is deterministic, so fixed keys + fixed claims = fixed bytes.

All keys in this file are TEST KEYS with published seeds. Never use them for
anything but fixtures.

Usage:
    python3 scripts/generate_examples.py           # (re)write examples/tokens/
    python3 scripts/generate_examples.py --check   # CI drift gate: regenerate,
                                                   # byte-compare with committed
                                                   # files, and require each
                                                   # compact token to appear
                                                   # verbatim in AAP-SPEC.md
"""

import base64
import hashlib
import json
import pathlib
import sys
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "examples" / "tokens"

# --- fixed inputs (TEST values; deterministic) -------------------------------

# Test key seeds (32 bytes hex). Published deliberately: fixtures must be
# reproducible by any implementation. NEVER use outside fixtures.
KEYS = {
    "registry-key-1": "8f7a1c2e4b6d8091a3c5e7f90b2d4f6a8c0e1f3a5b7d9e0c2a4b6d8f0a1c3e5f",
    "broker-key-1": "0102030405060708090a0b0c0d0e0f101112131415161718191a1b1c1d1e1f20",
    "broker-key-2": "202122232425262728292a2b2c2d2e2f303132333435363738393a3b3c3d3e3f",
}

REGISTRY_ISSUER = "did:opena2a:authority:opena2a.org"
BROKER_ISSUER = "https://broker.acme.example"
AGENT_DID = "did:opena2a:agent:acme/orders-reader"
DELEGATEE_DID = "did:opena2a:agent:acme/reporting-bot"

# 2026-06-01T12:00:00Z — the same fixed clock as the reference e2e test.
IAT = int(datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc).timestamp())

ATX_REFERENCE = "sha256:" + hashlib.sha256(b"aap-example-atx").hexdigest()
BINARY_HASH = "sha256:" + hashlib.sha256(b"aap-example-binary").hexdigest()

JTI = {
    "ait": "1c9f2e8a7b6d5c4e3f2a1b0c9d8e7f6a",
    "cgt": "9f8e7d6c5b4a39281706f5e4d3c2b1a0",
    "da": "4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d",
    "bac": "7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b",
}

# --- JWS primitives (mirror assertion.ts exactly) -----------------------------


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def compact_json(obj: dict) -> bytes:
    # Node JSON.stringify: compact separators, insertion order, no ASCII escaping.
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def private_key(kid: str) -> Ed25519PrivateKey:
    return Ed25519PrivateKey.from_private_bytes(bytes.fromhex(KEYS[kid]))


def public_jwk(kid: str) -> dict:
    pub = private_key(kid).public_key().public_bytes_raw()
    return {"kty": "OKP", "crv": "Ed25519", "x": b64url(pub), "kid": kid, "use": "sig", "alg": "EdDSA"}


def mint_compact(kid: str, claims: dict) -> str:
    header = {"alg": "EdDSA", "typ": "JWT", "kid": kid}
    signing_input = f"{b64url(compact_json(header))}.{b64url(compact_json(claims))}"
    sig = private_key(kid).sign(signing_input.encode("ascii"))
    token = f"{signing_input}.{b64url(sig)}"
    verify_compact(token)  # self-verify before the token leaves this process
    return token


def verify_compact(token: str) -> None:
    h, p, s = token.split(".")
    header = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
    pub_raw = base64.urlsafe_b64decode(
        public_jwk(header["kid"])["x"] + "=" * (-len(public_jwk(header["kid"])["x"]) % 4)
    )
    Ed25519PublicKey.from_public_bytes(pub_raw).verify(
        base64.urlsafe_b64decode(s + "=" * (-len(s) % 4)), f"{h}.{p}".encode("ascii")
    )


def mint_general(kids: list[str], claims: dict) -> dict:
    """JWS General JSON Serialization (RFC 7515 section 7.2.1) over the same claims.

    One entry per signature; each protected header carries its own alg + kid —
    this is the multi-suite vehicle of AAP-SPEC section 8.2.
    """
    payload = b64url(compact_json(claims))
    signatures = []
    for kid in kids:
        protected = b64url(compact_json({"alg": "EdDSA", "kid": kid}))
        sig = private_key(kid).sign(f"{protected}.{payload}".encode("ascii"))
        # self-verify
        pub_raw = private_key(kid).public_key().public_bytes_raw()
        Ed25519PublicKey.from_public_bytes(pub_raw).verify(
            sig, f"{protected}.{payload}".encode("ascii")
        )
        signatures.append({"protected": protected, "signature": b64url(sig)})
    return {"payload": payload, "signatures": signatures}


# --- the pinned claim sets (member order is normative for fixtures) ----------


def ait_claims() -> dict:
    return {
        "iss": REGISTRY_ISSUER,
        "sub": AGENT_DID,
        "agent_id": "aim_orders_reader",
        "atx_reference": ATX_REFERENCE,
        "declared_purpose": "Reads order records for reporting",
        "trust_level": 4,
        "iat": IAT,
        "exp": IAT + 3600,
        "jti": JTI["ait"],
    }


def cgt_claims() -> dict:
    # Exactly the reference broker assertion's claim set and order
    # (Secretless src/broker/cpi/assertion.ts mintBrokerAssertion).
    return {
        "iss": BROKER_ISSUER,
        "sub": AGENT_DID,
        "aud": "https://api.orders.internal",
        "scope": "orders.read",
        "trust_class": "orders:read",
        "issuer_chain": [REGISTRY_ISSUER],
        "trust_level": 4,
        "iat": IAT,
        "exp": IAT + 300,
        "jti": JTI["cgt"],
    }


def da_claims() -> dict:
    return {
        "iss": BROKER_ISSUER,
        "sub": DELEGATEE_DID,
        "aud": "https://api.orders.internal",
        "scope": "orders.read",
        "trust_class": "orders:read",
        "issuer_chain": [REGISTRY_ISSUER],
        "trust_level": 4,
        "act": {"sub": AGENT_DID},
        "max_depth": 1,
        "delegator_atx": ATX_REFERENCE,
        "iat": IAT,
        "exp": IAT + 300,
        "jti": JTI["da"],
    }


def bac_claims() -> dict:
    # An L3 claim set; it includes the L1/L2 members to show the cumulative shape.
    return {
        "iss": REGISTRY_ISSUER,
        "sub": AGENT_DID,
        "bac_level": 3,
        "atx_reference": ATX_REFERENCE,
        "binary_hash": BINARY_HASH,
        "drift_score": 0.04,
        "anomaly_state": "nominal",
        "intent_verified": True,
        "iat": IAT,
        "exp": IAT + 60,
        "jti": JTI["bac"],
    }


# --- spec-embed gates (--check) ------------------------------------------------


def extract_json_block(spec: str, heading: str) -> dict:
    """First ```json block after the exact heading line (validate_examples.py rules)."""
    lines = spec.splitlines()
    start = next(i for i, l in enumerate(lines) if l.strip() == heading)
    in_block, block = False, []
    for line in lines[start + 1 :]:
        if not in_block and line.strip() == "```json":
            in_block = True
            continue
        if in_block:
            if line.strip() == "```":
                return json.loads("\n".join(block))
            block.append(line)
    raise SystemExit(f"no json block after {heading!r}")


def same_with_order(a, b) -> bool:
    """Equality that also requires identical member order (the signed bytes' order)."""
    if isinstance(a, dict) and isinstance(b, dict):
        return list(a) == list(b) and all(same_with_order(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same_with_order(x, y) for x, y in zip(a, b))
    return a == b


def check_spec_blocks(spec: str) -> int:
    """Each decoded claim-set block embedded in AAP-SPEC.md must equal the generated
    structure, values AND member order — an edited spec block fails even if the
    schemas still accept it."""
    expected = {
        "### 3.2 Token Structure": ait_claims(),
        "### 4.2 Token Structure": cgt_claims(),
        "### 5.3 Assertion Form": da_claims(),
        "### 6.4 Claim Set": bac_claims(),
        "### 9.4 Multi-Signature Form": mint_general(["broker-key-1", "broker-key-2"], cgt_claims()),
    }
    failures = 0
    for heading, want in expected.items():
        got = extract_json_block(spec, heading)
        if same_with_order(got, want):
            print(f"spec block OK  {heading}")
        else:
            print(f"SPEC BLOCK DRIFT at {heading!r} (must equal the generated fixture, values and order)")
            failures += 1
    return failures


def check_header_shapes() -> int:
    """Every protected header must be exactly the pinned section 9.2/9.4 shape."""
    failures = 0
    compact_kids = {"ait": "registry-key-1", "cgt": "broker-key-1", "da": "broker-key-1", "bac": "registry-key-1"}
    for name, kid in compact_kids.items():
        token = (OUT / f"{name}-v1.jwt").read_text(encoding="utf-8").strip()
        h = token.split(".")[0]
        header = json.loads(base64.urlsafe_b64decode(h + "=" * (-len(h) % 4)))
        want = {"alg": "EdDSA", "typ": "JWT", "kid": kid}
        if same_with_order(header, want):
            print(f"header OK      {name}-v1.jwt")
        else:
            print(f"HEADER SHAPE   {name}-v1.jwt: {header} != {want}")
            failures += 1
    general = json.loads((OUT / "cgt-v1.general.json").read_text(encoding="utf-8"))
    for i, entry in enumerate(general["signatures"]):
        p = entry["protected"]
        header = json.loads(base64.urlsafe_b64decode(p + "=" * (-len(p) % 4)))
        kid = ["broker-key-1", "broker-key-2"][i]
        want = {"alg": "EdDSA", "kid": kid}
        if same_with_order(header, want):
            print(f"header OK      cgt-v1.general.json signatures[{i}]")
        else:
            print(f"HEADER SHAPE   cgt-v1.general.json signatures[{i}]: {header} != {want}")
            failures += 1
    return failures


# --- output -------------------------------------------------------------------


def build_files() -> dict[str, str]:
    files: dict[str, str] = {}

    tokens = {
        "ait": ("registry-key-1", ait_claims()),
        "cgt": ("broker-key-1", cgt_claims()),
        "da": ("broker-key-1", da_claims()),
        "bac": ("registry-key-1", bac_claims()),
    }
    for name, (kid, claims) in tokens.items():
        files[f"{name}-v1.jwt"] = mint_compact(kid, claims) + "\n"
        files[f"{name}-v1.claims.json"] = json.dumps(claims, indent=2) + "\n"

    general = mint_general(["broker-key-1", "broker-key-2"], cgt_claims())
    files["cgt-v1.general.json"] = json.dumps(general, indent=2) + "\n"

    files["test-keys.json"] = (
        json.dumps(
            {
                "warning": "TEST KEYS with published seeds — fixture reproduction only, never production use",
                "keys": [
                    {"kid": kid, "ed25519SeedHex": seed, "publicJwk": public_jwk(kid)}
                    for kid, seed in KEYS.items()
                ],
            },
            indent=2,
        )
        + "\n"
    )
    return files


def main() -> int:
    check = "--check" in sys.argv
    files = build_files()

    if check:
        failures = 0
        for name, content in files.items():
            path = OUT / name
            if not path.exists():
                print(f"MISSING   examples/tokens/{name}")
                failures += 1
            elif path.read_text(encoding="utf-8") != content:
                print(f"DRIFT     examples/tokens/{name} (regenerate with scripts/generate_examples.py)")
                failures += 1
            else:
                print(f"stable    examples/tokens/{name}")
        # Embed gate: every compact token must appear verbatim in the spec.
        spec = (ROOT / "AAP-SPEC.md").read_text(encoding="utf-8")
        for name, content in files.items():
            if name.endswith(".jwt") and content.strip() not in spec:
                print(f"NOT EMBEDDED in AAP-SPEC.md: examples/tokens/{name}")
                failures += 1
        failures += check_spec_blocks(spec)
        failures += check_header_shapes()
        return 1 if failures else 0

    OUT.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        (OUT / name).write_text(content, encoding="utf-8")
        print(f"wrote examples/tokens/{name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
