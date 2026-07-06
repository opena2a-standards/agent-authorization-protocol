# Agent Authorization Protocol (AAP)

## Scoped, Attested Authorization for AI Agent Systems

**Version:** 0.3.0-draft
**Authors:** OpenA2A
**Date:** July 2026
**Intended status:** Standards Track (IETF Internet-Draft; named individual authors will be attributed at Internet-Draft submission per IETF convention)

> **Reconciliation note (2026-06-01).** This document supersedes the March 2026 draft
> `aim-roadmap/master-plan/drafts/ietf-aap-internet-draft.md` by the same author. Changes
> are non-architectural: the credential is renamed ATC → **ATX** (Agent Trust eXtension,
> per `atx-spec/core.md`), DIDs move from `did:atp:` to `did:opena2a:`, and a companion
> document, [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md), is referenced as the
> resolution/enforcement layer. The six-component token model below is unchanged.

---

## Abstract

This document defines the Agent Authorization Protocol (AAP), a standard for authorization
in AI agent systems. AAP provides mechanisms for agent identity assertion, scoped capability
grants, cross-agent delegation, behavioral attestation, cross-organizational federation, and
revocation propagation. AAP is the authorization complement to existing agent communication
protocols (A2A, MCP) in the same way that OAuth 2.0 complements HTTP for web applications.

AAP has two layers:

1. **The token model** (this document), the AAP credentials and assertions: what they
   contain, how they are signed, and how they are verified.
2. **The broker & resolution layer** ([`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md)),
   how an agent obtains and exercises a grant without the credential value ever entering its
   reasoning context, via a `grant://` reference and a local broker. The broker is the
   component that mints and exchanges the tokens defined here.

**Reference implementation.** The AAP broker reference implementation is
[Secretless](https://github.com/opena2a-org/secretless) (`src/broker/`, `src/grant/`): the
`grant://` scheme, the resolution flow of §6 of the broker profile, the Credential Provider
Interface with the Exchange mode (RFC 8693) implemented, credential confinement behind an
ephemeral worker, and an in-repo end-to-end broker conformance test
(`src/broker/aap-conformance.test.ts`). It targets broker conformance Level 1 (see
[`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md) §13-§14). AIM (Agent Identity Management)
supplies the developer surface the broker profile names (the `@agent.perform_action`
decorator and 5-step fine-grained authorization) and is the reference implementation for the
identity and trust layers AAP builds on (AIP, ATX, ATP); AIM does not implement the broker.

---

## Status of This Memo

This Internet-Draft is submitted in full conformance with the provisions of BCP 78 and
BCP 79. Internet-Drafts are working documents of the Internet Engineering Task Force (IETF).

---

## 1. Introduction

AI agent systems present authorization challenges that existing protocols (OAuth 2.0, SAML,
OIDC) were not designed to address. Agents are non-deterministic: the same agent with
identical permissions can behave differently depending on its inputs, conversation history,
and model state. Static authorization grants cannot account for this behavioral variability.

AAP introduces six protocol components that together provide complete authorization coverage
for agent-to-agent, agent-to-service, and human-to-agent interactions:

1. **Agent Identity Token (AIT)**, cryptographic identity assertion.
2. **Capability Grant Token (CGT)**, scoped, short-lived authorization.
3. **Delegation Assertion (DA)**, cross-agent capability delegation.
4. **Behavioral Attestation Claim (BAC)**, real-time behavioral state proof.
5. **Cross-Org Trust Federation**, Registry-to-Registry mutual trust.
6. **Revocation Propagation Protocol**, federated revocation within 60 seconds.

The governing constraint on every choice in AAP: **OpenA2A owns the protocol and the
vocabulary; it owns no one's trust.** Nothing in AAP may require a vendor, cloud, or
government to surrender its own root. The topology is a trust *program* of federated
conformant Root Authorities, not a single root, the same property that made DNS, TLS,
OAuth, and OIDC universal.

## 2. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "MAY", and "OPTIONAL" are to be interpreted as described in BCP 14 (RFC 2119,
RFC 8174).

- **Agent**, an AI system that can take actions on behalf of a user or organization.
- **Agent Trust eXtension (ATX)**, a signed credential issued by a Registry attesting to an
  agent's identity, code integrity, capabilities, and trust level. ATX is the credential the
  AIT references. (ATX is the current name for the credential formerly called ATC.)
- **Agent Security Context (ASC)**, shared state describing an agent's current security
  posture across monitoring products.
- **NanoMind**, local semantic intent classification model used for intent-verified
  authorization.
- **Registry / Root Authority**, the trust authority that issues ATXs, maintains the
  transparency log, and computes trust scores. Participants operate conformant Root
  Authorities under the ATP Trust Program.

## 3. Agent Identity Token (AIT)

### 3.1 Purpose
The AIT is a cryptographic assertion of agent identity, analogous to an OIDC ID Token. It is
presented by agents to identify themselves to other agents, services, and infrastructure.

### 3.2 Token Structure

The AIT is an AAP token in the form of Section 9: a JWT whose claim set is pinned by
[`schemas/ait-claims-v1.schema.json`](./schemas/ait-claims-v1.schema.json). Claim names
follow the JWT registry convention (Section 9.6).

| Claim | Req | Type | Meaning |
|---|---|---|---|
| `iss` | MUST | DID | Issuing Registry (Root Authority) DID. |
| `sub` | MUST | DID | Agent DID (`did:opena2a:agent:org/agent-name`). |
| `agent_id` | MAY | string | Deployment-local agent identifier. |
| `atx_reference` | MUST | `sha256:` + 64 hex | Hash of the current ATX this identity references. |
| `declared_purpose` | MAY | string | Natural-language purpose declaration. |
| `trust_level` | MUST | integer 0–4 | Registry trust level at issuance. |
| `iat` / `exp` | MUST | NumericDate | Validity window (seconds since epoch, RFC 7519 §2). |
| `jti` | MUST | 32 hex chars | Unique token id, 128-bit (Section 8.1). |
| `aap_ver` | MAY (v1) | integer | Claim-schema version (Section 9.6). |

Example (generated by `scripts/generate_examples.py` with the published test keys — never
hand-authored; the decoded claim set follows):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6InJlZ2lzdHJ5LWtleS0xIn0.eyJpc3MiOiJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhZ2VudF9pZCI6ImFpbV9vcmRlcnNfcmVhZGVyIiwiYXR4X3JlZmVyZW5jZSI6InNoYTI1NjoyMDUyODc5ZGRhMTViMWNhNWU2MDMxOWUzNDc3YTQwMDg0MTJiZmZkYWYzYzM1NjZjNjU4Nzk1YTQ4Y2FiOGZkIiwiZGVjbGFyZWRfcHVycG9zZSI6IlJlYWRzIG9yZGVyIHJlY29yZHMgZm9yIHJlcG9ydGluZyIsInRydXN0X2xldmVsIjo0LCJpYXQiOjE3ODAzMTUyMDAsImV4cCI6MTc4MDMxODgwMCwianRpIjoiMWM5ZjJlOGE3YjZkNWM0ZTNmMmExYjBjOWQ4ZTdmNmEifQ.RwM5kDqjuCZpmPtTNipseEGcHB06uqZZ8T8Shm2v3FROK9ECULU1qjP466AMwEPjAKL-xFIasjTo_en20Hc_Bw
```

```json
{
  "iss": "did:opena2a:authority:opena2a.org",
  "sub": "did:opena2a:agent:acme/orders-reader",
  "agent_id": "aim_orders_reader",
  "atx_reference": "sha256:2052879dda15b1ca5e60319e3477a4008412bffdaf3c3566c658795a48cab8fd",
  "declared_purpose": "Reads order records for reporting",
  "trust_level": 4,
  "iat": 1780315200,
  "exp": 1780318800,
  "jti": "1c9f2e8a7b6d5c4e3f2a1b0c9d8e7f6a"
}
```

No reference implementation mints AITs yet; the schema and generated fixture pin the form
for implementers. (The broker reference implementation consumes the ATX directly as its
subject claim; the AIT is the standalone identity assertion for deployments without a
presented ATX.)

### 3.3 Verification
AIT verification MUST be local. The verifier checks the signature against the issuer's public
key (distributed via the trust anchor mechanism). No network call to the Registry is required
at verification time.

## 4. Capability Grant Token (CGT)

### 4.1 Purpose
The CGT is a short-lived, scoped authorization token, analogous to an OAuth 2.0 Access Token.
It authorizes a specific capability exercise with fine-grained-authorization (FGA)
constraints. In a broker deployment ([`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md)) the
CGT is what the broker mints from a verified ATX before exchanging it for a downstream token.

### 4.2 Token Structure

The CGT is an AAP token in the form of Section 9, **ratified byte-for-byte from the
reference implementation**: the claim set below is exactly what the Secretless broker's
`mintBrokerAssertion` (`src/broker/cpi/assertion.ts`) signs. It is pinned by
[`schemas/cgt-claims-v1.schema.json`](./schemas/cgt-claims-v1.schema.json).

| Claim | Req | Type | Meaning |
|---|---|---|---|
| `iss` | MUST | string | Minting broker's issuer identifier (the operator's broker URL). |
| `sub` | MUST | DID | Agent DID, taken from the **verified** ATX — never from agent input. |
| `aud` | MUST | string | Downstream audience / resource. |
| `scope` | MUST | string | Downstream OAuth scope requested (e.g. `orders.read`). |
| `trust_class` | MUST | `class:action` | The ATX capability (abstract trust class, e.g. `orders:read`) exercised for this grant. Distinct from `scope`: the trust class is the portable, abstract capability; the scope is the local downstream binding. |
| `issuer_chain` | MUST | DID array | ATX issuer chain, carried for v2 cross-broker verification (broker profile §7, §11). |
| `trust_level` | MUST | integer 0–4 | ATX trust level. |
| `iat` / `exp` | MUST | NumericDate | Validity window; `exp - iat` is the policy TTL (§4.3). |
| `jti` | MUST | 32 hex chars | Unique token id, 16 random bytes hex (Section 8.1). |
| `aap_ver` | MAY (v1) | integer | Claim-schema version (Section 9.6). |
| `fga_constraints` | MAY | string | JSON-encoded FGA policy. Optional-to-ignore (§8.3); not minted by the v1 reference. |
| `intent_verified` | MAY | boolean | NanoMind intent verification result. Optional-to-ignore; not minted by the v1 reference. |
| `max_uses` | MAY | integer | Use-count bound. Optional-to-ignore; not minted by the v1 reference. |
| `context_required` | MAY | boolean | Whether exercise requires conversational context review. Optional-to-ignore; not minted by the v1 reference. |

Example (generated; this is a real, verifiable token under the published test keys):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiI5ZjhlN2Q2YzViNGEzOTI4MTcwNmY1ZTRkM2MyYjFhMCJ9.7zmUIjgHLztQBSxtz38bKM5_lvta8WshMA_e6zRdW4_MhUb7fw1A5dAQMAWOJUKZklBFmdJf_vfoL0_0B-eJBA
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/orders-reader",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "orders:read",
  "issuer_chain": ["did:opena2a:authority:opena2a.org"],
  "trust_level": 4,
  "iat": 1780315200,
  "exp": 1780315500,
  "jti": "9f8e7d6c5b4a39281706f5e4d3c2b1a0"
}
```

In a broker deployment the CGT is used as the RFC 8693 `subject_token` with
`subject_token_type: urn:ietf:params:oauth:token-type:jwt` — which is why the compact JWT
form (Section 9.3) is mandatory on interop paths: the downstream authorization server
verifies it as a standard JWT against the broker's published key material.

### 4.3 TTL Tiers
- STANDARD: 4 hours
- PRIVILEGED: 30 minutes
- SUPER_PRIVILEGED: 15 minutes (no renewal, human approval required)

## 5. Delegation Assertion (DA)

### 5.1 Purpose
The DA enables cross-agent capability delegation, analogous to OAuth 2.0 Token Exchange
(RFC 8693). The delegatee's capability scope CANNOT exceed the delegator's scope. The broker
profile's Exchange mode is a realization of the DA over RFC 8693.

### 5.2 Constraints
- MaxDepth limits delegation chain depth.
- Delegator's ATX hash is embedded for audit trail.
- Scope is cryptographically bounded.

### 5.3 Assertion Form

The DA is an AAP token in the form of Section 9: the CGT claim set (§4.2) plus the
RFC 8693 delegation members, pinned by
[`schemas/da-claims-v1.schema.json`](./schemas/da-claims-v1.schema.json).

| Claim | Req | Type | Meaning |
|---|---|---|---|
| *(all CGT claims)* | MUST | §4.2 | `sub` is the **delegatee**. |
| `act` | MUST | object | The delegating agent, `{"sub": <delegator DID>}`. Nesting `act` expresses a chain, innermost actor first (RFC 8693 §4.1). |
| `max_depth` | MUST | integer ≥ 1 | Remaining delegation depth below this assertion. |
| `delegator_atx` | MUST | `sha256:` + 64 hex | Delegator's ATX hash (§5.2 audit trail). |

The delegatee's `scope` and `trust_class` MUST be equal to or a subset of the
delegator's. The minting broker enforces subsetting at mint time; a verifier that can
resolve the delegator's grant MUST re-check it.

Example (generated; `orders-reader` delegates read access to `reporting-bot`):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL3JlcG9ydGluZy1ib3QiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImFjdCI6eyJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIifSwibWF4X2RlcHRoIjoxLCJkZWxlZ2F0b3JfYXR4Ijoic2hhMjU2OjIwNTI4NzlkZGExNWIxY2E1ZTYwMzE5ZTM0NzdhNDAwODQxMmJmZmRhZjNjMzU2NmM2NTg3OTVhNDhjYWI4ZmQiLCJpYXQiOjE3ODAzMTUyMDAsImV4cCI6MTc4MDMxNTUwMCwianRpIjoiNGEzYjJjMWQwZTlmOGE3YjZjNWQ0ZTNmMmExYjBjOWQifQ.qIy-22zZEY-rNB3VX_5t_aSAgp5KVDdLDXA3GdVnZWPtXyBfTguAT_tlGlB7jhKZQ2rpH_QbckF8dglX__BPAQ
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/reporting-bot",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "orders:read",
  "issuer_chain": ["did:opena2a:authority:opena2a.org"],
  "trust_level": 4,
  "act": {"sub": "did:opena2a:agent:acme/orders-reader"},
  "max_depth": 1,
  "delegator_atx": "sha256:2052879dda15b1ca5e60319e3477a4008412bffdaf3c3566c658795a48cab8fd",
  "iat": 1780315200,
  "exp": 1780315500,
  "jti": "4a3b2c1d0e9f8a7b6c5d4e3f2a1b0c9d"
}
```

The v1 reference realizes delegation through its Exchange mode (the broker assertion is
the subject token of the RFC 8693 exchange); it does not yet mint standalone DAs with an
`act` chain.

## 6. Behavioral Attestation Claim (BAC)

### 6.1 Purpose
The BAC is a short-lived (60-second TTL) signed assertion of an agent's current behavioral
state. It has no internet parallel, it exists because agents are non-deterministic.

### 6.2 Three Levels
- L1: build-time attestation (ATX + scan results).
- L2: runtime self-attestation (binary hash match).
- L3: behavioral continuity (drift score + anomaly state + intent verification).

### 6.3 Verification
BAC verification is local (< 2 ms). The receiver verifies the signature against the
issuing Registry instance's published public key, under the suite model of §8.2. The
post-quantum profile for BACs (an ML-DSA-65 signature alongside Ed25519, via the
multi-signature form of Section 9.4) is a target, not a shipped property: no
implementation mints BACs yet, and v1 fixtures are Ed25519.

### 6.4 Claim Set

The BAC is an AAP token in the form of Section 9, pinned by
[`schemas/bac-claims-v1.schema.json`](./schemas/bac-claims-v1.schema.json). Levels are
cumulative: an L2 BAC carries the L1 members, an L3 BAC carries all.

| Claim | Req | Type | Meaning |
|---|---|---|---|
| `iss` | MUST | DID | Issuing Registry instance. |
| `sub` | MUST | DID | Attested agent. |
| `bac_level` | MUST | 1, 2, or 3 | Attestation level (§6.2). |
| `atx_reference` | MUST (L1+) | `sha256:` + 64 hex | Build-time attestation anchor. |
| `binary_hash` | MUST (L2+) | `sha256:` + 64 hex | Runtime binary self-attestation. |
| `drift_score` | MUST (L3) | number 0–1 | Behavioral drift measure. |
| `anomaly_state` | MUST (L3) | string | Current anomaly state (vocabulary implementation-defined in v1). |
| `intent_verified` | MUST (L3) | boolean | NanoMind intent verification state. |
| `iat` / `exp` | MUST | NumericDate | `exp - iat` MUST be ≤ 60 (the 60-second TTL, §6.1). |
| `jti` | MUST | 32 hex chars | Unique token id (§8.1). |
| `aap_ver` | MAY (v1) | integer | Claim-schema version (Section 9.6). |

Example (generated; an L3 attestation):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6InJlZ2lzdHJ5LWtleS0xIn0.eyJpc3MiOiJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJiYWNfbGV2ZWwiOjMsImF0eF9yZWZlcmVuY2UiOiJzaGEyNTY6MjA1Mjg3OWRkYTE1YjFjYTVlNjAzMTllMzQ3N2E0MDA4NDEyYmZmZGFmM2MzNTY2YzY1ODc5NWE0OGNhYjhmZCIsImJpbmFyeV9oYXNoIjoic2hhMjU2OjQ3OWJkMjhhNTVlM2EzZWIyMGI5ZjViNDgyMDIzMThkNWRlOWQwZGJlYTllNmRmMjBiMmVlN2ZmOTVhNGMxMzUiLCJkcmlmdF9zY29yZSI6MC4wNCwiYW5vbWFseV9zdGF0ZSI6Im5vbWluYWwiLCJpbnRlbnRfdmVyaWZpZWQiOnRydWUsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1MjYwLCJqdGkiOiI3ZTZmNWE0YjNjMmQxZTBmOWE4YjdjNmQ1ZTRmM2EyYiJ9.hqY6KA-OWfh8r7nA98fK5G30iYli7WJSXGiwSoi938y6JA_2D6T0FSVKElxc_js2322uKOT_oJ9UPe2-VbJOBA
```

```json
{
  "iss": "did:opena2a:authority:opena2a.org",
  "sub": "did:opena2a:agent:acme/orders-reader",
  "bac_level": 3,
  "atx_reference": "sha256:2052879dda15b1ca5e60319e3477a4008412bffdaf3c3566c658795a48cab8fd",
  "binary_hash": "sha256:479bd28a55e3a3eb20b9f5b48202318d5de9d0dbea9e6df20b2ee7ff95a4c135",
  "drift_score": 0.04,
  "anomaly_state": "nominal",
  "intent_verified": true,
  "iat": 1780315200,
  "exp": 1780315260,
  "jti": "7e6f5a4b3c2d1e0f9a8b7c6d5e4f3a2b"
}
```

## 7. Cross-Organizational Federation

### 7.1 Model
Federation follows a PKI-style hierarchy: subordinate Registry nodes (Root Authorities) issue
ATXs trusted by their peers per published trust lists. Any federated node can verify any other
node's ATXs without direct contact. No participant joins OpenA2A; each operates a conformant
Root Authority and cross-trusts.

### 7.2 Revocation Propagation
When any node revokes an ATX, the revocation MUST propagate to all federation members within
60 seconds via signed push. No member needs to poll. The broker profile binds authorization
revocation entirely to this mechanism, it defines no separate revocation system.

## 8. Security Considerations

### 8.1 Replay Prevention
All tokens include a unique identifier (`jti`): 16 random bytes, lowercase hex (32
characters), as minted by the reference implementation. Receivers MUST track used
identifiers for the token's TTL window.

### 8.2 Cryptographic Agility and Post-Quantum Readiness
The signature suite is a named, swappable field — the JOSE `alg` of each signature's
protected header (Section 9) — so suites can be added or retired by negotiation, never by
a new credential format. A verifier MUST reject a token whose declared suite it does not
support rather than silently downgrade.

The v1 suite registry (Section 9.5) contains exactly one entry, `EdDSA` (Ed25519,
RFC 8037), which is what the reference implementation signs today. The post-quantum
target is hybrid Ed25519 + ML-DSA-65 (FIPS 204), carried as two `signatures[]` entries of
the multi-signature form (Section 9.4) — one per suite, matching ATX's per-signature
`algorithm` model: a hybrid token verifies only if at least one ML-DSA-65 signature
**and** at least one Ed25519 signature verify. The ML-DSA-65 `alg` identifier is adopted
on IETF registration of ML-DSA for JOSE (coordinated with the ATX suite registry); no AAP
implementation mints post-quantum signatures yet. Key exchange, where AAP deployments
negotiate transport keys, targets hybrid X25519 + ML-KEM-768 (FIPS 203) on the same
adoption path.

### 8.3 Intent Verification
NanoMind intent verification provides semantic understanding that static policies cannot.
Intent classification is probabilistic; systems MUST NOT rely on it alone for irreversible
actions.

### 8.4 Trust is not authorization
A valid AIT/ATX is an identity and posture assertion, not permission to touch a resource, and
trust is not transitive. Authorization exists only where a local policy grants it; brokers
MUST default-deny. See [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md) §3.

### 8.5 Credential confinement
Where AAP is deployed via a broker, no credential value, temporary token, or backend
identifier may enter an agent's reasoning context. This is normative in the broker profile
(§4) and is the property that defends the credential-harvest and exfiltration attack classes
of the AI Agent Threat Matrix (techniques T-3002, T-3003, T-3006, T-8002).

## 9. Token Serialization and Signing (Normative)

This section pins the byte-level form of every AAP token (AIT, CGT, DA, BAC). It is
ratified from the reference implementation (Secretless `src/broker/cpi/assertion.ts`):
what the reference broker actually signs is normative, byte for byte. AAP tokens are
JOSE objects — JWTs (RFC 7519) over JWS (RFC 7515).

### 9.1 Canonical Form

The signed bytes are the **JWS Signing Input**:

```
ASCII( BASE64URL(UTF8(protected header)) || "." || BASE64URL(payload) )
```

AAP defines no other canonical form: **serialization is canonicalization.** The producer
serializes the header and claim set once (compact JSON, no insignificant whitespace) and
signs those exact bytes; a verifier operates on the transmitted base64url segments and
never re-serializes. There is no JCS step, no field projection, and no delimiter
grammar — this is the deliberate design difference from ATX (JCS over a projected TBS,
`atx-spec/core.md` §1.3a.2) and ATP (pipe-delimited seven-field string, ATP §4.3), and it
exists because AAP tokens, uniquely in the family, are verified by *foreign* systems:
RFC 8693 authorization servers, STSes, and OIDC-style verifiers that understand exactly
one thing, a standard JWT. Base64url is unpadded (RFC 7515 §2).

### 9.2 Protected Header

Pinned by [`schemas/jose-header-v1.schema.json`](./schemas/jose-header-v1.schema.json):

| Member | Req | v1 Value |
|---|---|---|
| `alg` | MUST | A suite identifier from the registry in §9.5. v1: `EdDSA`. |
| `typ` | MUST | `JWT`. Explicit per-token media types (e.g. `aap-cgt+jwt`, RFC 9068 style) are a candidate v2 negotiation item (§8.1 of the broker profile); v1 pins the value the reference emits. |
| `kid` | MUST | Key id of the signing key in the issuer's published key material (the broker's discovery document, or the Registry's key set). |

### 9.3 Compact Serialization

The compact form `header.payload.signature` is the v1 baseline and is REQUIRED on every
interoperability path where a foreign system verifies the token — in particular a CGT/DA
presented as an RFC 8693 `subject_token` (`urn:ietf:params:oauth:token-type:jwt`) MUST be
compact. A compact token carries exactly one signature and therefore exactly one suite.

### 9.4 Multi-Signature Form

Where more than one signature is required — the hybrid post-quantum profile of §8.2 —
the token is carried as JWS General JSON Serialization (RFC 7515 §7.2.1), pinned by
[`schemas/jws-general-v1.schema.json`](./schemas/jws-general-v1.schema.json): one
`signatures[]` entry per suite, each with its own protected header (`alg`, `kid`) over
the same payload. This is the family's named, swappable per-signature suite model — an
entry's `{protected.alg, protected.kid, signature}` corresponds one-to-one to the
ATX/ATP `{algorithm, keyId, value}` — expressed in the JOSE-standard container. Every
declared entry MUST verify; a verifier MUST NOT accept a token on a subset of its
declared signatures.

Example (generated; the §4.2 CGT claim set under two Ed25519 test keys — a hybrid
deployment replaces the second entry with an ML-DSA-65 signature once that suite is
registered):

```json
{
  "payload": "eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiI5ZjhlN2Q2YzViNGEzOTI4MTcwNmY1ZTRkM2MyYjFhMCJ9",
  "signatures": [
    {
      "protected": "eyJhbGciOiJFZERTQSIsImtpZCI6ImJyb2tlci1rZXktMSJ9",
      "signature": "7-kf_vmchx-P6zg-CsSIQvYdPHQaObrQSIngnI7HpL1D5l544iGTg8jIOxpNf0g0KoBRNVr2vJ5Gj3fjRwtoAg"
    },
    {
      "protected": "eyJhbGciOiJFZERTQSIsImtpZCI6ImJyb2tlci1rZXktMiJ9",
      "signature": "oa5XXSuBDkyj3T9r0ySIKKbYpvko5mODZkxMOqZ-l5lenGjLEb4p5X2rALKAqP-DmS0fkDiex41IzgrUw6guDQ"
    }
  ]
}
```

### 9.5 Suite Registry (v1)

| `alg` | Algorithm | Status |
|---|---|---|
| `EdDSA` | Ed25519 (RFC 8032 / RFC 8037) | Active. The only suite the v1 reference mints. |
| `ML-DSA-65` | FIPS 204 | Reserved. Adopted on IETF registration of ML-DSA for JOSE; until then no AAP token declares it. |

Adding or retiring a suite is a row change here plus version negotiation (broker profile
§8.1) — never a format change.

### 9.6 Claim Conventions

- Claim names use the JWT registry convention (lowercase, snake_case for compound
  names: `trust_class`, `issuer_chain`), matching RFC 7519/8693/9068 practice. This is a
  deliberate, documented exception to the OpenA2A camelCase JSON convention, which
  governs API responses, not IETF-track token claims.
- `iat`/`exp` are NumericDate (seconds since epoch, RFC 7519 §2) — not ISO 8601 strings.
- Unknown claims follow §8.3: optional-to-ignore unless marked mandatory-to-understand.
- **Versioning:** the claim-schema version is the `aap_ver` claim. It is OPTIONAL in v1
  (the reference does not mint it; v1 fixtures omit it) and REQUIRED from the first
  federated version (broker conformance Level 3), where a peer broker must select a
  claim schema without a shared channel. Protocol *messages* carry the negotiated
  version explicitly per broker profile §8.1.

### 9.7 Fixtures

Every token example in this document is generated by
[`scripts/generate_examples.py`](./scripts/generate_examples.py) from published test-key
seeds ([`examples/tokens/test-keys.json`](./examples/tokens/test-keys.json)), fixed
timestamps, and fixed `jti` values — deterministic and reproducible byte-for-byte, and
verified in-process before being written. CI regenerates and byte-compares
(`--check`), and fails if any embedded token in this document drifts from the generated
fixture. Hand-authored example bytes are prohibited.

## 10. IANA Considerations

This document requests registration of the `aap` scheme in the URI Schemes registry, and (via
the broker profile) the `grant` scheme. It further anticipates registries for AAP protocol
versions, CPI mode identifiers, and signature suite identifiers (coordinated with the ATX
suite registry). Until IANA registries exist, the suite registry of Section 9.5 is
managed in this specification.

## 11. References

### Normative References
- [RFC 2119] / [RFC 8174], Key words for requirement levels.
- [RFC 6749], The OAuth 2.0 Authorization Framework.
- [RFC 7515], JSON Web Signature (JWS).
- [RFC 7519], JSON Web Token (JWT).
- [RFC 8037], CFRG Elliptic Curve Signatures in JOSE (`EdDSA`).
- [RFC 8693], OAuth 2.0 Token Exchange.
- [RFC 6962], Certificate Transparency.
- [FIPS 203], Module-Lattice-Based Key-Encapsulation Mechanism Standard.
- [FIPS 204], Module-Lattice-Based Digital Signature Standard.
- [ATX], Agent Trust eXtension credential format (`atx-spec/core.md`).
- [ATP], Agent Trust Protocol.

### Informative References
- [A2A], Agent-to-Agent Protocol Specification.
- [MCP], Model Context Protocol Specification.
- [OpenA2A], OpenA2A Platform Architecture.
- [AAP-BROKER-PROFILE], AAP Broker & Resolution Layer (this repository).
- [AI Agent Threat Matrix], https://threats.opena2a.org

## Authors' Addresses

Abdel Fane
OpenA2A
Email: abdel@opena2a.org
