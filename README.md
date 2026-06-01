> **[OpenA2A](https://github.com/opena2a-org/opena2a)**: [CLI](https://github.com/opena2a-org/opena2a) · [HackMyAgent](https://github.com/opena2a-org/hackmyagent) · [Secretless](https://github.com/opena2a-org/secretless-ai) · [AIM](https://github.com/opena2a-org/agent-identity-management) · [ATP](https://github.com/opena2a-org/agent-trust-protocol)

# Agent Authorization Protocol (AAP)

The authorization layer of the ATP family. ATP says *who an agent is*; ATX is the signed credential
that carries that trust; **AAP resolves that trust into concrete, scoped access to a real resource —
without the credential value ever entering the agent's reasoning context.**

An agent emits an abstract **grant reference** (`grant://orders-db`). A local, operator-controlled
**broker** verifies the agent's ATX, evaluates resource policy, obtains a scoped credential through
one of three credential-provider modes, performs the operation, and returns only the result. No
secret, temporary credential, backend address, or vendor name ever reaches the agent — or the model
behind it.

## The one principle

OpenA2A owns the protocol and the vocabulary. It owns no one's trust. Nothing in AAP requires a
vendor, cloud, or government to give up their own root. The topology is a **trust program**
(federated conformant Root Authorities), not a single root — the same reason DNS, TLS, OAuth, and
OIDC won.

## The decision / enforcement split

| | States | Owned by | Travels with agent |
|---|---|---|---|
| **ATX** (subject claim) | what an agent *is* — identity, issuer chain, trust level, scan summary, capabilities as trust classes (`db:read`) | issuer | yes |
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

Assume and Exchange leave the broker holding nothing but one rotating key — prefer them.

## Status

`0.1.0-draft`. Authored in the open; intended for submission as an IETF Internet-Draft. The
normative core is written to be stable; the extensible edge is expected to evolve. See
[`AAP-SPEC.md`](./AAP-SPEC.md).

## Reference implementation

A v1 **Exchange** broker extends the existing Secretless broker, validated against Okta (RFC 8693).
The developer surface is the AIM `@agent.perform_action` decorator. See
[`examples/orders-db-exchange.md`](./examples/orders-db-exchange.md) and
[`AAP-SPEC.md` §14](./AAP-SPEC.md#14-reference-implementation-informative).

## Specification

- [`AAP-SPEC.md`](./AAP-SPEC.md) — the full specification.
- [`examples/`](./examples/) — worked examples (resolution flow, policy grammar, transport bindings).

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
