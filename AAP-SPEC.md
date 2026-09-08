# Agent Authorization Protocol (AAP)

## Scoped, Attested Authorization for AI Agent Systems

**Version:** 0.5.0-draft
**Authors:** OpenA2A
**Date:** September 2026
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
[Secretless](https://github.com/opena2a-org/secretless-ai) (`src/broker/`, `src/grant/`): the
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

The CGT is an AAP token in the form of Section 9. The baseline claim set (the first ten
rows below) is **ratified byte-for-byte from the reference implementation**: it is exactly
what the Secretless broker's `mintBrokerAssertion` (`src/broker/cpi/assertion.ts`) signs.
The 0.5 members (`authorization_details`, `aap_crit`, `cnf`; Sections 4.4 to 4.6) are
specified here and pinned by generated fixtures; no implementation mints them as of
2026-09-08 (FGC program audit, section 2, "CGT claims minted: exactly 10, no cnf" and
"authorization_details / aap_crit / cnf: 0 in repo"). The claim set is pinned by
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
| `authorization_details` | MAY | array | RFC 9396 structured grant entries, typed by the registry of Section 4.4. Mandatory to understand: MUST be listed in `aap_crit` when present. Narrows within `scope` and `trust_class`, never widens them (Section 4.4). Not minted by any implementation as of 2026-09-08 (audit, section 2). |
| `aap_crit` | MAY | string array | The claim names a verifier MUST understand or reject the token (Section 4.5). |
| `cnf` | MAY | object | RFC 7800 confirmation: binds the token to the presenter's key (Section 4.6). Mandatory to understand: MUST be listed in `aap_crit` when present. |
| `fga_constraints` | MAY, **deprecated** | string | JSON-encoded FGA policy from the 0.3 and 0.4 text. Deprecated in 0.5, replacedBy `authorization_details`. Still optional-to-ignore (broker profile §8.3): a verifier ignores it. No implementation minted it (audit, section 2: 0 occurrences in the reference broker); it stays defined because the -00 and -01 Internet-Draft text and both reference verifiers carry it. |
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

### 4.4 Authorization details

The `authorization_details` claim is the RFC 9396 claim of the same name: an array of
objects, each with a REQUIRED `type` member naming an entry type from the registry in
Section 4.4.1, plus the members that type defines. It is the structured, fine grained form
of the grant. Where the 0.3 and 0.4 text reserved `fga_constraints` (a JSON encoded string
a verifier could ignore), 0.5 carries the same intent in a registered, structured claim
that a verifier cannot ignore: `authorization_details` is mandatory to understand and
MUST be named in `aap_crit` (Section 4.5) whenever it is present.

**Narrowing rule.** `scope` and `trust_class` stay REQUIRED so that foreign RFC 8693 and
OIDC style verifiers, which understand only the scope string, keep working. Within one
token, `authorization_details` MUST fall inside what `scope` and `trust_class` permit:
every entry's locations and actions MUST be ones the scope string already allows, and no
entry may name a capability outside the trust class. A verifier that understands
`authorization_details` enforces the intersection; a verifier that understands only
`scope` enforces `scope`; neither ever grants more than `scope` alone would. The minting
broker MUST reject a request whose requested entries would widen the scope.

**Producer rule.** A producer MUST NOT emit `authorization_details` (and therefore
`aap_crit`) toward a verifier that has not advertised support for them, because a
verifier without `aap_crit` support treats the token as an unconstrained baseline token.
Support is advertised in the broker discovery document (broker profile §8.5) and selected
by the negotiation of broker profile §8.1. As of 2026-09-08 neither reference verifier
implements `aap_crit` (audit, section 2: 0 occurrences in `aap-conformance`).

#### 4.4.1 Entry type registry

The initial registry has seven types. Member names inside an entry are camelCase
(Section 9.6); `type`, `locations`, `actions`, `datatypes`, `identifier`, and
`privileges` are the RFC 9396 common members and keep their registered spelling. Every
type that can carry data out of the session (`mcp_tool`, `peer_agent`, `model`, `network`,
and `data` with a write action) carries an `egressCeiling` member: a set of labels
(Section 4.4.2); when absent it is the empty set, which is default deny for any session
that has admitted a labeled field. Unless a member says otherwise, an absent set member
means "unbounded" and an absent identity member is not permitted.

| `type` | Members (MUST unless marked MAY) | Meaning |
|---|---|---|
| `mcp_tool` | `serverId` (DID or `sha256:` key fingerprint); `serverAtx` MAY (`sha256:` ATX reference); `tools` (array of tool names); `argumentConstraints` MAY (object keyed by tool name, value an object of argument name to constraint); `schemaHash` MAY (`sha256:` of the pinned tool schema); `egressCeiling` MAY | The MCP servers and tools the agent may call. This is also the declared server list: connecting to a server outside the grant is MCP drift. |
| `skill` | `identifier`; `version`; `contentHash` (`sha256:`) | A skill the agent may load, pinned to a version and content hash. |
| `peer_agent` | `peerDid` (DID); `direction` (array, one or both of `outbound`, `inbound`); `subDelegationDepth` (integer >= 0); `egressCeiling` MAY | A peer the agent may delegate to or accept delegation from, and how far the peer may delegate onward. |
| `model` | `endpoint` (URI or DID of the model endpoint); `models` MAY (array of model identifiers); `egressCeiling` MAY | The model endpoints the agent may send context to. |
| `network` | `destinations` (array of `host` or `host:port`; a leading `*.` matches subdomains); `tlsRequired` (boolean); `egressCeiling` MAY | The network destinations the agent may reach. |
| `data` | `locations`; `actions` (array; `read` and `list` are read actions, every other action is a write action); `fieldsAllowed` MAY (array of field paths); `fieldsDenied` MAY (array of field paths); `labelCeiling` MAY (set of labels; absent means the empty set); `egressCeiling` MAY (applies when `actions` contains a write action) | The data the agent may read or write, down to the field, and the highest labels it is cleared for. |
| `budget` | at least one of `spend` (`{"amount": decimal string, "currency": ISO 4217}`); `rate` (`{"max": integer, "windowSeconds": integer}`); `maxUses` (integer >= 1); `concurrency` (integer >= 1); `tokenCap` (`{"input": integer, "output": integer}`, either MAY be omitted) | The resource budget of the grant. A `budget` entry carries no data and has no egress ceiling. |

A verifier that meets an entry `type` it does not implement MUST reject the token: an
unknown type inside a mandatory to understand claim is not understood. New types are
added to this registry by a revision of this document; until an IANA registry exists
(Section 10) the registry is managed here.

#### 4.4.2 Label semantics (to be replaced by reference)

This subsection defines the label terms this document uses. The definitions are
placeholders for the label registry and definitions document of the FGC program, which
is not published as of 2026-09-08; a later revision replaces this subsection with a
citation and changes no rule.

- A **label** is an opaque string naming a sensitivity class (for example `internal`, a
  contact identifier class, or a residency class such as `residency:eu`). Labels are
  attached to fields by the data owner; this document does not define the vocabulary.
- A **label set** is a set of labels. Labels are sets, not levels: two fields can carry
  incomparable labels (a health record class and an EU residency class), and a session
  that has read both must be treated as carrying both. A total order would force one of
  them to be "higher" and would let the other one leak through the comparison.
- A field with label set L is **admissible under a ceiling** C only if L is a subset of C.
- The **session label** is the union of the label sets of every field admitted into the
  session so far. It only grows within a session (the broker profile's session high water
  mark). Session boundary: one CGT lifetime is one session; the session label starts
  empty when the CGT is minted and is discarded at `exp`.
- An entry with an **egress ceiling** E admits the session's data out only if the session
  label is a subset of E. The default E is the empty set, so a session that has admitted
  any labeled field is denied egress through an entry that carries no ceiling, while a
  session that has admitted only unlabeled fields is not.
- **Residency** is a label family (`residency:<region>`), so the three broker rules that
  govern a health record class also govern data that may not leave a region. This is the
  cross reference from the `jurisdiction` slot of broker profile §9.

### 4.5 Mandatory to understand claims

JWT has a `crit` header parameter for header members but no equivalent for claims. The
`aap_crit` claim closes that gap: it is an array of claim names that the verifier MUST
understand in order to accept the token. A verifier that encounters a name in `aap_crit`
that it does not implement MUST reject the token. A verifier MUST also reject a token
whose `aap_crit` names a claim that is not present in the token, and a token whose
`aap_crit` is present but empty. `aap_crit` MUST NOT name the baseline claims of
Section 4.2 (they are already required). `authorization_details` MUST be listed whenever
it is present. `cnf` MUST be listed whenever it is present, because a verifier that
ignores `cnf` accepts the token as a bearer token, which is the downgrade Section 4.6
exists to prevent. Every other claim is optional to ignore per broker profile §8.3.

### 4.6 Proof of possession

The `cnf` claim (RFC 7800) binds a CGT or DA to the presenter's key, so that a token
seen in transit is not a credential. `cnf` carries exactly one of `jwk` (RFC 7800 §3.2,
the public key itself) or `jkt` (the base64url SHA-256 JWK thumbprint of RFC 7638, as
registered for `cnf` by RFC 9449 §6.1). The bound key is the key the presentation binding
step of the broker profile (§6, step 3) verified: the ATX subject key where the ATX
carries one (ATX 2.0), or the key registered for the agent DID under AIP. The
presentation proof formats per binding are defined in the broker profile §6.8.

`cnf` is REQUIRED on every CGT or DA that is presented by an agent to any party other
than the broker that minted it (a network binding, a peer broker, a delegatee). On the
local unix socket binding, where the CGT never leaves the minting broker and the
presenter is bound by OS peer credentials, `cnf` MAY be omitted. A verifier that receives
a token with `cnf` MUST verify the presenter's proof against the bound key and MUST reject
the token otherwise. As of 2026-09-08 no implementation mints `cnf` and the reference
broker binds no presentation (audit, section 2: "CGT claims minted: exactly 10, no cnf";
broker profile 0.3 §6 verified the ATX and nothing about the presenter).

### 4.7 Example with authorization details

Example (generated; the Section 4.2 claim set plus one `data` entry, one `budget` entry,
`aap_crit`, and `cnf` bound to the published presenter test key `agent-key-1`):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImF1dGhvcml6YXRpb25fZGV0YWlscyI6W3sidHlwZSI6ImRhdGEiLCJsb2NhdGlvbnMiOlsiaHR0cHM6Ly9hcGkub3JkZXJzLmludGVybmFsL29yZGVycyJdLCJhY3Rpb25zIjpbInJlYWQiXSwiZmllbGRzQWxsb3dlZCI6WyJpZCIsInN0YXR1cyIsInRvdGFsIl0sImZpZWxkc0RlbmllZCI6WyJjdXN0b21lci5lbWFpbCJdLCJsYWJlbENlaWxpbmciOlsiaW50ZXJuYWwiXX0seyJ0eXBlIjoiYnVkZ2V0IiwibWF4VXNlcyI6MTAwLCJyYXRlIjp7Im1heCI6NjAsIndpbmRvd1NlY29uZHMiOjYwfX1dLCJhYXBfY3JpdCI6WyJhdXRob3JpemF0aW9uX2RldGFpbHMiLCJjbmYiXSwiY25mIjp7ImprdCI6IkhsSGdDY2pyaGJleXc4MFZNZWY1MXlQd2h5UnFqaXdMZHdTTFJxbzdoU0kifSwiaWF0IjoxNzgwMzE1MjAwLCJleHAiOjE3ODAzMTU1MDAsImp0aSI6ImMzZDRlNWY2YTdiODA5MWEyYjNjNGQ1ZTZmNzA4MTkyIn0.I26bq7dBZYSYdGA5i0c5w7mgPxjaRXe5RWOw7jWX3P4qWm-fHxDeXa33D_0_PeEggP_Mv8Ky01MMDfEFw3C2DA
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
  "authorization_details": [
    {
      "type": "data",
      "locations": ["https://api.orders.internal/orders"],
      "actions": ["read"],
      "fieldsAllowed": ["id", "status", "total"],
      "fieldsDenied": ["customer.email"],
      "labelCeiling": ["internal"]
    },
    {
      "type": "budget",
      "maxUses": 100,
      "rate": {"max": 60, "windowSeconds": 60}
    }
  ],
  "aap_crit": ["authorization_details", "cnf"],
  "cnf": {"jkt": "HlHgCcjrhbeyw80VMef51yPwhyRqjiwLdwSLRqo7hSI"},
  "iat": 1780315200,
  "exp": 1780315500,
  "jti": "c3d4e5f6a7b8091a2b3c4d5e6f708192"
}
```

The 0.5 members sit after the baseline members and before the validity window, so the
byte order of the baseline members is unchanged from the reference construction. The
presenter test key and its thumbprint are published in
[`examples/tokens/presenter-keys.json`](./examples/tokens/presenter-keys.json).

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
| `authorization_details` | MAY | array | As in §4.4, subject to the attenuation rule of §5.4. Mandatory to understand; listed in `aap_crit`. |
| `aap_crit` | MAY | string array | As in §4.5. |
| `cnf` | MAY | object | As in §4.6, bound to the **delegatee's** key: the delegatee is the presenter of a DA. |

The delegatee's `scope` and `trust_class` MUST be equal to or a subset of the
delegator's. The minting broker enforces subsetting at mint time; a verifier that can
resolve the delegator's grant MUST re-check it. The same holds for
`authorization_details` under the attenuation relation of §5.4.

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


### 5.4 Attenuation

Delegation attenuates: a DA can only carry less than the delegator's grant. For
`authorization_details` this is made mechanical by a **narrower than or equal to**
relation defined per entry type. An entry E' of the delegatee is narrower than or equal
to an entry E of the delegator (same `type`) when every member of E' is narrower than or
equal to the corresponding member of E under the member kind:

- **identity members** (`serverId`, `serverAtx`, `identifier`, `version`, `contentHash`,
  `schemaHash`, `peerDid`, `endpoint`): equal. A pinned hash in E must be the same hash in
  E'; E' MAY pin a hash E left open.
- **allow set members** (`locations`, `actions`, `datatypes`, `privileges`, `tools`,
  `models`, `destinations`, `direction`, `fieldsAllowed`, `labelCeiling`,
  `egressCeiling`): E' is a subset of E. An absent allow set in E means unbounded, except
  `labelCeiling` and `egressCeiling`, where absent means the empty set, so E' cannot name
  a label E did not carry. An absent allow set in E' inherits E's value.
- **deny set members** (`fieldsDenied`): E' is a superset of E. Absent means the empty
  set.
- **bound members** (`subDelegationDepth`, `maxUses`, `concurrency`, `rate.max`,
  `spend.amount` in the same currency, `tokenCap.input`, `tokenCap.output`): E' is less
  than or equal to E. `rate.windowSeconds` in E' is greater than or equal to E's for the
  same or a smaller `rate.max`. A bound absent in E means unbounded; a bound absent in
  E' inherits E's value. For `peer_agent`, `subDelegationDepth` in E' MUST additionally
  be strictly less than E's, since E' is one delegation deeper.
- **restriction flags** (`tlsRequired`): if E is `true`, E' MUST be `true`.
- **constraint objects** (`argumentConstraints`): every constraint E states for a tool and
  argument is present in E' with an equal or more restrictive value; E' MAY add
  constraints.

A DA is valid only if **every** entry in its `authorization_details` is narrower than or
equal to some entry of the same `type` in the delegator's `authorization_details`, and
**no entry lacks such a parent**. An orphan entry (a type or identity the delegator does
not hold) makes the DA invalid, whatever the rest of the token says. The delegatee's
array MAY hold fewer entries than the delegator's. When a DA chain is present (nested
`act`), the relation is checked link by link, each DA against its immediate delegator.
The minting broker MUST check the relation at mint time; a verifier that can resolve the
delegator's grant MUST re-check it; a verifier that cannot MUST NOT treat the DA as
carrying more than its own entries state.

### 5.5 Example of an attenuated delegation

Example (generated; `orders-reader` delegates to `reporting-bot` with fewer fields and a
smaller budget than the §4.7 grant, `cnf` bound to the delegatee's presenter key, which in
the fixtures is the same published test key):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL3JlcG9ydGluZy1ib3QiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImF1dGhvcml6YXRpb25fZGV0YWlscyI6W3sidHlwZSI6ImRhdGEiLCJsb2NhdGlvbnMiOlsiaHR0cHM6Ly9hcGkub3JkZXJzLmludGVybmFsL29yZGVycyJdLCJhY3Rpb25zIjpbInJlYWQiXSwiZmllbGRzQWxsb3dlZCI6WyJpZCIsInN0YXR1cyJdLCJmaWVsZHNEZW5pZWQiOlsiY3VzdG9tZXIuZW1haWwiXSwibGFiZWxDZWlsaW5nIjpbImludGVybmFsIl19LHsidHlwZSI6ImJ1ZGdldCIsIm1heFVzZXMiOjEwLCJyYXRlIjp7Im1heCI6MTAsIndpbmRvd1NlY29uZHMiOjYwfX1dLCJhYXBfY3JpdCI6WyJhdXRob3JpemF0aW9uX2RldGFpbHMiLCJjbmYiXSwiY25mIjp7ImprdCI6IkhsSGdDY2pyaGJleXc4MFZNZWY1MXlQd2h5UnFqaXdMZHdTTFJxbzdoU0kifSwiYWN0Ijp7InN1YiI6ImRpZDpvcGVuYTJhOmFnZW50OmFjbWUvb3JkZXJzLXJlYWRlciJ9LCJtYXhfZGVwdGgiOjEsImRlbGVnYXRvcl9hdHgiOiJzaGEyNTY6MjA1Mjg3OWRkYTE1YjFjYTVlNjAzMTllMzQ3N2E0MDA4NDEyYmZmZGFmM2MzNTY2YzY1ODc5NWE0OGNhYjhmZCIsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiJkNGU1ZjZhN2I4YzkwMTJiM2M0ZDVlNmY3MDgxOTIwMyJ9.dITVeSEbF66f47VAt6oFjLHwLsDYpe2jz_7j8rTs0p2DH3wIAYdpEeHAo_qWpeOimjeib4dW3RvYRi77yR3UAQ
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
  "authorization_details": [
    {
      "type": "data",
      "locations": ["https://api.orders.internal/orders"],
      "actions": ["read"],
      "fieldsAllowed": ["id", "status"],
      "fieldsDenied": ["customer.email"],
      "labelCeiling": ["internal"]
    },
    {
      "type": "budget",
      "maxUses": 10,
      "rate": {"max": 10, "windowSeconds": 60}
    }
  ],
  "aap_crit": ["authorization_details", "cnf"],
  "cnf": {"jkt": "HlHgCcjrhbeyw80VMef51yPwhyRqjiwLdwSLRqo7hSI"},
  "act": {"sub": "did:opena2a:agent:acme/orders-reader"},
  "max_depth": 1,
  "delegator_atx": "sha256:2052879dda15b1ca5e60319e3477a4008412bffdaf3c3566c658795a48cab8fd",
  "iat": 1780315200,
  "exp": 1780315500,
  "jti": "d4e5f6a7b8c9012b3c4d5e6f70819203"
}
```

Against the §4.7 grant: `fieldsAllowed` is a subset, `fieldsDenied` is equal,
`labelCeiling` is equal, `maxUses` and `rate.max` are smaller over the same window, and
both entries have a parent of the same type. Removing the `data` entry from the delegator
and leaving it in the delegatee would make the entry an orphan and the DA invalid.

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
- L3: behavioral continuity (drift score + anomaly state + intent verification), and,
  from 0.5, the session label (§6.4): the set of data labels the session has admitted.

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
| `session_label` | L3 only; MUST when the issuer holds a session high water mark for the subject (broker profile §6.10) | string array (a set) | The union of the label sets of every field admitted into the session so far (§4.4.2). MUST NOT appear at L1 or L2. Labels are a set, not a level. |
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

### 6.5 Example with a session label

Example (generated; the same L3 attestation for a session that has admitted one
`internal` labeled field; the sixty second window is unchanged):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6InJlZ2lzdHJ5LWtleS0xIn0.eyJpc3MiOiJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJiYWNfbGV2ZWwiOjMsImF0eF9yZWZlcmVuY2UiOiJzaGEyNTY6MjA1Mjg3OWRkYTE1YjFjYTVlNjAzMTllMzQ3N2E0MDA4NDEyYmZmZGFmM2MzNTY2YzY1ODc5NWE0OGNhYjhmZCIsImJpbmFyeV9oYXNoIjoic2hhMjU2OjQ3OWJkMjhhNTVlM2EzZWIyMGI5ZjViNDgyMDIzMThkNWRlOWQwZGJlYTllNmRmMjBiMmVlN2ZmOTVhNGMxMzUiLCJkcmlmdF9zY29yZSI6MC4wNCwiYW5vbWFseV9zdGF0ZSI6Im5vbWluYWwiLCJpbnRlbnRfdmVyaWZpZWQiOnRydWUsInNlc3Npb25fbGFiZWwiOlsiaW50ZXJuYWwiXSwiaWF0IjoxNzgwMzE1MjAwLCJleHAiOjE3ODAzMTUyNjAsImp0aSI6ImU1ZjZhN2I4YzlkMDEyM2M0ZDVlNmY3MDgxOTIwMzE0In0.IIEDb6Im_NyKUFwQUQmI1CvRHZyGRLEidvsloYeFwp9ukW3zwqOouTbqF3x8eI6UnEoLCaU3liJMZmBHjpomAA
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
  "session_label": ["internal"],
  "iat": 1780315200,
  "exp": 1780315260,
  "jti": "e5f6a7b8c9d0123c4d5e6f7081920314"
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
60 seconds via signed push. No member needs to poll. Revoking an agent's ATX revokes
every grant minted for it within the propagation window. Revoking a single grant
without revoking the agent is the local list of §7.3; it is not federated.

### 7.3 Grant revocation list

Before 0.5 the only way to kill a compromised grant, a leaked delegation, or a grant
made obsolete by a policy change was to revoke the whole agent's ATX. From 0.5 a broker
MUST maintain a **grant revocation list**, local to the operator, keyed by two things:

- **`jti`**: the identifier of a CGT or DA. Listing a `jti` revokes that token.
- **`sub`**: an agent DID. Listing a subject revokes every CGT and DA minted for it by
  this broker, current and future, until the entry is removed.

A revocation **cascades through delegation chains by the delegator's `jti`**: listing a
CGT's `jti` also revokes every DA whose chain leads back to it, and listing a DA's `jti`
revokes every DA delegated from it. A verifier resolves the chain through the `act`
members and the delegator grants it can resolve; a DA whose delegator grant is listed is
revoked even when its own `jti` is not.

The list MUST be checked at **every** resolution (broker profile §6, step 5), after the
ATX and CRL checks and before policy evaluation, and a listed token MUST produce the
opaque denial of broker profile §6.6. The list is local: it never leaves the operator, is
never fetched from a hosted service, and needs no federation transport. That is what
keeps it inside Zero Failures. An entry MAY carry an expiry no earlier than the revoked
token's `exp` (a `jti` entry is useless after that) and a subject entry has no implicit
expiry. As of 2026-09-08 no implementation maintains a grant revocation list: the
broker profile 0.3 §6 step 2 bound revocation "entirely" to the ATX CRL, and the audit's
reference broker rows (audit, section 2) record no grant revocation surface.

## 8. Security Considerations

### 8.1 Replay Prevention
All tokens include a unique identifier (`jti`): 16 random bytes, lowercase hex (32
characters), as minted by the reference implementation. Receivers MUST track used
identifiers for the token's TTL window and MUST reject a repeated identifier. The
reference verifiers enforce this (conformance category `REPLAYED_JTI`): a jti is
remembered from first acceptance until the token's `exp`, and a second presentation
inside that window rejects, after all other checks pass.

### 8.2 Cryptographic Agility and Post-Quantum Readiness
The signature suite is a named, swappable field — the JOSE `alg` of each signature's
protected header (Section 9) — so suites can be added or retired by negotiation, never by
a new credential format. A verifier MUST reject a token whose declared suite it does not
support rather than silently downgrade. Suite acceptance is pinned by verifier policy per
path, never selected by the token; a producer configured for the hybrid profile on a path
MUST NOT fall back to a classical-only token on that path except through explicit version
negotiation (broker profile §8.1).

The v1 suite registry (Section 9.5) contains two active entries: `EdDSA` (Ed25519,
RFC 8037) and `ML-DSA-65` (FIPS 204; JOSE `alg` identifier and `AKP` key type registered
by RFC 9964, May 2026). The post-quantum profile is hybrid Ed25519 + ML-DSA-65, carried
as two `signatures[]` entries of the multi-signature form (Section 9.4) — one per suite,
matching ATX's per-signature `algorithm` model: a hybrid token verifies only if at least
one ML-DSA-65 signature **and** at least one Ed25519 signature verify, with every declared
entry verifying (Section 9.4). Hybrid is the RECOMMENDED form wherever both ends implement
AAP; single-suite compact tokens remain the interoperability baseline (Section 9.3).
ML-DSA-65 signing uses the empty context string and no pre-hash variant, as RFC 9964
requires. Key exchange, where AAP deployments negotiate transport keys, targets hybrid
X25519 + ML-KEM-768 (FIPS 203); ML-KEM has no final JOSE registration yet, so that row
remains reserved on the same adoption path this section previously applied to ML-DSA-65.

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

### 8.6 Presentation is not possession

An ATX proves what was attested about a build, not that the presenter is that agent, and
a CGT or DA without `cnf` proves only that someone holds the bytes. Before 0.5 every
presentation in AAP was bearer: the broker verified the ATX and nothing about the
presenter. 0.5 adds the presentation binding step of the broker profile (§6, step 3, and
§6.8) and the `cnf` claim (§4.6). A deployment that accepts an ATX or a CGT over a
network binding without the binding step accepts a badge, and MUST NOT claim conformance
to the broker profile. The A2A agent card publishes the ATX to the world; that is by
design, and it is why possession must be proven separately.

### 8.7 A constraint a verifier may ignore is not a constraint

The 0.3 and 0.4 text reserved `fga_constraints` as optional to ignore. A downstream that
does not understand it treats the grant as unconstrained, so the claim could never be
relied on. 0.5 deprecates it (§4.2) and moves the constraint into
`authorization_details`, which `aap_crit` makes mandatory to understand (§4.5). The
residual hazard is a legacy verifier that ignores `aap_crit` itself; the producer rule of
§4.4 (never emit toward a verifier that has not advertised support) is the only control
until every verifier on a path implements 0.5, and deployments MUST treat a path with a
legacy verifier as a bearer, unconstrained path.

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

The suite of a compact token is pinned per path by verifier policy (§8.2). `EdDSA` is the
v1 interoperability baseline; an `ML-DSA-65` compact token is the PQ-interop form, minted
where the counterparty advertises support for the RFC 9964 suites. During the current
adoption window the RECOMMENDED default on foreign-interop paths remains `EdDSA` —
deployed RFC 8693/OIDC verifiers do not yet verify RFC 9964 suites; the re-evaluation
triggers are recorded in
[`decisions/2026-07-16-mldsa65-serialization-profile.md`](./decisions/2026-07-16-mldsa65-serialization-profile.md).
Example (generated; the §4.2 CGT claim shape with its own `jti`, signed `ML-DSA-65` under
test key `broker-pqc-1`):

```
eyJhbGciOiJNTC1EU0EtNjUiLCJ0eXAiOiJKV1QiLCJraWQiOiJicm9rZXItcHFjLTEifQ.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiJiMWMyZDNlNGY1YTYwNzE4MjkzYTRiNWM2ZDdlOGY5MCJ9.9vagfB_BNqu_Yk-Sh8muBWLdHvgguw1XheApS2LEmj7ZUWERjxxNtsyXESMFcFd2zzCtCtaS74FCMZtjEWCO3s1vemtsqbk-BOtHBEemovDMTMvW_7YCZ8_qlDLYj0XbW3If8lYpy5JIpdLRO_Cuqh1KMmLJv8G2znNUUiZIwpyAVSAlpG0sMh_Ue_qEV4CArWStBhMGouh5RBKol9UUiitomcaIInMHmZyDSWyeW3IZFMpUTSSjO3QemOHv6sF4TXs-IfdfcfgjLAhH4L8WLfDKslaxD1qlG3OIQJiZBWu-YmylDbSuRiRKBvlCl_Nq4fD44NdxK8oNZnYrK1ZDO-cUZCZHdldUY8up-6l7yG8nlbzpwk5YjQZFgWvUseg5bH3a7Nmwsh0cCPObdHMU-g0uHBw687MzPB9OlEI8X-Yfm0U13SQ7s0OtdvwYz0PtcFOqcZpBtI0DNfmqR44aOSjQkvlzuuZHH7CFPPzgG3y1VItBl4exw_Uh9wkxTxwzTJIloR_OSAjU-FgJi0dAx6aaUEJbTyKtNnteS3TVzG_cMO-UYKAsTzpaK8zddPaSMadPZycHAOnk-ZbUV1SZVbaX80M1ZFLJ8lhPzjs2XEd3XCY0ipvA-O6G9Hrm67gEJCpnka7u0uUBDHTGlgu-BNI_JS11NmyOb58kshaaoh5FAAEa-249VUSa17uzcZV8hl4GaZmfn2zDnj1-rnXAqtZSNoHiPB1pTCkw5ow2Ljrt8FlIR4cXh19JFy2lrh6_4jWQXng9D0Y9xh42nrI9kSLV09spoVFKSNNAAKf5rdR7W0LMje3YGFWp_DZHQv9Mt_KtvWO-ZsRbAeZ7l6YSsmqiX0fjAcxQmVhfykea787dwVQgpy-nOzSyhe-_QuqdfdYco1MIWSgdpFmRyQsMzN0AWRT1Y2KOcU7zqfg2xH6TyVSMyuvU3J9KhkPuhHaItaWgntdcvnyG3ioKlJfucKA3_5qNZoKIiAe73aNZQUE0TnTdIX-I1f--Y9LT8EbDtSVx1RahCBmJwGRvYaC0TYQXO86AmGUTGRnWqaBNX7Bd9QgTVR_jtVSmJ7MCelP50zdm-ODeHqoqT3e_VC-K7ouesTuDvCqBvpgBvTlntr4p3L3jr_QgtCWtA23rk0WmEN3XWswjEyzvhI6nRO7Z6FUGlW80OuDmd9wBHeWoxo08U937XTogvljbWp546dZz-EvGc6YKQrlwLIpKHA1Sj7xlWqr4FrXDZJvwWGuxP2q44qpEzw8M8uShNInadKE4GBJcQ3QYkQQRCgJ-kSD01sZJRmxur2mX6xfxdNu9SdedgVwTne0iIK0JYO7BWAeTBYADIHvC-IWKatsmmAD4C_61y829DhLMIVcGD3fb2dqmYUy-eKZvys76gHtKlo0Ko3r1-XnlGxevTruI8GLIZKmf9tITiWu2jFXnCtfiYExT3hgDT-D7F27BYyHIB7bRWuZCTZAbCt0KdASdyKodcuYCVoLdd9lni7hNAJt4gmAkn3Bimz4Pl3QbF8QwJn8Fdg3PSr4MQ4CJAV_kAjrPdUQT8DZ1H4iHxptFkTUfvVnsKktWXcAQsaPbsu3d_0s8GayF1XZAjmzdvq3WrjP3sNXgm-Zq0O3Tu5-yAZxvScYOUq-HP6nJFaeysRYg36Hbao6-LKZxIiNjO3z8cN8OjPXFW6xiwAj2Wyf_yphcF3Il7eEq8EZxZqD8pt86pRybXK7s38rEQBDnXc1X1mnrm1cRjDj-NmPqODDgXijG9z89QqznsQdtHUZJz4JiwAkYUhVFjrvL5SyEd29z89-YAnOv6y4TrxdcdXg73_ohQRVwMij_y9W50wzAwH_aniySuEA06T4j8AvUntA8HT2QWpGhPpJbWYwwXAxrsS8jub8F3naMIDYN0RNjbZmnjTe2j4zPUsz-U8ZCQcarIJlM9gvK6lU33QtVtJOMTP4IIhMte6XjOnAjC63bs2Rf0yWq3qLSRKcDcLYtMhlwxMEupFcXAvWaOL6g428eq4Md-frCiC8pqe1YNdc_MJhV_bU2wSXLg0FyPdyRUWfQcQ1K3-IVetXU63jIjjeOLlwC8fvJAs3QKuk1YOisZiR4vK8L2HKZZZegoK87YYtf7rvlIEYcRmHEhWDMkHk6Z4rTn-ACaB4gRNzmaJTahxetEGR3JtohQ0BmlmyF7huPdT_yGHQ2XPrFHbS6ZfXvclTBKdFcqtNrr6mpLpk0DII5lElgvd_QXYXlsbgPVoPGrkAeoB_T1OS4E_kdRL7El-h6aP6hpIWOi3KXmHBJjoINA94L03gjB02G1zyB3MBpJ7r0tlafDLCjVBLgPCS_XBSDmSTRIX4tlIYTeweoVo0yEmEMHPlDffRLJisQQ7Mp02oaXxY90mgNUI5WM8TRw9ed_jyK1Qd56CiXRuBXjMIEJmsA_0HxqRpXZxLkUy1bUiZkqKOzaInzeNQwzq_EA6JivQP2wOV3XDnKL8C0xLww0lHN_esQCsO1UlVnLlDNPk1_LbiPNZ_YiDSQvWU4qU2rYYDwgHBj7PzvOtX6tH8Uhk4b7PlWfSkKAUW9cEIXvysdiWU8DeLX4SoGRbpxTeiKeb1SMiEXwbnuTboWulU9j73haUmT7joS1IivQXZUjfcXgi-GSKFFSMaYI1QXnRINfkGJ0o2TMNbml9rr-ukvih6jGCsG1yviauDIkcqTHrrHByZ7IAdPhLWE7-9YJeW8rnb4J7goH_mrMTTyjDc9UAoLf4PQj9ucCIzXzad5DtYrMhpW6gzZxuDUOc2RNSD7D5OAkoqdlChmYt5fnbueiCjKZFJUcwzx3k6sLwdAJqXyw_pRlUFK6tEozrObvSUxveXyyFeAfj8oouDiMCgUtjR01MkIFbrVilGnGPJO2om2Cuvp2rdN4Oj-n4z59O7u8PRxXLpb-2LJRDKu64HmqE_BM-e6YK6SJthm-9kw7t788rNR5yDKifQ4cV-LdQhXeL6-2H3jfQ085z91qSm48oZyiw0voQTCvjYNe-RIkvfV2gHXw5RWLeagNPTC4nTQYQ9E09Sc1VqdVwxRg2ecnYdSoP2RI-9uWxrF5-ShJ_NMasW1nwV_tsq-zTZbCBEUcGBKQYKORHIdw1na9eDBdmMJnEhzX34B53TogeGV5xO-JJoNbNTjjPlqhBf5E9V2Pz4EFicvlVVPw1P5KkQjsSNf8hfPel6Hqqm1eNNxsfMfXZa4fZBV8s3MFHruc7D0mXPyhdLRPMs8tgXuGXASuVGsb0HA4AKTcaZCFOgqASnC7NF7diCr7SYOvpmgtzCbeODKM94Z_BfW5nWmvJRlzEppr2l2DOAm3UZSTqqZenqR2bdHHGniJOEQ4U2z0GxoQXEOMpGzi6hQN01iE13_lGXPZ3iELUF6S1eC2VsVXpkNZP7xNCVxWN_gMtFqi4z98tMMf2pz5D0cAJlWTYvJ9Crj44zqBTb30TFJecc7Vwo6oFvrkcPnyWnzzRCh2Y9mCntkYu7bQ9L9qaSuREWlRqjksBW4swjhvrXNGiziQiICdxpMtlGpC_poPGrUE9zpRqVnXbT3xfwEJze9BzUrXh6RJTir-0AmWPo8NGqYwl8O0y7_IAwrl51cuEQANVRQ0wI-2hiJLlbLdzm1S4Bf5mRmkko8QK3mKxQl7NUpjPmE_KlvqUmhw4ubEOpwIoqJm_eRICBNTvCPfh4vZnxjtAcUcBabPs96XKMhapGG4_jP7vzVLW-7dDogOMCIiXIKVDe7X9PqK0ly-bUOdPLqzsWvrk9x7awm0sHstX-LE3jsY-b41WnS6-m9reLFFVeeIDx36-cMR36pSFOfew6FMcMUb8moeIoDNLRuTCeTGvu53e7jLH2nrw-6vMK_0U1JPPb7ESXa5Oh--SfJKy4aqK8XC-07tSisvcgF5ryoknpFxv7PF8SPu0lDEbySpdD0msGjRinpv8zaP6pYqFjLF7f72sAjkIcpJCeCpuwuQK1imxv7Ak3n0q3eqVSBbOZmc0XvEaIEXZ7zVtLqKM_LJbjDcGucVzcvHzsRCee0TYaq-1vgiaSfAD3nsJ0KUDcbmet6RfwqgQicj4norwQjWGOIe3ZIP85JCwn0952Fac3zoTlkzZvwkS2_0MyFf6o-Of68YqqjWoFZfaXEeky6vOELkg2_OlQmfd3ua1NsHYOq9LMZMrtknqqSS2puHFPuZhatUOh9GA76mg8VgxPDoKYSM6x-wyF-wYCqsnvqoxwmhgnObBeERwEK63Whoh-6Ti383SuVEpol1CX4i4hFtRYdhOaIHe3gvn93Y9suhMpEWUIUXTBUrbZ2hXTg6622sIkEjQALSHd9ws_5_Sg9SUuTl5y51dfaPJK4vMTVMzeu6hbI1t7vAAAAAAAAAAAAAAAAAAAAAAAAAgsWHCAl
```

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

A general-form token that declares any `ML-DSA-65` entry is on the hybrid profile of
§8.2 and MUST carry at least one `EdDSA` entry and at least one `ML-DSA-65` entry; a
verifier MUST reject a general-form token missing either family (conformance category
`HYBRID_INCOMPLETE`). Together with the subset rule above, this means a stripped hybrid
token can never degrade to single-family acceptance. Multiple entries of one suite with
no `ML-DSA-65` entry remain a legal multi-signature (co-signature) form, published as
[`examples/tokens/cgt-v1.general.json`](./examples/tokens/cgt-v1.general.json).

Example (generated; the §4.2 CGT claim set under the hybrid profile — one `EdDSA` entry
and one `ML-DSA-65` entry over the same payload):

```json
{
  "payload": "eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJvcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiI5ZjhlN2Q2YzViNGEzOTI4MTcwNmY1ZTRkM2MyYjFhMCJ9",
  "signatures": [
    {
      "protected": "eyJhbGciOiJFZERTQSIsImtpZCI6ImJyb2tlci1rZXktMSJ9",
      "signature": "7-kf_vmchx-P6zg-CsSIQvYdPHQaObrQSIngnI7HpL1D5l544iGTg8jIOxpNf0g0KoBRNVr2vJ5Gj3fjRwtoAg"
    },
    {
      "protected": "eyJhbGciOiJNTC1EU0EtNjUiLCJraWQiOiJicm9rZXItcHFjLTEifQ",
      "signature": "njv38RRBZbBspeTyiXRwJrLVtflKX4_nViYaJLMNhZN00omEy763sbXTbgZK8cTkFlyyfh7Io4o0kf-LzPeSufxepcCUuDGxdTa62xZ94A1IRrmCUuT1Gggh_z5k0TbMDJo3XcYjbvEmy8nsn_zH5vbm7En8bDQRKPC0Sws0q6M4572KUJiKuMvjmkLWBm5zgYnQalBtfSAjcURECSGOsai0TlVYGXNzJ6RCDsNlMjrqKhKHNEKZLknwvB6fDISbEKoRS2tG5mKACbKOw-SrZuKcVOeGXpZa3bKriNfibppqj1SRbR-KKiTyXfm4BLRWUKAkYPffUCy6pZ7xxh0psjPLpGGIA1dkYQnHwaoKIiBnoEzjY1blT1UrV2k-hbd5YPB-nVIq-6SN9zkct0FmgXUxwIwMOXcE_FM3kYaGIuTNPxVppKmdfqW6H1V4iIHoYyMVaPr0z1elR8c6kbVIswnhFL7-YyHfJMr9mJYK7SzI_C2bSznlvn3OtoWn0evbkiajtmXPdzClZE7RsRMFBs2ecDTj09b9HGloPuOucCKJHtAnSHjVC7wPBteq94adnkxnGmp5zLQQPXzs6wiyZMnwPVOZ06Bv-pTVJmosutWWZp9aActNW1LBb6qcvvAVPuheFMrW4mWpy63vMrUbtbD-hNGExtywAlsGTMXsJdNH2u7XYabHhkduArKJaNh4HD8jZtbORPuQTJuJ-3ju6pl8cbeUQXAllIAQSjWg2QZtyMHef-wKcbYJeGV8cnrjdAExvv4QnVtJdUlxszu2OwDUErzjqDQunwKgJgs76SIDfSoTF4hLEIAmYRaJSFRhDH0FmMb-sBp71p5B5qGMSRfjauahOMNmYDECmJ4KLkLm4UMYZCW-4eSWZFdd5WkzJXcNmr3L6jpxLuIbmqytSJnGi6BFLDajdH5XkY6bfJhhBLqzkDirukktJzIZxJU9PSRMPkjWcmvhHIHAZGyeAfmaQXcTKNd4LCLo-2YyVfHhdK_ywZKRSG2i8jJ3Mgphirgev3aKp1R1Z7DjaRojH8F2cYqUH_lJ_yREJ6kqex5nspWXVLO4FYlbeeZAiuokk8GOs3MLGCb-mI4hkP_11KZKgBEmY1IIVvW-c8T7r4bKuFVL2jz5khINxeLqxvwn6zgSbZZgeg-5Oh85sH275MXoUIlBWmAeHPd2tS-EEcI9E_IX4_YbMaizH91gZv7ut-5lYtthrdSDW6UGJy-e6yqc5leRs6lqKT77chLSJgquPJj56WC-l8uFgTn7njoUzge5dNeXwJGd6H2CnRmOG_wmycepaanANLV58sWVNhAo4RwoMjlD2v7hFeO9UL15D7WtAs4pCytI5wnbaK2tDt3riTMVLQAeujEJ6YRn-5r7wK5Owz8Esyqh1e87khaxil0p6yNzcun5hVuyX7yGI8hFZ4iqKPD9txRhn8qn6YFeFerSaLpyQvTVDi6oQMr9yh9011zdqrAJH4R3fvy8zo-Oha_1ky8AYR-becD8lc5pcKg1NbCJ15hTWs3bDQpK_TYu5G4sN-UTO2CbEFEs_WFkxhviAQDkamKWS5u2kQDAoTWyLABIZlznS0_i7i1pRuLLO3nssAXxAJWO1iC3vvKwjb1Q6n_vEpC4EUeXbkFGaj8Eo3mtxZUTPve0cHeYVV6waCRSngxTW29X9bEzSDUv15mGrwlbWRhi-DvbeN7FqYqhMpV-4uAMwoVwehCyzvWXTD3mv-i57OmqymcYTjLmO4pZr6JGDRhhFYbrV4wF4_SfZRcwJ93ZblFaum6cPdmlg2BKmxZsDhtio8M88K945Qi-BlcJrd6dlf1ZUd9CUWIozP0o_UrFk34n15DWeJjK4BMV8bH7Mjfg5kEJfPmF58TifkxkZiyER5m1meNYiSBNKfPhJNCZDWC-MuGKGBF5Yc9alSOGtk20-703d6c8vyns2DDEnu4G7kPsqfoAJeX_qj3jRoDzCfS8oeOAltkO_FVTK_igsEt4i8NhIkhyZv4E47Cfdkn4dR9XWJEueT8_kyThpYH0imc-79ITJPqz4dSKqUGkYRg_ADUGq6IzmR0b0QZSK406LZUYw_NDA8txGTDZhOWwTvX8A37ywlWOWNXgoQ3mG9UJB54lYqma0g0MVKh23WgcOhQ0cVPDd4jThu__teN2NJN3-Ae6bfFQT5BnXksJazmDXd0B7rEMSWJXnnG63cGr6ghMrk19uLrSxbyTAbIfuBmxghBSZeO05nknK2S6pPQfelx6gRIqYrZT-LID9nhGEigb5P-9bNPY9Jrf13-s-VXWYEsD7nGTQ0arh0rLBGD2l6g7N32SMyDvOFlUIXsUOWO7ZMhlE0LuI5WB0ElC_tGwydSrBKNZfQRD5D1IWjnTV2GdB-9R_p1QlIKz0mUYkQh-dve3nJcZ3BcKtsffniIcGkmeh040M8K4a51GKYyrP_IVQeHHhKK62RMAO0-7Pm4lUkLxWf-wmVLc4UUizDDfEYUw5VR2OJn3E01PSp5gXHyntBiArrbzlG7WGuQydAmTwSN15NSU21wQrwR3xzPiOLmY4rx0pqWD8BtZ2F9Td5pbN6QUZE3tyJrH670RNeMRU42_FpHYiaQ7-fOt9t14wZ-dZGx8N7Ac7FA3sMzf_bheahzHYGS2YVAUCX8mC8nW7iXEEybMVXb9KgJRqu9Q72g1rwEul276h4pgkGh46OmNRK3Z6lPKj8JGeoocvkBG6UTwrtqsKgNP7PhWb4P4C3ZTSyUthDWdk8o0IL7R2IPjRnd5m1GLnkrWqW4JgSyhJLhQAPxeqrmy20M1lLg_5t_1BpQykjzI44UZ7qlZLgPlywfjtsXmAhkknMe2FnLHs2Edd7IxM_tYFlptHB1UYWrnJP9StsNJ6a4I53Y-jhMW3mim4gMqWNqkpq1xDRF8v2HMLubyzhE9XtIwaNnXgzWL9zXvjE5w3EX7Q8vmmSFhobxFigX1XobJaE4L6_4IYn64SpqLQYACHPutdvV_03LSOss3VdYMlkJ1cryifzfvC9bxiGF0x5MJH0GZ0JGewjlLNQPWuix2xsh464Eeuz3vfbaFxRhfAzhotoF2IIFSJRFT2FAz1yvecIofjpNExNrm8g0ZconEfzr7g6wAcR80oMLBSSD4FiAFBdeGHGa308I2pbtkG4Tl6u-UPPa3QU0U2nWkBmrExNN2hHarkMYTXrNoStqgX7xS4Hivd-zjz4tDuzlcYkN7jee2fQByqJb9AG1UMAQG5U8hBwZW6FG0hK3h6i0NHsZF8_DkXTVCH-2Af8-weLl0nF_ZImYlLSQUoacUm3zQhXbmfw5r2INL5sUJNfq3fkdvwax94XDOv-bGOV5oP7YCFliUlbQJJzzaJa5yIJUa2vLwVts6iXE5dt7WR7M93yzXGJAaOzpFekUdAdT8Ey20xhrv_j_efNlUjC_biySOC748WJ7R98HnKiqenu-wSv_-sBckra7_U2ua_pdI028lekqfUWFsX4ZEB9FNnjqO3O0sQoxPfgaVnskAoMzBfRbtchFafzgAY_31y_3hMsYsSF3eeyRz4rqnfgo-k8mJjCn8bV7rlxxBxpHV1Nkc_e-CDaHkH3ndf2zksv2ZbjRWcUuL4Aq8s7bqukYDsGkv0pzeO7xClMDHP-7JB6FbPytWb8NhjFazEjOBAmD0PpUr3BTbNdFPzMEhK1rexiA2fNUymtpliRgaDYFhr2JVVoIM3x2nu60RTOWJcT4Rwfda1cHnnfpERTShO30QZ5aDtPDBKn6xZIgYBQulg7zIbWYRVLsQaM1J8mZXs4F83v26rksO6FuVlRUgAnt116w9ZAziLRXamHIU9OidtcoSmFI6RKPIF9Ehd3epcEuYW5m8PpOeKIWQVEYdxT5IB5PvyKcvwR-08kD6cE0iW3VwBm7V_sQOmdpIKCXh1B0liCE3xgtyCkmgfk2NyWvV7qIEiUyyVBMEmeXDr3z0QC9Glh3Z0W4zemZKg3OVEmxeKewIX4bmPt40JYsqOirnHxVPbr5eNKeihXVC7Rt6j_VOagCPt8BazlNjt194DGf6e9QIl1El-GOcAQaa97pezSMLddMOw9qlVSuA6ZijA5F-lzZDNzIHJmI9OHJFg2m2gkMl04DE0gnCZAUJpcH933nkFRfAZZl5DbsYKytP68gqOczmBjY758vfGDLl6AB1za_I-Xsaq0O5BOmCRjS82CBL8uR8aGJhR6QTW-7Pt4mtwc8BB1ew8wgH6etx7FOrl2CkLvR08h4e3utquF2RAdPybCxj4yKUkCy-C3PoPz9kqcMDWT6KuChidMWAP4Yjar_MZvgB4rD9Ad4CWn-gqvSQtd7rMmyVqrvD2ug6O1mr1OQNH3LC0AYILWlrgO77AAAAAAAAAAAAAAAAAAAAAAAABgoSGB0l"
    }
  ]
}
```

### 9.5 Suite Registry (v1)

| `alg` | Algorithm | Status |
|---|---|---|
| `EdDSA` | Ed25519 (RFC 8032 / RFC 8037) | Active. The v1 interoperability baseline. |
| `ML-DSA-65` | FIPS 204 (JOSE registration: RFC 9964) | Active since 2026-07-16 ([decision note](./decisions/2026-07-16-mldsa65-serialization-profile.md)). Hybrid with `EdDSA` per §8.2/§9.4; PQ-interop compact per §9.3. |

ML-DSA-65 verification keys publish as RFC 9964 `AKP` JWKs (`pub` per FIPS 204 §5.3;
a private JWK, where one exists at all, carries the 32-byte seed as `priv`). `ML-DSA-44`
and `ML-DSA-87`, though registered for JOSE by RFC 9964, are NOT in the AAP registry;
a verifier rejects them as unknown suites (§8.2).

Adding or retiring a suite is a row change here plus version negotiation (broker profile
§8.1) — never a format change.

### 9.6 Claim Conventions

- Claim names use the JWT registry convention (lowercase, snake_case for compound
  names: `trust_class`, `issuer_chain`), matching RFC 7519/8693/9068 practice. This is a
  deliberate, documented exception to the OpenA2A camelCase JSON convention, which
  governs API responses, not IETF-track token claims.
- `iat`/`exp` are NumericDate (seconds since epoch, RFC 7519 §2) — not ISO 8601 strings.
- Claims registered by another RFC keep their registered spelling (`authorization_details`
  from RFC 9396, `cnf` from RFC 7800, `act` from RFC 8693). Members **inside** an
  `authorization_details` entry that this document defines are camelCase
  (`fieldsAllowed`, `labelCeiling`, `egressCeiling`), because they are AAP structures,
  not JWT claims; the RFC 9396 common members (`type`, `locations`, `actions`,
  `datatypes`, `identifier`, `privileges`) keep their registered spelling.
- Unknown claims follow §8.3: optional-to-ignore unless named in `aap_crit` (§4.5),
  which is how a claim is marked mandatory-to-understand in an AAP token.
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
fixture. Hand-authored example bytes are prohibited. ML-DSA-65 fixtures use the FIPS 204
deterministic signing variant with the empty context string — hedged signing would break
byte-reproducibility; production minting MAY hedge (§8.2), verification is identical
either way. The ML-DSA-65 test key derives from a published 32-byte seed
(`mlDsa65SeedHex` in `test-keys.json`), the same seed form RFC 9964 pins for the AKP
`priv` parameter; fixture bytes are cross-verified by three independent FIPS 204
implementations (dilithium-py, @noble/post-quantum, OpenSSL via Node ≥ 25).

The 0.5 fixtures (`cgt-v1.fgc.jwt`, `da-v1.fgc.jwt`, `bac-v1.session.jwt`, embedded in
§4.7, §5.5, and §6.5) are additive: every 0.4 fixture and `test-keys.json` are byte
identical to their 0.4 form, so a suite that pins them keeps verifying. The presenter
key the `cnf` fixtures bind to is published separately in
[`examples/tokens/presenter-keys.json`](./examples/tokens/presenter-keys.json) with its
RFC 7638 thumbprint.

## 10. IANA Considerations

This document requests registration of the `aap` scheme in the URI Schemes registry, and (via
the broker profile) the `grant` scheme. It further anticipates registries for AAP protocol
versions, CPI mode identifiers, signature suite identifiers (coordinated with the ATX
suite registry), and `authorization_details` entry types (Section 4.4.1). The
`authorization_details` and `cnf` claims are already registered in the JSON Web Token
Claims registry by RFC 9396 and RFC 7800; `aap_crit` would be registered by a future
revision. Until IANA registries exist, the suite registry of Section 9.5 and the entry
type registry of Section 4.4.1 are managed in this specification.

## 11. References

### Normative References
- [RFC 2119] / [RFC 8174], Key words for requirement levels.
- [RFC 6749], The OAuth 2.0 Authorization Framework.
- [RFC 7515], JSON Web Signature (JWS).
- [RFC 7519], JSON Web Token (JWT).
- [RFC 8037], CFRG Elliptic Curve Signatures in JOSE (`EdDSA`).
- [RFC 8693], OAuth 2.0 Token Exchange.
- [RFC 9396], OAuth 2.0 Rich Authorization Requests (the `authorization_details` claim).
- [RFC 7800], Proof-of-Possession Key Semantics for JSON Web Tokens (the `cnf` claim).
- [RFC 7638], JSON Web Key (JWK) Thumbprint.
- [RFC 9449], OAuth 2.0 Demonstrating Proof of Possession (the `jkt` confirmation method).
- [RFC 9964], ML-DSA for JOSE and COSE (the `ML-DSA-65` `alg` and `AKP` key type).
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
- [RFC 9421], HTTP Message Signatures (a presentation proof format, broker profile §6.8).
- [ATX-2.0], Agent Trust eXtension 2.0, the revision that carries the subject key; in
  preparation, not published as of 2026-09-08.
- [AI Agent Threat Matrix], https://threats.opena2a.org

## Authors' Addresses

Abdel Fane
OpenA2A
Email: abdel@opena2a.org
