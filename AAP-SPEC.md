# Agent Authorization Protocol (AAP)

## Scoped, Attested Authorization for AI Agent Systems

**Version:** 0.5.1-draft
**Authors:** OpenA2A
**Date:** October 2026
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
[`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md) §13-§14). OpenA2A AIM (Agent Identity Management)
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

The schema and generated fixture pin the form for implementers. (The broker reference
implementation consumes the ATX directly as its subject claim; the AIT is the standalone
identity assertion for deployments without a presented ATX.)

> **Implementation status (non-normative).** This specification does not record which
> implementations mint AITs. An AIT is minted by the issuing Registry named in `iss`, and
> the record is that Registry implementation's own repository.

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

The CGT is an AAP token in the form of Section 9. The baseline claim set (the first nine
rows below, ten claims from `iss` to `jti`) is **ratified byte-for-byte from the reference
implementation**: it is exactly what the Secretless broker's `mintBrokerAssertion`
(`src/broker/cpi/assertion.ts`) signs. The 0.5 members (`authorization_details`,
`aap_crit`, `cnf`; Sections 4.4 to 4.6) are specified here and pinned by generated
fixtures; they are outside the ratified baseline, which is the ten claims and nothing
else. The claim set is pinned by
[`schemas/cgt-claims-v1.schema.json`](./schemas/cgt-claims-v1.schema.json).

> **Implementation status (non-normative).** The record of which implementations mint or
> verify the 0.5 members is kept outside this specification: for the reference broker it is
> broker profile §14 and the reference implementation's own repository; for the reference
> verifiers it is the aap-conformance repository's `conformance.json`.

| Claim | Req | Type | Meaning |
|---|---|---|---|
| `iss` | MUST | string | Minting broker's issuer identifier (the operator's broker URL). |
| `sub` | MUST | DID | Agent DID, taken from the **verified** ATX — never from agent input. |
| `aud` | MUST | string | Downstream audience / resource. |
| `scope` | MUST | string | Downstream OAuth scope requested (e.g. `orders.read`). |
| `trust_class` | MUST | capability | The ATX capability (abstract trust class) exercised for this grant, in the capability grammar of AIP Section 4.1: a reserved namespace (AIP Section 4.2), or a namespace prefixed with the defining organization's domain, then a colon and an action, e.g. `acme.com/orders:read`. Distinct from `scope`: the trust class is the portable, abstract capability; the scope is the local downstream binding. A broker SHOULD mint a value in that grammar. Under claim schema version 1 (Section 9.6), a verifier MUST also treat as well formed the legacy `namespace:action` form, a value matching `^[a-z0-9_-]+:[a-z0-9_-]+$`, which admits an unreserved bare namespace such as `orders:read`; removing the legacy form requires a new claim schema version. A value in neither form is malformed. The aap-conformance repository's `conformance.json` is the record of the pattern its reference verifiers match. |
| `issuer_chain` | MUST | DID array | ATX issuer chain, carried for v2 cross-broker verification (broker profile §7, §11). |
| `trust_level` | MUST | integer 0–4 | ATX trust level. |
| `iat` / `exp` | MUST | NumericDate | Validity window; `exp - iat` is the policy TTL (§4.3). |
| `jti` | MUST | 32 hex chars | Unique token id, 16 random bytes hex (Section 8.1). |
| `aap_ver` | MAY (v1) | integer | Claim-schema version (Section 9.6). |
| `authorization_details` | MAY | array | RFC 9396 structured grant entries, typed by the registry of Section 4.4. Mandatory to understand: MUST be listed in `aap_crit` when present. Narrows within `scope` and `trust_class`, never widens them (Section 4.4). Outside the ratified baseline (Section 4.2, preamble). |
| `aap_crit` | MAY | string array | The claim names a verifier MUST understand or reject the token (Section 4.5). |
| `cnf` | MAY | object | RFC 7800 confirmation: binds the token to the presenter's key (Section 4.6). Mandatory to understand: MUST be listed in `aap_crit` when present. |
| `fga_constraints` | MAY, **deprecated** | string | JSON-encoded FGA policy from the 0.3 and 0.4 text. Deprecated in 0.5, replacedBy `authorization_details`. Still optional-to-ignore (broker profile §8.3): a verifier ignores it. No known implementation minted it (the name does not occur in the reference broker's source); it stays defined because the -00 and -01 Internet-Draft text and both aap-conformance verifiers (`verifiers/python/verify.py`, `verifiers/node/verify.mjs`) carry it. |
| `intent_verified` | MAY | boolean | NanoMind intent verification result. Optional-to-ignore; not minted by the v1 reference. |
| `max_uses` | MAY, **deprecated** | integer | Use-count bound from the 0.3 and 0.4 text. Deprecated in 0.5, replacedBy `budget.maxUses` (§4.4.1). Still optional-to-ignore; not minted by the v1 reference. When both are present, `budget.maxUses` MUST NOT exceed `max_uses` (the §4.4 narrowing rule applied to one bound). |
| `context_required` | MAY | boolean | Whether exercise requires conversational context review. Optional-to-ignore; not minted by the v1 reference. |

Example (generated; this is a real, verifiable token under the published test keys):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiI5ZjhlN2Q2YzViNGEzOTI4MTcwNmY1ZTRkM2MyYjFhMCJ9.cnJS6s3vA96X5-h24VNv8gAgykdrkrpKGSz_aGDrqXmIeH740dv6YwlKBCsSqb_L3ZDDGiczeMfoxpvciLgyAA
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/orders-reader",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "acme.com/orders:read",
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
that a conforming verifier must understand or reject: `authorization_details` is mandatory
to understand and MUST be named in `aap_crit` (Section 4.5) whenever it is present.

**Narrowing rule.** `scope` and `trust_class` stay REQUIRED so that foreign RFC 8693 and
OIDC style verifiers, which understand only the scope string, keep working. Within one
token, `authorization_details` MUST fall inside what `scope` and `trust_class` permit:
every entry's locations and actions MUST be ones the scope string already allows, and no
entry may name a capability outside the trust class. A verifier that understands
`authorization_details` enforces the intersection; a verifier that understands only
`scope` enforces `scope`; neither ever grants more than `scope` alone would. The minting
broker MUST reject a request whose requested entries would widen the scope.

**Producer rule.** A producer MUST NOT emit `authorization_details` (and therefore
`aap_crit`) toward a verifier that has not advertised support for every entry type the
token carries, because a verifier without `aap_crit` support treats the token as an
unconstrained baseline token. The advertisement is the **set of entry types** the
counterparty understands, with the semantics of RFC 9396 §10
`authorization_details_types_supported`, not a boolean; it is carried in the broker
discovery document (broker profile §8.5), whose own schema names the member, and selected
by the negotiation of broker profile §8.1. Both aap-conformance reference verifiers
(`verifiers/python/verify.py`, `verifiers/node/verify.mjs`) implement `aap_crit`; that
repository's `conformance.json` is the record of what they verify.

#### 4.4.1 Entry type registry

The initial registry has seven types. The wire value of `type` is a URI the family
controls, `https://specs.opena2a.org/aap/types/<name>`, where `<name>` is the short name
in the first column; the short name is the registry key and the name this document uses in
prose. The URI is an identifier and is not required to resolve. Member names inside an
entry are camelCase (Section 9.6); `type`, `locations`, `actions`, `datatypes`,
`identifier`, and `privileges` are the RFC 9396 common members and keep their registered
spelling. Every type that can carry data out of the session (`mcp_tool`, `peer_agent`,
`model`, `network`, and `data` with a write action) carries an `egressCeiling` member: a
set of labels (Section 4.4.2); when absent it is the empty set, which is default deny for
any session that has admitted a labeled field. Every type MAY carry `requiresApproval`
(boolean): when `true`, the broker admits the entry only through the escalation hook of
broker profile §6.10 and denies it where no hook exists. Unless a member says otherwise,
an absent set member means "unbounded" and an absent identity member is not permitted.

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

#### 4.4.2 Label semantics

These definitions are normative here. A label vocabulary registry, if one is published, is
derived from this subsection and changes no rule.

- A **label** is an opaque string naming a sensitivity class (for example `internal`, a
  contact identifier class, or a residency class such as `residency:eu`). Labels are
  attached to fields by the data owner; this document does not define the vocabulary.
- A **label set** is a set of labels. Labels are sets, not levels: two fields can carry
  incomparable labels (a health record class and an EU residency class), and a session
  that has read both must be treated as carrying both. A total order would force one of
  them to be "higher" and would let the other one leak through the comparison.
- A field with label set L is **admissible under a ceiling** C only if L is a subset of C.
- The **session** is the agent's context at this broker. The **session label** is the
  union of the label sets of every field admitted into that context so far. It only grows
  within a session (the broker profile's session high water mark). It is keyed by `sub` in
  the Agent Security Context (ASC) and carries across every CGT and DA minted for that
  `sub`; it is reset only by a deployment defined context reset recorded in ASC, and a
  deployment that issues data grants MUST define that reset. A CGT lifetime is the
  minimum session, not its bound.
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

The `cnf` claim (RFC 7800) binds a CGT or DA to the presenter's key, so that a token seen
in transit is not a credential. `cnf` carries exactly one of `jwk` (RFC 7800 §3.2, the
public key itself) or `jkt` (the base64url SHA-256 JWK thumbprint of RFC 7638, as
registered for `cnf` by RFC 9449 §6.1). The bound key is the key the presentation binding
step of the broker profile (§6, step 3) verified: the ATX subject key where the ATX
carries one (a later revision of ATX; the current ATX 1.1 format carries no subject key),
or the key registered for the agent DID under AIP. The presentation proof formats per
binding are defined in the broker profile §6.8. The presenter is the agent that presents
the token to a broker: the `sub` of a CGT, the delegatee of a DA. A CGT the minting broker
uses as its own assertion toward a downstream (Assume, Exchange) is not presented in this
sense; `cnf` on such a token is not verified by the downstream.

`cnf` is REQUIRED on every CGT or DA that is presented by an agent to any party other than
the broker that minted it (a network binding, a peer broker, a delegatee). On the local
unix socket binding, where the agent never holds the CGT and the presenter is bound by OS
peer credentials, `cnf` MAY be omitted. A verifier that receives a token with `cnf` MUST
verify the presenter's proof against the bound key and MUST reject the token otherwise.
`cnf` is outside the ratified baseline of Section 4.2, and broker profile 0.3 §6 verified
the ATX and nothing about the presenter; the implementation status note of Section 4.2
says where support for `cnf` and for presentation binding is recorded.

### 4.7 Example with authorization details

Example (generated; the Section 4.2 claim set plus one `data` entry, one `budget` entry,
`aap_crit`, and `cnf` bound to the published presenter test key `agent-key-1`; entry
`type` values are the registry URIs of §4.4.1):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImF1dGhvcml6YXRpb25fZGV0YWlscyI6W3sidHlwZSI6Imh0dHBzOi8vc3BlY3Mub3BlbmEyYS5vcmcvYWFwL3R5cGVzL2RhdGEiLCJsb2NhdGlvbnMiOlsiaHR0cHM6Ly9hcGkub3JkZXJzLmludGVybmFsL29yZGVycyJdLCJhY3Rpb25zIjpbInJlYWQiXSwiZmllbGRzQWxsb3dlZCI6WyJpZCIsInN0YXR1cyIsInRvdGFsIl0sImZpZWxkc0RlbmllZCI6WyJjdXN0b21lci5lbWFpbCJdLCJsYWJlbENlaWxpbmciOlsiaW50ZXJuYWwiXX0seyJ0eXBlIjoiaHR0cHM6Ly9zcGVjcy5vcGVuYTJhLm9yZy9hYXAvdHlwZXMvYnVkZ2V0IiwibWF4VXNlcyI6MTAwLCJyYXRlIjp7Im1heCI6NjAsIndpbmRvd1NlY29uZHMiOjYwfX1dLCJhYXBfY3JpdCI6WyJhdXRob3JpemF0aW9uX2RldGFpbHMiLCJjbmYiXSwiY25mIjp7ImprdCI6IkhsSGdDY2pyaGJleXc4MFZNZWY1MXlQd2h5UnFqaXdMZHdTTFJxbzdoU0kifSwiaWF0IjoxNzgwMzE1MjAwLCJleHAiOjE3ODAzMTU1MDAsImp0aSI6ImMzZDRlNWY2YTdiODA5MWEyYjNjNGQ1ZTZmNzA4MTkyIn0.lqc9HJVQlSAsGlwmPnBzb3OGzYHwMVVFpb57w60hit84b960hf23EE18AfLQeJVLQOeDiy4OJnOpOawGtxgIAg
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/orders-reader",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "acme.com/orders:read",
  "issuer_chain": ["did:opena2a:authority:opena2a.org"],
  "trust_level": 4,
  "authorization_details": [
    {
      "type": "https://specs.opena2a.org/aap/types/data",
      "locations": ["https://api.orders.internal/orders"],
      "actions": ["read"],
      "fieldsAllowed": ["id", "status", "total"],
      "fieldsDenied": ["customer.email"],
      "labelCeiling": ["internal"]
    },
    {
      "type": "https://specs.opena2a.org/aap/types/budget",
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
presenter test keys (`agent-key-1`, `agent-key-2`, `role` `presenter`) and their
thumbprints are published in
[`examples/tokens/test-keys.json`](./examples/tokens/test-keys.json).

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
| `max_depth` | MUST | integer ≥ 0 | Remaining delegation depth below this assertion; 0 is a terminal delegation. MUST NOT exceed the `subDelegationDepth` of the delegator's `peer_agent` entry whose `peerDid` is this DA's `sub`, when such an entry exists (§5.4). |
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
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL3JlcG9ydGluZy1ib3QiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImFjdCI6eyJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIifSwibWF4X2RlcHRoIjoxLCJkZWxlZ2F0b3JfYXR4Ijoic2hhMjU2OjIwNTI4NzlkZGExNWIxY2E1ZTYwMzE5ZTM0NzdhNDAwODQxMmJmZmRhZjNjMzU2NmM2NTg3OTVhNDhjYWI4ZmQiLCJpYXQiOjE3ODAzMTUyMDAsImV4cCI6MTc4MDMxNTUwMCwianRpIjoiNGEzYjJjMWQwZTlmOGE3YjZjNWQ0ZTNmMmExYjBjOWQifQ.Lr4HhIi5xeWcnNY5k1E-0hoOWlcwpaqAAe_bjATpFEQRYeK3kYrkisk9xfD4x4KLvP7EmUbywpI7gMCsLKHsBw
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/reporting-bot",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "acme.com/orders:read",
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
  a label E did not carry. An absent allow set in E' inherits E's value. For
  `network.destinations` the subset is evaluated by pattern coverage: each E' element
  equals an E element or matches an E `*.` pattern, and an E' pattern is covered only by
  an equal or broader E pattern.
- **deny set members** (`fieldsDenied`): E' is a superset of E. Absent means the empty
  set.
- **bound members** (`subDelegationDepth`, `maxUses`, `concurrency`, `rate.max`,
  `spend.amount` in the same currency, `tokenCap.input`, `tokenCap.output`): E' is less
  than or equal to E. A `spend` in a currency E does not carry is not comparable and makes
  the entry an orphan. `rate.windowSeconds` in E' is greater than or equal to E's for the
  same or a smaller `rate.max`. A bound absent in E means unbounded; a bound absent in
  E' inherits E's value. For `peer_agent`, `subDelegationDepth` in E' MUST additionally
  be strictly less than E's, since E' is one delegation deeper.
- **restriction flags** (`tlsRequired`, `requiresApproval`): if E is `true`, E' MUST be
  `true`.
- **constraint objects** (`argumentConstraints`): every constraint E states for a tool and
  argument MUST appear in E' JSON equal; E' MAY add constraints for arguments E leaves
  unconstrained. The constraint grammar is deferred to the revision that lands broker
  enforcement.

A DA is valid only if **every** entry in its `authorization_details` is narrower than or
equal to some entry of the same `type` in the delegator's `authorization_details`, and
**no entry lacks such a parent**. An orphan entry (a type or identity the delegator does
not hold) makes the DA invalid, whatever the rest of the token says. The delegatee's
array MAY hold fewer entries than the delegator's. A DA's `max_depth` MUST NOT exceed the
`subDelegationDepth` of the delegator's `peer_agent` entry whose `peerDid` is the DA's
`sub`, when such an entry exists. When a DA chain is present (nested `act`), the relation
is checked link by link, each DA against its immediate delegator.
The minting broker MUST check the relation at mint time; a verifier that can resolve the
delegator's grant MUST re-check it; a verifier that cannot MUST NOT treat the DA as
carrying more than its own entries state.

### 5.5 Example of an attenuated delegation

Example (generated; `orders-reader` delegates to `reporting-bot` with fewer fields and a
smaller budget than the §4.7 grant, `cnf` bound to the delegatee's published presenter
test key `agent-key-2`):

```text
eyJhbGciOiJFZERTQSIsInR5cCI6IkpXVCIsImtpZCI6ImJyb2tlci1rZXktMSJ9.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL3JlcG9ydGluZy1ib3QiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImF1dGhvcml6YXRpb25fZGV0YWlscyI6W3sidHlwZSI6Imh0dHBzOi8vc3BlY3Mub3BlbmEyYS5vcmcvYWFwL3R5cGVzL2RhdGEiLCJsb2NhdGlvbnMiOlsiaHR0cHM6Ly9hcGkub3JkZXJzLmludGVybmFsL29yZGVycyJdLCJhY3Rpb25zIjpbInJlYWQiXSwiZmllbGRzQWxsb3dlZCI6WyJpZCIsInN0YXR1cyJdLCJmaWVsZHNEZW5pZWQiOlsiY3VzdG9tZXIuZW1haWwiXSwibGFiZWxDZWlsaW5nIjpbImludGVybmFsIl19LHsidHlwZSI6Imh0dHBzOi8vc3BlY3Mub3BlbmEyYS5vcmcvYWFwL3R5cGVzL2J1ZGdldCIsIm1heFVzZXMiOjEwLCJyYXRlIjp7Im1heCI6MTAsIndpbmRvd1NlY29uZHMiOjYwfX1dLCJhYXBfY3JpdCI6WyJhdXRob3JpemF0aW9uX2RldGFpbHMiLCJjbmYiXSwiY25mIjp7ImprdCI6InFJX19CT2NjZ0FoaEg5d29iX0c3Z0ZWSExLSWtTNEN1dHZvU3gwYk1DWTgifSwiYWN0Ijp7InN1YiI6ImRpZDpvcGVuYTJhOmFnZW50OmFjbWUvb3JkZXJzLXJlYWRlciJ9LCJtYXhfZGVwdGgiOjEsImRlbGVnYXRvcl9hdHgiOiJzaGEyNTY6MjA1Mjg3OWRkYTE1YjFjYTVlNjAzMTllMzQ3N2E0MDA4NDEyYmZmZGFmM2MzNTY2YzY1ODc5NWE0OGNhYjhmZCIsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiJkNGU1ZjZhN2I4YzkwMTJiM2M0ZDVlNmY3MDgxOTIwMyJ9.ZhU2ZalLHieZWlmN72ZPOL3y-uvXDOH2TqGh9tMEGJuq5MG4gjrkU3O30xCJIVpYdn3KGF0eG6UbyJ3Qh912Cw
```

```json
{
  "iss": "https://broker.acme.example",
  "sub": "did:opena2a:agent:acme/reporting-bot",
  "aud": "https://api.orders.internal",
  "scope": "orders.read",
  "trust_class": "acme.com/orders:read",
  "issuer_chain": ["did:opena2a:authority:opena2a.org"],
  "trust_level": 4,
  "authorization_details": [
    {
      "type": "https://specs.opena2a.org/aap/types/data",
      "locations": ["https://api.orders.internal/orders"],
      "actions": ["read"],
      "fieldsAllowed": ["id", "status"],
      "fieldsDenied": ["customer.email"],
      "labelCeiling": ["internal"]
    },
    {
      "type": "https://specs.opena2a.org/aap/types/budget",
      "maxUses": 10,
      "rate": {"max": 10, "windowSeconds": 60}
    }
  ],
  "aap_crit": ["authorization_details", "cnf"],
  "cnf": {"jkt": "qI__BOccgAhhH9wob_G7gFVHLKIkS4CutvoSx0bMCY8"},
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
multi-signature form of Section 9.4) is a target, not a shipped property: the v1 fixtures
are Ed25519.

> **Implementation status (non-normative).** This specification does not record which
> implementations mint BACs. As for the AIT (Section 3.2), the record is the issuing
> Registry implementation's own repository.

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
| `session_label` | L3 only; MUST when the issuer holds a session high water mark for the subject (broker profile §6.10) | string array (a set) | The union of the label sets of every field admitted into the session so far (§4.4.2). MUST NOT appear at L1 or L2. Labels are a set, not a level. An empty array means the session has admitted no labeled field; absence means the issuer holds no high water mark for the subject. The two are distinct. |
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
never fetched from a hosted service, and needs no federation transport. That is what keeps
it inside Zero Failures (broker profile §11). An entry MAY carry an expiry no earlier than
the revoked token's `exp` (a `jti` entry is useless after that) and a subject entry has no
implicit expiry. Broker profile 0.3 §6 step 2 bound revocation "entirely" to the ATX CRL;
the grant revocation list is a requirement that text did not carry.

> **Implementation status (non-normative).** This specification does not record which
> implementations maintain a grant revocation list. For the reference broker that record
> is broker profile §14 and the reference implementation's own repository.

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
eyJhbGciOiJNTC1EU0EtNjUiLCJ0eXAiOiJKV1QiLCJraWQiOiJicm9rZXItcHFjLTEifQ.eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiJiMWMyZDNlNGY1YTYwNzE4MjkzYTRiNWM2ZDdlOGY5MCJ9.Sb5dBpuexMs13mzUMJ1ERnpwhLV6TiNTNFmm8quJ9TxJihFYejH-4zHNEYeJhZa0xi7H1YuseS0KdFayKqe0aFAll-Nm9KGSwcqWf8L1xdR6e0jdgxxNZ6Dx_XrNvHPFw9UBs4MHlJJQ1W1EhGEPtEJDtrWGcEmVkFIrR0dlmAt0fwrg2iS-2-AuL8aApPLQdDT6trTrJHf7QSUERTVtRAjazjJ7r4XYOklVPJ2qy8tqbyoJGVhqrm_1oJXBSmWhifAUbkrL3nIoBWiaySw9r8Rih1ISBC3RdRKBeA1x0mn_ZBCLMbljcGU0UNX5jkkgK1Dn5rUQscCFXHPPgpsnDpsSP6OU3QCnCJdRCOvlHeIjLFg-pk_0sCFLbUj71EO_6i--U4W1vwIE_hAExXcFpHBvSnR1uLcPvqAcMto34RWLtETAc8WUGTxS7l6IMsxHTLauxcMwSd96K4SopQftlg-_1OB1Q1Sx8wCsY1t9sPoodaFNP_OEcvvCdbh2kvZeauVW58JvKG5l6SUnuMESdMQmclfaR0J5-NXU9LVxvL80VXUHfXOOjPxsh31V72eunSYfbqaijMQF5J_qxCFGCuudkmxEg1LcLuLiX8e3BywP01TtB91E-1cTOZDDTAeLf-1RR6LPJD9M9tB3RLgck3sdjR7WROpTGq576xShZl0ykUD9k8HT08RdrA2-eVjZA2-OdnnF6Qv5sG4CPz2--cF3hY03M_lG8MA_OsF5Rv1rYJr2ObLSFj6IFaakGytAG2QdnzwrVAVDf1kbpi7Hbzq36itcNN-sA1MDQNONsRxlwTTDp9jxN_Rt5Tc7uhZZywhqy1m498D93R5UHjMpclZfLPDeTLQcdvW6R-5zmZYJklU-Llah7q0g-8dkF2a491HOetErmx8hNjqphGIoffvRRjozPf62xEogR5tEr4AOzcyn7-NUD9i2LdHi5i_bGOJJ_F-4NmYFSG25lJMW1m5wWdkczbK8C9khDTn-14OcaxJTAWZLNM0pTbINUgZ_LEG5zxhItPc-xaP5N3A1GVe1DyJIUf2NWPSd1Ro9MJ0d9wqKolUcBAuCtZMo_pl_3ZGFPJAPz6rdYPQaEO_A7-4lHUG2-Q3GN_o5-myhAmTtH5sAHHF8o4N1a-SSlWCvOCgIMzdWA8CiaVJECbD14okPpJTwnq3z-IiDvN9W4VLU8vjRkdm7RfzTPa8pRsEIG0M7vOjYKwTAvy1cdMZSaRqjrNas4PT14thlVWCe6KdU3KgBc8a_SNf9hKN_nqdzSGcH3y5nIZ5AsQzvJIUcKFbbUI6HFQ9PJ1IYLWtwk5NtiEi2VWaZEEJuHfOgweld9yWPo--N02Kp2Wudl5jFs4QORqZGUfOHyzO-rXjby3YXrVnCsu4binMMxyjSDAb05y2sE_3XB-k5sk3rhwUIOEtcqPY2CnT_GxjkRmwvSOR_f7mY2ecpdmfdoyNUma2VG1VQ2wE80qeDenTQBF07xn_YSxhPE4Q78wmH2ollkDLg219iNuCpWzelXrn9bPt409kH12xWTNF2KhzsAfOKHsQqOXxYDH8TuDbKO6ZAa2XxzIq9EMCwdD0DAEc8f39KHm_QNV85F-EAMfG2IbmdjfL1-2rPa8YGkffXCcRRfioBfm2fpP1WGfdGmBJPe4uo6ytiAip07RmFj-x_hEwaPpVPbGJ1_TZlJFuQ0GRh1OcYtqAC51gcbUx7cKVtJsVoO-LKJPqiXQ5z1NYNOvSZs6SPR95xQv_eBTtd_r9azaLGeYoIjdembIhDjcJOXrFVsXoaWLKB_IGMDzrjrp7Uy1dFVM8gBri5Z15uUcor4WV6GCvwbV_h-fOQ0ryCm3_Q8Ims09XDNnUkXYh5qWC1CYBJcyPhFuAoiF7jbBkYWxMk4OxEgHDCEbb8GGkc6JM5FRu8KhKcrqtNtFPGZx12eywocUSQpyOof8uv8cwYxoEjAwPH146cHlmJh6_pc8c4A8kMpBnFpf1_bjn4M1DbrBGYyqZX0re7WNH5uUwol-j47aK7A4btsS2TBAp-CieKxV0DSFBXnKrNPiDls79BDcqr-BJQbTYSXUB3Ht7r4WnQPo9VwUv5BKm9PLxhwCvEtbAIb4brzq-bixRUR6HKm3ulEI0mCKVGNTYYt427Lis7J3ZTjTHv1AnZpmZlo5dOQe7PxxKBEVLpYxQ4HdjcJMC2386wLlHQprJbB7U465gu7W2l4NwDeyLA5kWvY2Zmp8BFMDF3Rjsr-uzTAF1yZz6bpy9V9J3AfoblEN-Q6RR-GX_fxuDeQMcedZHJAGCv-yKbg2bicDkVSQtfQcUMal-o-ZKMb5doIVGLycPi9YQmYqgemqBcM75rtJiiGOgUgmvvHPojBrUNHwq-visugJEvnh3GCheMfjLx30SxVuDmH6EHDhfwL56joRe9rDZIokJwLJWp9CrsXXd4U8xtEkiuW-eKCP-z8UgxNEoWIpzGPkt-45tym12SQV8Uk3TgXh0G47GpQ8UhHeip8lN3sTgFfYz0jvnlczI821j_CXqV6iogsHciYiq_jnzAveoEjk2vPmMLmllNNUzh1tDOQBWCsVA849uViR9oTFI2LxxoRBgo_hLi04IXK44KrP2SUpkF5ZVpzhjBiKsLhWvByZSKfbZ5GxB6a12eSlD0EB653LjPNcQThha_5h4527J7tKmpDlACRY1eLK1xwcwjRPUlll4Ks77ZK0BNyjddMUByVzntlKMeIqSgmFi20USGYlFGERJUT4iCJ2b2ebg9Nivx6UeCCYFWztEH8-glVZRyzAqsdaa-ru_4TZ06NBjQ5cGYWHRJUw5x99_nIJvV2eW75x5WKwuS8SrUx4135tqJyJRWC37tgdOC1cyMZfzfSQ6QSlLRwTvR3t_uorLAono0SsB-HhQ9pf6idcJ-2xshEYhqxsBwBv2h0hu8BNlZ_5q3pQYH9XBu2RjLx18fEtyI4Qh5lqofjWqyKokfJRKtjNbHJMaHSe0Rh5BaaeqIAJjhz4COpEaX18LngjE4YqeV9aLVB8QstWsGYaFOTAekucYsTzDlIhzWTJ6624ggDUlbN7kkIC7-nh8in0PRm03Q92yNqe0dG6E30C2aNLpn8CG434aIb9ADWNsD47f7lemoj29lXpd1kVC0WFcRL8T_oriKgwoxP6-Qxve84iI0MWazbFm1jPv2E4Rq5DbX2cH0gdS6uXNYQh_v_n4HzVSg6Q9m7u9AFWV9JOqr52rDKS78BZUpPIG3l2mtHNOJnWUjEdwkaFBbHgGN65um7-p9FyWQU8OHA_rgax4gGviyygec1UJJ-SoOL1kMZJ9FBQ7LhvZE8i7QKWv9OUASQs-u_otpFM_RtqZuKdt9h0VwqD6KKTZiT8RhBHHuXfs_6GIBLNwoespRi16zSpIgT6uAofhJIuDGgiUk6DmnlOHBY6X5_c9L-lsd_EfRlkiVkfKIw3zPTlz6WwsKdI6Z6Mj1TLTJbiDSquM_s6O13Op69C0i1AaIeYzMdsOwaJ3fgoDVf6N5epC3cDVYrn-_xOwXTPKUfQul74zlp5AzEizDvAvi62MI_hVQUJPOtQnXvDKwJFeQdnJM1YZIxCmY7jRoiTcPkWB7Eb3gNvc31IgIQ6PhF5afDr0ifSH_qvxt0bakbq_1JQ6yqB3reK3d3HO8oy1LfGO9JbxxNu8K6J6gedF_Ry_QHdNflG0IZa94bJSukwJi7rcVW2y68skYZn1nX7G0qhZzMdiwmwxQb_znXPERiPEYWApsRNaoYyLhAzhZaGyS9c5ydi4hYJ7b_IMRSuupZvBTlJhCiT-kKzyimlkcNT_KMPUrU_ODrB9H_9vziFr5CcBMxE_L1QBtNAUT-rrN6hGFUWBSFrouOZ5Wnjyt6DUiuLD0DADKYrOSntTHgDuEJCekDq3gFU_QFD33yEEo2zSWo7ATeYwvQQR3mcZ5q5G2iYJMLxWU932F76ww7n4g1eoiO0txZ0e5By2VK4MNus-ecuJ-jALu0pmWtK8TWs-R5K-CiuBEHSPESsfpPh8MeQNLslgouD9qVKos8FquCBaDPtfCf8-4Pzz6XE4qUzFG0wQw9hCwqKt7TbkKgyZ-Si8o11syRDyqfaBaIXTpjYAG5gMF1nz3Q3Ud7F_GJYepYblN-woHZc_6Fpgi48VfBAphiln2Jk38oZ88WTSeeMAbE30ZTiB36MZ75Qc9Ybd8S3vWfZvr9jLerF8cd1yBG2nEvgrmQToeQzuksTgq8jYOrUJjAdPUuSGbKrHmxlkB6F6n0H0zQq1Z-SbQAk82S98BjtbhA89J3quyIkaGcQ2U0tHzvlglcIUpZX6dp-r_B0VqkqOzIzFTiI-X_iqDpKu0BSgtdaStvdDm8i1a_QAAAAAAAAAAAAAAAAAAAAAABw0UGSMm
```

### 9.4 Multi-Signature Form

<!-- opena2a-definition: signature-family-gate -->
This section is the one home of the family signature gate: every declared signature entry
MUST verify, and an artifact that declares an ML-DSA-65 entry MUST also carry a verifying
Ed25519 (EdDSA) entry, otherwise it is rejected as `HYBRID_INCOMPLETE`. ATX, ATP and AIP
cite this rule for their own signature arrays rather than restate it.

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
  "payload": "eyJpc3MiOiJodHRwczovL2Jyb2tlci5hY21lLmV4YW1wbGUiLCJzdWIiOiJkaWQ6b3BlbmEyYTphZ2VudDphY21lL29yZGVycy1yZWFkZXIiLCJhdWQiOiJodHRwczovL2FwaS5vcmRlcnMuaW50ZXJuYWwiLCJzY29wZSI6Im9yZGVycy5yZWFkIiwidHJ1c3RfY2xhc3MiOiJhY21lLmNvbS9vcmRlcnM6cmVhZCIsImlzc3Vlcl9jaGFpbiI6WyJkaWQ6b3BlbmEyYTphdXRob3JpdHk6b3BlbmEyYS5vcmciXSwidHJ1c3RfbGV2ZWwiOjQsImlhdCI6MTc4MDMxNTIwMCwiZXhwIjoxNzgwMzE1NTAwLCJqdGkiOiI5ZjhlN2Q2YzViNGEzOTI4MTcwNmY1ZTRkM2MyYjFhMCJ9",
  "signatures": [
    {
      "protected": "eyJhbGciOiJFZERTQSIsImtpZCI6ImJyb2tlci1rZXktMSJ9",
      "signature": "XnVv7UHh0_Gsm8Pkdoa5uVK4CUBmxz_IiNZLPemL9EWKrvYmD6sijAecqGJo3ZmKBFt7HiEbZ-da5d52HItYDQ"
    },
    {
      "protected": "eyJhbGciOiJNTC1EU0EtNjUiLCJraWQiOiJicm9rZXItcHFjLTEifQ",
      "signature": "T7GWc3Ix5QJ0rjGxkXMd_P5KNG1RU0T03sUSYr61EEsj5zYcfywQE5xpWZaQ68dr_q00-TSjWU15Z8vAtA_4xf2aahApijIkKLAZA1SctwGBMM1g6m9mZZvt83b3tuzEaeP78UrxGqLku6iV0nTrq6Sa2y-Md9X8LUZtOvnUKvPlzdKq7Lj7t72H8BLjwcpCIjPWfeMhle2oLgcv7zlLiK4Vvax6QMlzCTKBLr_cR8d6C26Ij_I25or6nwwvwVnc0XDID5MPC9eGpqOBGXCo7nQOBhklcG49IETGZ8-e-vrp8B1E4OwEy7SGwDtfOqds_sRX8ZACKPfnb7Q9GN8UYjeZSRyv0LXqsg-3dyJtQ0FI76WGAb840zxmBp9tF4U9O77v4ZAr_FvpC6uytyrNiNtXsVi2CDyrBTwxbxcfvZDoKQRurbnwk-JW6VnFvCwuvTmYeGtQvkYlIObz6jkjno5W7mhVEbtBjoGjV826jzbpoEj3gpRQp_ylMbiVe3yNkQC4yXsF7xqLOzUkibqsMXTy3l9AgBeUhMPOjDNA0QKlETMYImPGEBdhNe_e3wRRwj0ML_NBFttnBOnS51cyjd83xpaS79zEdAm18DJbKOou7MSMr4GBAQ2oMZEy_nlwaTDvz5VpyU5hMZBsSbw2uDcJublG5vaHdkvzHxQWte5-lmnJ-f3M8Be7er6G-mBXc6mzwb8xHwDNAR8rH9Gc3BNyfoNAdPfzn6_JvMR-D776rR9yVOCW08H4v1E3csqUrmn2h0VeB8Y8yEreyT4QNkaGptDttYRwFI3D8D36ueqv-QYY47h3rgWEi0GCpIcdzbU7Toyg44vZce3r4A2TDCAWqOrJfB9Ou2cpWbggPp9bEwBvuk_dP4bnFjUlutWxNW4muLQY6q_WMSSS06sX0dBBgrckIwcS_QLTjxT46eiBdFTmITv4ic3HjQbiI9okbN_qNuD7GiZkIu8icEq7TEFYOonaFkkaPwEOTrt8pV_2yo62D-0W8P-ZzvpjSRQ7_qtqRj2aM65qyVoAim8igP2ShnAWa2vAv40P_hpSyrEDc0P-7s2zN2snAWOS-RQtkdmDD_lhaCGrQJptWG2mPevOxRtqBr7_sP-16-58zwBlU12YRyEPJDiJlfz4oFaNcLwAc76IARRCuTun-iWjTQXVA8MDFO6xEdGTYWPLgWNLT6af3XDGuntc0CZqbw37jXfMlaR24rseYB8Lx2QVQU-RaWO3H7ZMPm-Z5LQEfEEnxVEFOvnKnIRvdGmJitYfO9_Nz32AGFbc9GiRswnOYVp5cae5BKBajqx1JKMkfe3-slYKeNCyI_RrQRev6JVQLpL7WBSHb2cTZLrBSaRTTB3k3cSvaLkhQTSdifT9E6CycirdncYL__mIRQ3m0J0Sk4xpirlPAz-4zERzhJxPw6uPqAfrQHpVK1rkQzI5QFVLI-9UVvega9hK6ZsfOqlcRhEOX6eCITi18A8NVAYPIamisE3ZjC-BjtHsf0Gi59DX615aOVtTwnPKtoDKmW7glo-yb-PbtYbRih3IDX7Dc39Y8XcATp3CyFRir2ygYLPgbDbNOIYE2_Y7jD3GrTeyQjwrmxPwaSv269GCAz06Rh6gFjAzy1W64B9k3N3dVGHvJLSj6MF6lXfCO7EWUpDwIRkCnqRzTwFEoMwzscu6LfEOGl6nf0CzuUhpN51vSjzQBgYQnnC9cPhBYthSq9Mm5_1cBFMHKkIJgef7oAj_2T9pqaSH1ziys3Y0dDt0GdD51-u44NstarifCi8RBt5iBoADI77nKlSg58OoT6afWcTI_HWuAsrWMV1ab4auh0yDLozuKF9W0tXd385EJ3gweO0rssEIk9zQ9wqzC8301VpjIiI1O6e_svBVakkk2Pcz6Cy5I97YBaNXi559TxhsQgyenMl3rtlO98BKY7EX-NEJcWvrZwn3a2eDUT91wOaemIlLxyHGIC63EZ1jM2bInZvuGDVpPeiQ6jnZkvqhLr86dyoh-ggGuubUADRPKuE6-Xv3JxMr4zv-dh13ha_Ie5bHf_C9zWTaAOXqUqbINKPaHE9iEkeqJNHK37Ox3Q-4-ZR31ni48x1kWdQ883TbW1vrS28Q3gsar3f-RLbO2hrkJAcJW8jJxxdqUIw8oW54G8HIAYH4SF0_MuY0ZW2RnPJjFML7_f6cNm0v6LLvbRJtXVy_8vz5RnI96sGiWxeXfKVfZINWk9mnB1CcDv6Dja6zWB12gAi89uyFoXDEcUJKhA-3dHtM7c9HEloVddg7I0m-1ZYewhjkVrLM-QSxLn4xe3kZ_sLihnAJcUXAQdbRAigpUnQ-j-SbvQgG76TMgSNIlm-8Ynft_c-SPy6o9vuw3S7qsrjEsxc_HdcVmHK6pfXhOQ7WD9NeNzES-FPOnhUBX2ATJRXZsRmZkILG1radzlcVFiPxdGAq0boWdqYuqdMHDmtFBuF9bdavdx8kWWq6xU1knshBurl4AhR813kapf9qwq5_KiUd6LBj_9l2U3ryrVdCBXAnw_jF9d4B8uSjKF1ANUyqi_ORsNToDYbR1AsZKdpPn64jyCIZ8LtynnHvgXlyqVuZ9n_aB4IQuSfQNUPpNUv3Zz1xblt8JsBwoX6X2MYdek85Pf24D4XJ-RRU_AeK0Dyjw2reX5nhN2jPJCix_k9TEdOohGYh0LkMY-gVOlvaiFxN4m9agQ8GjBb94YQTns309BEsVWC7XCoe2F8eHDrmB0L9HfpNxJNdD7TJZPxyBVCLx6Aj-klWonp4B0j29r-fCbIpxpKT07F8Nu33gDT1qMVOy0pfCU1Wc53kp4uMrjE-2IvQmhL4lXgxF3UhKPUrKHKKy0dDerZOB4n6vrQm1az4E0UDUapJBTLPoTU8RFzuiXCI-ct1Hxs4ocxu1eS2Qyfq6kBPr_Gfku-GaFN0fHmHZqusYsCQaWHgTuM_yHjQTH7wbbqeA7BEJDOTiUJJ2BLusKSA9t11oiiFiXCyinGV2Uvpsl42DKCQ5ooyeXkt1dtntizptnE7004oAtb2pavZLgzGW4FVV8s4x-KHUakNVGVI6T0xQl2EWBlRF_JWbiopNesKE6UuQgCj3uuFVQDSAp-GPMrKRo4_7DIXrX0kfNo5wV2TKMro9a8u0o-o8Z1em_I3NhygzKADpkQuzGv-dtwhhpkH4h_Myn9TlXkQiH0I6BgTNBSQ-ajxo0XvNhSAcaD1rBUisGE3E9__-ujxFDgDCnF1DTOBf4C3T0MdqQuzABQRmbtxPUK2v6neiRM6f4pteuUBtuoyQ497aDv6AnExX6ELiKE_Vqj4-6wPiJjuBSaQAzjC4e3SxhMPqzOqgxYWlF_nx1v04v17U97UWYx5R-iP2RI_OfflbxwGbEDMNSBO_OYdFvfVk8Yshm6XHaBzIkYSFAGme8JZBxbNUmU5Kvjep_qvcbOLE9DB4E-rptFTwENGtgxM3t85zNQTePY6sxjfUrzWn4CWBAgN5yj5wqEqWtmTAgp4RNQA64h50953F69vG-lL91xMnsEIWc9u-yozlj3iGbOkrHMgav3wzZj7zFKUvsBhKuR2AHXOW-w-9avidLs7VoEAzz-EqsaTWHCUFkfvYi71C4JSmzM4d-xzAfeRqywG20-l-9EjRm4w-W2nB2fMOq4t-SZDZOyzhiH7Yz4JtyqNZlodSya7x6pPlM05RzoRol6t1WgSQTrXg4_5y_qQMlHzfDgvxz8BXFR7p2SVu8Lz4rHyPqnD9wpgmeGnGMvl0eUoN1-yeilrOdOkHeu2pJmc-18xZfLJCxg6eMX1b3tdPrAozs09sOf2I4UMb8YON1s-8JqHXjRdWplv0CtIsjudgzWalm4FFAukqydt5aSxMIBDugp4yKv48xPI1ri7p-5knE-4RabFBGLO5N2pxpMgS9YbTeoMZvaLMvKCN-kiwQxTzBUhMcKFj79V4PvqqFIZtgShGkQ6bORdXTz8vcNpAJ_2TZ7s-F-kA3_pDFYwPgDYGPJ2WxZdNl9YJEuR18lcny-btkDoBDhiU4Dryl5_AIc5AYP3XWZElf7bwP_n3Ze8r514JCqRhiQ9TggUKJR7xwyWCVkrx5fVcshRU8l1vIqD_13HQ7chdJMT92QPCVIm9GrOv8_38p1NEJOOLpgVloUSODB8H6J37DLY9-_J9AJGU-Nvrf4vmL1b5A29WFFfvliwhBC9Kfnuf6hu5f2ZjIsAGT0re0QuxD_PevLG2NBkmAEDmFXd7gZzxo-1xtwqRD2BkD_c5vUtr_AJbA69yuuVepiV_OhHqjoMpwOqhwViJV11QfpLUV2lBEQvzPRPmBgPRkdlcYCTmrXG0fH_Hk9xdobD3xwfMzU6UHuMkMj5i4-V6GpylNURIydATYWjq-4AAAAAAAAADRQfIycw"
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
§4.7, §5.5, and §6.5) are additive: `ait-v1.jwt` and `bac-v1.jwt` are byte identical to
their 0.4 form, and the 0.4 entries of `test-keys.json` are unchanged, so a suite that
pins them keeps verifying after it accepts the appended entries. Every CGT and DA fixture
carries the domain-prefixed `trust_class` `acme.com/orders:read` (§4.2), so `cgt-v1.jwt`,
`cgt-v1.mldsa65.jwt`, `cgt-v1.general.json`, `cgt-v1.hybrid.general.json` and `da-v1.jwt`
differ from their 0.4 form in that claim and in the payload and signature bytes it
changes; a suite that pins the earlier bytes regenerates them from the published seeds.
The presenter keys the `cnf` fixtures bind to (`agent-key-1` for the CGT subject,
`agent-key-2` for the delegatee) are appended to `test-keys.json` with `role` `presenter`
and their RFC 7638 thumbprints.

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
- [FIPS 203], Module-Lattice-Based Key-Encapsulation Mechanism Standard.
- [FIPS 204], Module-Lattice-Based Digital Signature Standard.
- [ATX], Agent Trust eXtension credential format (`atx-spec/core.md`).
- [ATP], Agent Trust Protocol.
- [AIP], Agent Identity Protocol (`AIP-SPEC.md`; Section 4.1 is the capability grammar of `trust_class`).

### Informative References
- [A2A], Agent-to-Agent Protocol Specification.
- [MCP], Model Context Protocol Specification.
- [OpenA2A], OpenA2A Platform Architecture.
- [AAP-BROKER-PROFILE], AAP Broker & Resolution Layer (this repository).
- [AAP-CONFORMANCE], AAP Conformance Suite, https://github.com/opena2a-standards/aap-conformance
  (the two reference verifiers, and `conformance.json`, the record of what they verify).
- [RFC 9421], HTTP Message Signatures (a presentation proof format, broker profile §6.8).
- [RFC 9162], Certificate Transparency Version 2.0 (the transparency log in the Registry definition, Section 2).
- [AI Agent Threat Matrix], https://threats.opena2a.org

## Authors' Addresses

Abdel Fane
OpenA2A
Email: abdel@opena2a.org
