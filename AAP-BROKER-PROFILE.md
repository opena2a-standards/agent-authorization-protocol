# Agent Authorization Protocol, Broker & Resolution Layer

## Resolving Agent Trust Into Resource Access Without Exposing Credentials

**Version:** 0.2.0-draft
**Authors:** OpenA2A
**Date:** June 2026
**Status:** Draft companion to [`AAP-SPEC.md`](./AAP-SPEC.md). Intended for the IETF Internet-Draft.

> **This is the resolution/enforcement layer of AAP.** The AAP token model, Agent Identity
> Token (AIT), Capability Grant Token (CGT), Delegation Assertion (DA), Behavioral Attestation
> Claim (BAC), federation, and revocation propagation, is defined in [`AAP-SPEC.md`](./AAP-SPEC.md).
> This document defines how an agent *obtains and exercises* those tokens without the credential
> value ever entering its reasoning context. Concept mapping is in §0.

---

## 0. Relationship to the AAP token model

This profile introduces no parallel credential format; it consumes the AAP tokens defined in
[`AAP-SPEC.md`](./AAP-SPEC.md). The vocabulary maps as follows:

| This document | AAP-SPEC.md token model |
|---|---|
| The presented ATX (subject claim) | the credential the **Agent Identity Token (AIT)** references |
| The **broker assertion** the broker mints from the ATX | a **Capability Grant Token (CGT)** / **Delegation Assertion (DA)** |
| **Exchange** mode (RFC 8693 token exchange) | a realization of the **Delegation Assertion (DA)** ("analogous to RFC 8693") |
| Revocation via the cached, federated CRL | the **Revocation Propagation Protocol** (AAP-SPEC §7.2) |
| Trust level / scan summary / issuer chain used in policy | claims carried by the AIT/ATX |

Where this document says "broker assertion," read "the CGT/DA the broker mints." Where it says
"ATX," read "the credential the AIT references." The broker is the component that mints, exchanges,
and enforces the AAP tokens.

---

## Abstract

The Agent Trust Protocol (ATP) answers *who an agent is* and *what it is trusted to be*. The Agent
Trust eXtension (ATX) is the signed credential that carries that trust. This **broker & resolution
layer of AAP** resolves an agent's trust into concrete, scoped access to a real downstream resource,
**without the credential value ever entering the agent's reasoning context, and therefore without it
ever reaching a language model provider.**

AAP separates two things that are routinely and dangerously conflated. The *policy decision*,
whether an agent holding a given trust class may use a resource, is expressed against the portable,
signed ATX. The *policy enforcement*, turning that decision into a usable credential for a specific
backend, is performed locally by a **broker** that the resource operator controls. An agent emits
only an abstract **grant reference** of the form `grant://name`. The broker verifies the agent's
ATX, evaluates local policy, obtains a scoped credential through one of three credential-provider
modes, performs the requested operation, and returns only the *result*. No secret, no temporary
credential, no backend address, and no vendor name is ever placed where the agent, or its model,
can read it.

This specification defines the grant reference, the Credential Provider Interface (CPI) and its
three modes (Retrieve, Assume, Exchange), the resolution flow, the federation-aware policy grammar,
and the future-proofing rules (version negotiation, cryptographic agility, extensible claims,
abstract identifiers, layer separation, and pluggable transport) that let AAP evolve for decades
without a credential redesign.

AAP is designed to complement, not replace, existing standards:

- **ATP / ATX**, AAP consumes the ATX as its subject claim. It does not redefine identity, trust
  scoring, revocation, or the transparency log; it reuses them.
- **OAuth 2.0 Token Exchange (RFC 8693)**, the Exchange mode is a profile of RFC 8693. The broker
  acts as an OAuth-style authorization-server client performing a token exchange for a scoped
  downstream token.
- **OAuth 2.0 / OpenID Connect**, in Exchange and Assume modes the broker acts as its own
  OIDC-style identity provider, minting short-lived assertions the downstream is configured to trust.
- **W3C DID Core**, agent and authority identifiers are `did:opena2a` DIDs.
- **AI Agent Threat Matrix**, AAP is a control against the credential-harvest and exfiltration
  attack classes (Section 12).

---

## Status of This Document

This is a working draft. OpenA2A authors AAP in the open and holds the pen until it is contributed
to the IETF as an Internet-Draft. The normative core (Sections 3–6, 9) is written to be stable; the
extensible edge (Sections 7–8, 10) is expected to evolve. Where this document and the OpenA2A
reference implementation in Secretless AI disagree, the disagreement is a bug in one of them and
MUST be reconciled, not silently resolved in either direction.

---

## 1. Terminology

The key words "MUST", "MUST NOT", "REQUIRED", "SHALL", "SHALL NOT", "SHOULD", "SHOULD NOT",
"RECOMMENDED", "MAY", and "OPTIONAL" in this document are to be interpreted as described in
BCP 14 (RFC 2119, RFC 8174) when, and only when, they appear in all capitals.

- **Agent**, an autonomous software actor, typically driven by a language model, that takes
  actions on behalf of a principal. The agent's *reasoning context* is the set of tokens visible to
  its model, including everything an upstream model provider receives.
- **ATX (Agent Trust eXtension)**, the signed, portable credential defined by ATP that states what
  an agent *is*: its identity, issuer and issuer chain, trust level, scan summary, and capabilities
  expressed as trust classes. ATX is the *subject claim* in AAP. (ATX is the current name for the
  credential formerly called ATC; implementations may still reference the legacy `atc` name.)
- **Trust class**, a capability expressed in abstract trust terms, e.g. `db:read`, `orders:read`.
  A trust class names *what an agent is trusted to do in the abstract*. It MUST NOT name a backend,
  a host, a path, a role, or a vendor.
- **Grant reference**, the abstract identifier an agent emits instead of a secret, of the form
  `grant://name` (Section 4). It names a logical resource the agent was granted. It MUST NOT encode
  a backend address, a credential, or a CPI mode.
- **Broker**, the AAP enforcement point. A local, operator-controlled process that verifies an
  ATX, evaluates resource policy, resolves a grant reference through a credential provider, performs
  the requested operation, and returns only the result.
- **Broker policy**, the local, operator-owned, deployment-specific ruleset that maps a trust
  class to a concrete resource and CPI mode (the *resource grant*). It is never part of the ATX.
- **Credential Provider Interface (CPI)**, the interface a backend implements to plug into the
  broker (Section 5). A provider declares which modes it supports. Providers are configuration,
  never protocol.
- **CPI mode**, one of Retrieve, Assume, Exchange (Section 5).
- **Broker assertion**, a short-lived token the broker mints from verified ATX claims, signed with
  the broker's own signing key, used as the subject token in Assume and Exchange modes.
- **ATP Trust Program**, the governance and conformance program under which participants operate
  conformant **Root Authorities** and cross-trust. A sovereign or hyperscaler operates a conformant
  Root Authority; it does not "join" OpenA2A.

---

## 2. Design Principles

Every choice in AAP answers to one test: **does adopting it require any vendor, cloud, or government
to give up their own root, their own identity system, or their own trust authority?** If yes, it is
wrong. This is why DNS, TLS, OAuth, and OIDC became universal and proprietary trust centers did not.
OpenA2A owns the protocol and the vocabulary; it owns no one's trust.

A direct, settled consequence: the topology is a **trust program, not a single root**. OpenA2A
defines AAP, operates the default community Root Authority, and publishes conformance and peering
rules. Everyone else operates conformant Root Authorities and cross-trusts (Section 7).

The following principles are normative and are referenced by number throughout:

1. **Versioned and negotiated**, every protocol message, policy grammar, claim schema, and
   signature carries a version; two parties negotiate the highest version they share (Section 8.1).
2. **Cryptographically agile**, the signature suite is a named, swappable field, never a hardcoded
   assumption (Section 8.2).
3. **Extensible claims with safe ignore**, each claim is marked mandatory-to-understand or
   optional-to-ignore; unknown optional claims are ignored safely (Section 8.3).
4. **Abstract identifiers**, no vendor or product name appears in any protocol structure, ever.
   The wire carries a CPI mode and a grant reference; vendors are configuration (Section 8.4).
5. **The trust layer never embeds the resource layer**, the decision/enforcement split is a
   permanent invariant (Section 3).
6. **Pluggable transport and discovery**, how a broker fetches keys, revocation, or an ATX is a
   binding, not the trust core (Section 8.5).

---

## 3. Architecture: The Decision / Enforcement Split

This is the structural heart of AAP. The policy *decision* and the policy *enforcement* are kept
separate and MUST NOT merge.

### 3.1 The subject claim (ATX)

The ATX states, in abstract trust terms, what an agent **is**: its identity, its issuer and issuer
chain, its trust level, its scan summary, and its capabilities **as trust classes** such as
`db:read`, never as resource bindings. The ATX is signed, portable, and travels with the agent. It
is defined by ATP/ATX; AAP does not redefine it. A capability in an ATX MUST NOT name a backend, a
path, or a role.

### 3.2 The resource grant (broker policy)

The broker policy states what a given **resource** gives to an agent that holds a given capability.
It is local, operator-owned, and deployment-specific. It is the only place a trust class is mapped
to a concrete resource and CPI mode. The broker policy is never part of, and never travels with, the
ATX.

### 3.3 The broker as enforcement point

The broker is the enforcement point that **intersects** the subject claim and the resource grant and
resolves a grant reference to a concrete action. This split is what lets the resource world, clouds,
SaaS, databases, payment rails, evolve independently of the credential.

### 3.4 Trust is not authorization

> **Normative warning.** Trust is **not** authorization, and trust is **not** transitive. A valid,
> highly-trusted ATX is a statement about an agent's identity and posture; it is **not** permission
> to touch any specific resource. "Easy to establish verifiable trust" MUST NOT quietly become "any
> federated agent can read your database." Authorization exists only where a local broker policy
> explicitly grants it. A broker MUST default-deny: absent a matching policy clause, every grant
> resolution fails.

---

## 4. Grant References and Context Hygiene

### 4.1 The core invariant

An agent's reasoning context, and therefore anything that reaches a language-model provider, MAY
contain **only** a grant reference. It MUST NOT contain:

- a secret value;
- a temporary or scoped credential of any kind;
- a backend address, hostname, connection string, or path;
- a vendor or product name;
- any signal from which the resolving CPI mode (Retrieve vs Assume vs Exchange) can be inferred.

The agent emits `grant://name`; the broker does everything else. This is the invariant the entire
protocol exists to defend, and it is the property the conformance test in the reference
implementation verifies directly.

### 4.2 Syntax

```
grant-reference = "grant://" grant-name
grant-name      = 1*( unreserved )   ; per RFC 3986 unreserved
```

A grant reference is an opaque logical name. It is deliberately *less* expressive than schemes that
embed a backend and path (for example a `secret://backend/path` reference): embedding a backend
identifier would violate Principle 4 and leak resolution topology into the agent context. A grant
name carries no structure a model could use to learn what stands behind it.

Example: `grant://orders-db` names the logical "orders database" grant. Whether it resolves through
a secret store (Retrieve), a cloud STS role (Assume), or an OAuth token exchange (Exchange) is known
only to the broker.

### 4.3 Binding to a request

A grant reference is presented to the broker together with the agent's ATX (Section 6). The grant
reference travels on the broker-facing channel only. It MUST NOT be logged into, echoed into, or
returned to the agent context alongside any resolved material.

---

## 5. The Credential Provider Interface (CPI)

A backend plugs into the broker by implementing the CPI and declaring which modes it supports. The
three modes correspond to the only three things a credential authority can do. The set is
extensible by the versioning rule (Section 8.1) should the world invent a fourth.

### 5.1 Mode: Retrieve

The provider **holds a secret and returns its value.** The broker either proxies the downstream
operation itself so the value never leaves the broker, or injects the value into an ephemeral worker
(Section 6.5). Secret stores, OS keychains, and password/vault platforms are Retrieve providers.
*Dynamic secrets* (short-lived secrets minted on demand) fold in here with an ephemeral flag, they
are not a new mode.

> Scope note: most Retrieve work is roadmapped in the Secretless reference implementation
> (features 170–199). AAP defines the mode; implementations SHOULD reuse that work rather than
> rebuild it.

### 5.2 Mode: Assume

The provider **takes an identity proof and returns short-lived, role-scoped credentials.** There is
no standing secret. Cloud STS-style role assumption is Assume. The identity proof is the broker
assertion (Section 11).

### 5.3 Mode: Exchange

The provider **is an OAuth-style authorization server, and the broker performs a token exchange**
(RFC 8693) to obtain a scoped bearer token for a downstream API. There is no standing secret.
Enterprise IdPs are Exchange providers. This is the mode implemented in the v1 reference
implementation (Section 13).

### 5.4 The security property to lead with

In **Retrieve**, the broker must hold a root credential to every backend it talks to, so its own
secret surface grows with each backend. In **Assume** and **Exchange** the broker holds nothing but
**one rotating signing key**. The no-standing-secret modes shrink the broker's own attack surface to
a single key. Deployments SHOULD prefer Assume and Exchange wherever the backend supports them.

### 5.5 Interface shape (non-normative)

A CPI provider exposes, at minimum: the set of modes it supports; a `resolve` operation that takes a
verified-ATX-derived context plus a resource binding and returns either a proxied result or a
scoped, short-lived credential confined to an ephemeral worker; and a declaration of the scope it
will request downstream. The provider never sees the agent's reasoning context and never receives
the grant reference in a form it can echo back to the agent.

---

## 6. Resolution Flow

A broker MUST perform the following steps, in order, for every grant resolution. Any failure
produces a typed, opaque denial (Section 6.6).

1. **Receive** the request on the broker-facing channel: the presented ATX plus a grant reference.
2. **Verify the ATX locally**, reusing the ATP/ATX verification path: signature(s), suite, validity
   window (issuedAt/expiresAt with bounded clock skew), and the cached, federated CRL. Revocation
   rides entirely on the ATX and the federated CRL, AAP defines no separate revocation system.
   Revoking an agent's ATX MUST remove its access within the existing CRL propagation window.
3. **Negotiate version** (Section 8.1) if not already established for the channel.
4. **Evaluate policy**: match the grant reference and the verified ATX's trust class against local
   broker policy, selecting a concrete CPI provider, mode, and downstream scope. Default-deny.
5. **Resolve** through the selected CPI provider:
   - **Retrieve**, proxy the operation in the broker, or inject the value into an ephemeral worker.
   - **Assume**, mint a broker assertion from ATX claims; obtain short-lived role-scoped credentials.
   - **Exchange**, mint a broker assertion; perform the RFC 8693 token exchange; obtain a scoped
     downstream token.
6. **Act** inside an ephemeral worker (Section 6.5) using the scoped credential, and return **only
   the result** of the operation to the agent.
7. **Audit** the verification, decision, resolution, and result (success or denial) through the
   signed audit path (Section 6.7).

### 6.5 The ephemeral worker

Where a credential value or scoped token must exist to perform the operation, it MUST be confined to
an ephemeral worker that is isolated from the agent process and its memory. The temporary token MAY
exist briefly in that worker. It MUST NOT enter the agent process or the agent context. Only the
result of the operation returns to the agent.

### 6.6 Denials

A denial MUST be a typed error that reveals nothing sensitive about policy internals or backend
topology, no backend name, host, scope, provider, or reason that could be used to map the
deployment. The same opaque denial is returned whether the grant is unknown, the policy denies, the
ATX is untrusted, or the provider fails. Diagnostic detail goes to the audit log, not to the agent.

### 6.7 Audit

Every verification, decision, resolution, and denial MUST be written to a signed audit log. The
audit record MUST NOT contain any credential value or downstream token. Implementations SHOULD reuse
the existing AIM signed-audit path rather than build a new one.

---

## 7. Federation-Aware Policy Grammar

The v1 reference implementation is single-org, but the policy grammar is defined so federation lights
up later **with no grammar change.** A policy clause MUST be able to match not only a local agent
identity but also the federation attributes of the presented ATX: the **issuer**, the **issuer
chain**, the **trust level**, the **scan summary**, and a **jurisdiction** claim (Section 9).

### 7.1 Canonical federation clause

The grammar MUST be able to express the following clause, even though a single-org v1 broker need
not evaluate the issuer-chain and jurisdiction predicates:

> *Any agent whose issuer chain includes a node in my trusted-partners set, at OASB level L2 or
> higher, holding capability `orders:read`, is granted the named resource `grant://orders-db`,
> scoped to read-only, for a short fixed window.*

Expressed in the (non-normative) policy grammar:

```yaml
- grant: grant://orders-db
  match:
    issuerChainIncludes: { partnersSet: trusted-partners }   # federation attribute
    oasbLevel: ">=L2"                                         # from ATX scanSummary
    trustClass: orders:read                                   # ATX capability
    jurisdiction: { in: [us, eu] }                            # Section 9 (v1: parsed, not enforced)
  resolve:
    mode: exchange
    provider: orders-idp           # configuration; never on the wire
    scope: orders.read
    ttl: 300s
```

A v1 broker MUST parse the full clause (including `issuerChainIncludes` and `jurisdiction`) and MAY
treat the federation-only predicates as always-satisfied within its own org while still enforcing
`trustClass`, `oasbLevel`, `mode`, `scope`, and `ttl`.

### 7.2 The Trust Program and Root Authorities

Participants operate **Root Authorities** under the ATP Trust Program. A sovereign or hyperscaler
operates a conformant Root Authority and cross-trusts peers via the ATP federation model (issuer
chains, trust lists, cross-border cosigning). AAP adds no new federation transport: it consumes the
issuer-chain and trust-level attributes that ATX already carries. v2 lights up cross-broker
verification on the **same broker assertion** a broker already mints for its own agents (Section 11);
v3 adds sovereign Root Authorities and jurisdiction *enforcement*. Both are governance and peering
plumbing, not a credential redesign.

---

## 8. Future-Proofing (Normative)

These are requirements, built into the protocol structure from the first version.

### 8.1 Versioning and negotiation

Every AAP protocol message, the policy grammar, every claim schema, and every signature carries a
version. Two parties negotiate the **highest version they both support**.

- A broker advertises a set of supported AAP versions in its discovery document (Section 8.5).
- A client selects the highest version in the intersection and stamps it on the request.
- If the intersection is empty, the broker returns a typed `version-unsupported` denial naming the
  set it supports (this is the one denial that MAY reveal supported versions, because versions are
  not sensitive topology).
- ATX already carries a version field; AAP follows that lead and additionally defines the *active
  negotiation handshake* that ATP/ATX/AIP leave implicit.

### 8.2 Cryptographic agility

The signature suite is a **named, swappable field**, never a hardcoded assumption. The default suite
is **hybrid Ed25519 + ML-DSA-65** (FIPS 204), matching ATX's per-signature `algorithm` model: a
credential carrying an ML-DSA-65 signature requires at least one ML-DSA-65 signature **and** at
least one Ed25519 signature to verify. Adding or retiring a suite is a suite-identifier change and a
negotiation (Section 8.1), never a new credential format. A verifier MUST reject a credential whose
declared suite it does not support rather than silently downgrade.

### 8.3 Extensible claims with safe ignore

Each claim is marked **mandatory-to-understand** or **optional-to-ignore**. A verifier that
encounters an unknown *optional* claim MUST ignore it safely and still accept the credential. A
verifier that encounters an unknown *mandatory-to-understand* claim MUST reject. This lets new claim
types, attributes, jurisdictions, and vendor-specific fields be added indefinitely without
invalidating agents already in the field.

### 8.4 Abstract identifiers

No vendor or product name appears in any protocol structure, ever. The wire carries a CPI **mode**
and a **grant reference**. Backend identity, provider selection, hostnames, and scopes live only in
broker configuration. A reference implementation that leaks a vendor name (for example "Okta") into
the broker core rather than confining it to a thin provider adapter has a **bug against Principle 4**.

### 8.5 Pluggable transport and discovery

How a broker finds a peer's keys, fetches a CRL, or receives an ATX, over an HTTP header, an A2A
agent card, or an MCP manifest, is a **binding**, not the trust core. AAP defines the bindings
separately from the core so new transports get new bindings while the core is untouched. The
initial bindings are:

- **HTTP**, ATX presented in an `Agent-Trust-Credential` header (as in ATP).
- **A2A agent card**, ATX embedded under the `atp` object of `/.well-known/agent.json`.
- **MCP manifest**, ATX referenced from the server manifest.

A broker publishes a discovery document (supported AAP versions, supported suites, and static public
key material for its broker-assertion signing key) at a well-known location on the **operator's own
domain**. OpenA2A is never in the hot path of a resolution.

---

## 9. Jurisdiction and Residency

ATX as currently specified carries no jurisdiction claim. AAP reserves the claim slot and the
grammar slot now so cross-country enforcement in a later version needs no redesign.

- **ATX claim slot (proposed extension):** an optional, optional-to-ignore `jurisdiction` claim
  naming the region(s) in which the agent is authorized to operate (for example ISO 3166-1 codes or
  a named region set). Marked optional-to-ignore so v1 verifiers accept ATXs that omit it.
- **Policy grammar slot:** a `jurisdiction` predicate (Section 7.1) able to constrain a grant, for
  example, "data may not be accessed by an agent operating outside the `eu` region."

A v1 broker MUST parse the `jurisdiction` predicate but is **not** required to enforce it.
Enforcement is a v3 concern under sovereign Root Authorities.

---

## 10. Two-Tier Conformance

AAP is **strict about a tiny core and liberal about everything else.** This is the governance answer
to universal adoption: a conservative core and a permissive edge keep the standard both universal and
coherent.

- **Mandatory core (slow-changing), policed by the conformance program:**
  - the grant-reference syntax and the context-hygiene invariant (Section 4);
  - the decision/enforcement split and default-deny (Section 3);
  - the resolution-flow ordering and the ephemeral-worker confinement (Section 6);
  - version negotiation (8.1), cryptographic agility (8.2), and safe-ignore claim handling (8.3);
  - the meaning of the base trust-class and federation attributes consumed from the ATX.
- **Extensible edge (fast-changing), out of conformance scope:** CPI provider implementations,
  policy-grammar vendor extensions, optional claims, additional transports and bindings, and
  deployment-specific scopes.

The conformance program polices the core and stays out of the edge.

---

## 11. The Broker as Its Own Identity Provider

For Exchange and Assume, the broker acts as its **own OIDC-style identity provider.** It mints a
short-lived **broker assertion** whose claims derive from the verified ATX (subject, trust class,
trust level, and a bounded validity window), signed with the broker's signing key. The downstream
authorization server (Exchange) or STS (Assume) is configured **once** to trust the broker's IdP,
the same way keyless CI authentication configures a downstream to trust a federated issuer.

- The broker's IdP signing key is the existing short-lived **delegated signing key** (30-day default)
  and it **rotates**.
- The only thing the downstream must reach is **static public key material**, publishable on the
  operator's own domain.
- The **same** assertion a broker mints for its own agents is what a peer broker will verify for a
  foreign agent in v2 federation. The federation-aware grammar (Section 7) and issuer-chain matching
  exist for exactly this reason. v2 is the identical primitive applied across an org boundary.

This is consistent with **Zero Failures**: OpenA2A operates the default community Root Authority but
sits outside every resolution hot path.

---

## 12. Security Considerations

### 12.1 Threat model and taxonomy mapping

AAP is a control against the **credential-harvest** and **exfiltration** attack classes of the AI
Agent Threat Matrix (https://threats.opena2a.org). By construction, no credential value enters the
agent context, which removes the substrate those techniques operate on. AAP references the following
technique IDs (resolve the canonical titles from the live taxonomy):

- **T-3002, Environment Variable Exposure.** AAP keeps secrets out of the agent's environment;
  there is no env var for an agent or a compromised tool to read.
- **T-3003, Tool Response Credential Capture.** The broker returns only operation results, never a
  credential, so there is nothing to capture in a tool response that crosses the context.
- **T-3006, Context Window Credential Leak.** The context-hygiene invariant (Section 4) guarantees
  no credential ever entered the window, so none can leak from it.
- **T-8002, HTTP Callback (and the broader T-8xxx exfiltration class).** Even a fully compromised
  agent can exfiltrate only grant references and operation results, not reusable credentials.

A HackMyAgent check that verifies a deployment conforms to AAP SHOULD cite these IDs in `T-NNNN`
form so AAP stays inside the four-layer research architecture rather than orphaned beside it.

### 12.2 Trust is not authorization

Restating Section 3.4 as a security property: a valid ATX is necessary but not sufficient for
access. The broker's default-deny policy is the authorization boundary. Federation widens *who can
present a verifiable identity*; it MUST NOT widen *what any identity may touch*.

### 12.3 Broker key compromise

In Assume/Exchange the broker holds one signing key. Its compromise is serious but bounded: the key
rotates (30-day default), the downstream trusts only the current published public key, and revoking
the key at the downstream severs all minted assertions at once. This is a far smaller blast radius
than Retrieve's per-backend root credentials, which is why the no-standing-secret modes are
preferred (Section 5.4).

### 12.4 Denial opacity

Opaque denials (Section 6.6) prevent an adversary from mapping a deployment's backends, providers,
or policy by probing grant references. The audit log retains full diagnostic detail for operators.

---

## 13. Conformance Levels

| Level | Name | Requirements |
|-------|------|--------------|
| **1** | Context Hygiene | Grant-reference syntax; the context-hygiene invariant (Section 4); decision/enforcement split with default-deny (Section 3); ATX verification + CRL before resolution (Section 6); ephemeral-worker confinement; opaque denials; signed audit. At least one CPI mode implemented. |
| **2** | Agile + Negotiated | Level 1 + version negotiation (8.1) + cryptographic agility with the hybrid default suite (8.2) + safe-ignore claim handling (8.3) + the published discovery document (8.5). |
| **3** | Federated | Level 2 + full federation-aware policy evaluation (issuer chain, trust level, scan summary) + cross-broker verification of peer broker assertions + jurisdiction enforcement (Section 9). |

The v1 reference implementation (Section 14) targets **Level 1** with the **Exchange** mode and the
structural slots for Levels 2–3 in place.

---

## 14. Reference Implementation (Informative)

The OpenA2A reference implementation lives in Secretless AI. It extends the existing Secretless
broker (a local daemon reachable over a Unix socket) with:

- the `grant://` scheme;
- the CPI abstraction with all three modes declared and **Exchange** implemented;
- an ATX verification step before resolution, reusing the AIM/ATP verification + CRL path;
- an RFC 8693 Exchange provider in which the broker mints a broker assertion from ATX claims and
  exchanges it for a scoped downstream token, with **Okta as the first conformance test** behind a
  thin provider adapter (no vendor name in the broker core);
- an ephemeral worker that performs the downstream operation and returns only the result.

The developer surface is the existing AIM `@agent.perform_action` decorator: an agent references a
grant, the SDK talks to the broker daemon, the broker does the rest.

Deliverable 3 is a conformance test that proves the Section 4 invariant directly: an agent obtains
and uses a scoped downstream token through a grant reference, and at no point does any credential
value or backend identifier appear in the agent context.

---

## 15. IANA / Registry Considerations

A future Internet-Draft will request registries for: AAP protocol versions; CPI mode identifiers;
signature suite identifiers (coordinated with the ATX suite registry); and the `grant` URI scheme.
Until then, identifiers are managed in this specification.

---

## 16. References

### Normative

- **RFC 2119 / RFC 8174**, Key words for requirement levels.
- **RFC 3986**, Uniform Resource Identifier (URI): Generic Syntax.
- **RFC 8693**, OAuth 2.0 Token Exchange.
- **ATP**, Agent Trust Protocol specification (OpenA2A).
- **ATX**, Agent Trust eXtension credential format (OpenA2A; see `atx-spec/core.md`).
- **FIPS 204**, Module-Lattice-Based Digital Signature Standard (ML-DSA).
- **RFC 8032**, Edwards-Curve Digital Signature Algorithm (EdDSA / Ed25519).

### Informative

- **RFC 6749 / RFC 6750**, OAuth 2.0 and Bearer Token Usage.
- **OpenID Connect Core 1.0.**
- **W3C DID Core 1.0** and the `did:opena2a` method.
- **AI Agent Threat Matrix**, https://threats.opena2a.org (techniques T-3002, T-3003, T-3006, T-8002).
- **OASB**, Open Agent Security Benchmark (levels L1–L3).
