> **OpenA2A specs** · [did:opena2a](https://github.com/opena2a-standards/did-method-opena2a) · [AIP](https://github.com/opena2a-standards/agent-identity-protocol) · [ATX](https://github.com/opena2a-standards/atx-spec) · [ATP](https://github.com/opena2a-standards/agent-trust-protocol) · **AAP** · [AIM](https://github.com/opena2a-org/agent-identity-management) · [all specs ↗](https://specs.opena2a.org)

# Agent Authorization Protocol (AAP)

The authorization layer of the ATP family. ATP says *who an agent is*; ATX is the signed credential
that carries that trust; **AAP resolves that trust into concrete, scoped access to a real resource,
without the credential value ever entering the agent's reasoning context.**

An agent emits an abstract **grant reference** (`grant://orders-db`). A local, operator-controlled
**broker** verifies the agent's ATX, evaluates resource policy, obtains a scoped credential through
one of three credential-provider modes, performs the operation, and returns only the result. No
secret, temporary credential, backend address, or vendor name ever reaches the agent, or the model
behind it.

## The one principle

OpenA2A owns the protocol and the vocabulary. It owns no one's trust. Nothing in AAP requires a
vendor, cloud, or government to give up their own root. The topology is a **trust program**
(federated conformant Root Authorities), not a single root, the same reason DNS, TLS, OAuth, and
OIDC won.

## The decision / enforcement split

| | States | Owned by | Travels with agent |
|---|---|---|---|
| **ATX** (subject claim) | what an agent *is*, identity, issuer chain, trust level, scan summary, capabilities as trust classes (`db:read`) | issuer | yes |
| **Broker policy** (resource grant) | what a *resource* gives an agent holding a trust class | resource operator | no |
| **Broker** (enforcement) | intersects the two; resolves `grant://name` to a concrete action | resource operator | n/a |

> **Trust is not authorization, and trust is not transitive.** A valid ATX is never permission to
> touch a resource. Authorization exists only where a local broker policy grants it. Default-deny.

## The three CPI modes

| Mode | What the provider does | Broker's secret surface |
|---|---|---|
| **Retrieve** | holds a secret, returns its value (broker proxies or injects into an ephemeral worker) | one root credential **per backend** |
| **Assume** | takes an identity proof, returns short-lived role-scoped credentials (cloud STS) | **one rotating signing key** |
| **Exchange** | OAuth-style token exchange (RFC 8693) for a scoped downstream token | **one rotating signing key** |

Assume and Exchange leave the broker holding nothing but one rotating key, prefer them.

## Two layers

AAP is defined in two documents:

- **[`AAP-SPEC.md`](./AAP-SPEC.md)**, the AAP **token model**: Agent Identity Token (AIT),
  Capability Grant Token (CGT), Delegation Assertion (DA), Behavioral Attestation Claim (BAC),
  cross-org federation, and revocation propagation. What the credentials contain, how they are
  signed and verified.
- **[`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md)**, the **broker & resolution layer**: how
  an agent obtains and exercises those tokens via a `grant://` reference and a local broker,
  without the credential value ever entering its reasoning context. Defines the
  decision/enforcement split, the Credential Provider Interface, and two-tier conformance.

## Status

`0.2.0-draft`. Authored in the open; intended for submission as an IETF Internet-Draft. The
0.2.0 reconciliation merges the March 2026 AAP token-model draft with the broker/resolution layer
into one coherent protocol (ATC → ATX, `did:atp:` → `did:opena2a:`).

## Reference implementation

A v1 **Exchange** broker extends the existing Secretless broker, validated against Okta (RFC 8693).
The developer surface is the AIM `@agent.perform_action` decorator. See
[`examples/orders-db-exchange.md`](./examples/orders-db-exchange.md) and
[`AAP-BROKER-PROFILE.md` §14](./AAP-BROKER-PROFILE.md#14-reference-implementation-informative).

## Specification

- [`AAP-SPEC.md`](./AAP-SPEC.md), the AAP token model (AIT/CGT/DA/BAC, federation, revocation).
- [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md), the broker & resolution layer.
- [`examples/`](./examples/), worked examples (resolution flow, policy grammar, transport bindings).

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
