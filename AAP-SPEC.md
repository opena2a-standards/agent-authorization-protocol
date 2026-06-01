# Agent Authorization Protocol (AAP)

## Scoped, Attested Authorization for AI Agent Systems

**Version:** 0.2.0-draft
**Authors:** Abdel Fane (OpenA2A)
**Date:** June 2026
**Intended status:** Standards Track (IETF Internet-Draft)

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
```json
{
  "agentId": "uuid",
  "agentDid": "did:opena2a:agent:org/agent-name",
  "atxReference": "sha256-hash-of-current-atx",
  "declaredPurpose": "natural language description",
  "trustLevel": 0,
  "issuedAt": "ISO 8601",
  "expiresAt": "ISO 8601",
  "signature": "Ed25519 + ML-DSA-65 hybrid",
  "issuerDid": "did:opena2a:authority:issuing-registry"
}
```

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
```json
{
  "tokenId": "unique-id",
  "agentId": "uuid",
  "capability": "db:read",
  "scope": {
    "resources": ["customers"],
    "actions": ["read"],
    "attributes": ["name", "email"],
    "maxUses": 100,
    "contextRequired": true
  },
  "fgaConstraints": "json-encoded FGA policy",
  "intentVerified": true,
  "issuedAt": "ISO 8601",
  "expiresAt": "ISO 8601",
  "signature": "Ed25519"
}
```

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

## 6. Behavioral Attestation Claim (BAC)

### 6.1 Purpose
The BAC is a short-lived (60-second TTL) signed assertion of an agent's current behavioral
state. It has no internet parallel, it exists because agents are non-deterministic.

### 6.2 Three Levels
- L1: build-time attestation (ATX + scan results).
- L2: runtime self-attestation (binary hash match).
- L3: behavioral continuity (drift score + anomaly state + intent verification).

### 6.3 Verification
BAC verification is local (< 2 ms). The receiver verifies the ML-DSA-65 signature against the
issuing Registry instance's public key.

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
All tokens include a unique identifier (`jti`). Receivers MUST track used identifiers for the
token's TTL window.

### 8.2 Post-Quantum Readiness
All signatures use hybrid Ed25519 + ML-DSA-65 (FIPS 204). Key exchange uses hybrid
X25519 + ML-KEM-768 (FIPS 203). The signature suite is a named, swappable field so suites can
be added or retired by negotiation, never by a new credential format.

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

## 9. IANA Considerations

This document requests registration of the `aap` scheme in the URI Schemes registry, and (via
the broker profile) the `grant` scheme. It further anticipates registries for AAP protocol
versions, CPI mode identifiers, and signature suite identifiers (coordinated with the ATX
suite registry).

## 10. References

### Normative References
- [RFC 2119] / [RFC 8174], Key words for requirement levels.
- [RFC 6749], The OAuth 2.0 Authorization Framework.
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
