# AAP overview

The principle AAP is built on, the split between deciding and enforcing access, the three
credential-provider modes, and the two documents that define the protocol.

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

- **[`AAP-SPEC.md`](../AAP-SPEC.md)**, the AAP **token model**: Agent Identity Token (AIT),
  Capability Grant Token (CGT), Delegation Assertion (DA), Behavioral Attestation Claim (BAC),
  cross-org federation, and revocation propagation. What the credentials contain, how they are
  signed and verified.
- **[`AAP-BROKER-PROFILE.md`](../AAP-BROKER-PROFILE.md)**, the **broker & resolution layer**: how
  an agent obtains and exercises those tokens via a `grant://` reference and a local broker,
  without the credential value ever entering its reasoning context. Defines the
  decision/enforcement split, the Credential Provider Interface, and two-tier conformance.
