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

## Use cases

### The key an agent should never hold

You paste an API key into an agent's environment. The agent reads web pages, documents and tool results, and it cannot reliably tell your instructions from text hidden in what it reads. One hidden instruction can ask it to send the key somewhere, and whoever receives it has standing access to your customers' data for as long as the key lives.

AAP removes the key from the agent. The agent emits an abstract `grant://name` reference. A local broker verifies the agent's ATX, evaluates the resource policy, obtains a scoped credential through one of three provider modes, performs the operation and returns the result. No secret, temporary credential, backend address or vendor name reaches the agent or the model behind it.

What you can do today: run the token conformance suite, then read the worked example [`examples/orders-db-exchange.md`](./examples/orders-db-exchange.md).

```bash
git clone https://github.com/opena2a-standards/aap-conformance
cd aap-conformance
npm install
node verifiers/node/verify.mjs fixtures
# summary: 44 pass, 0 fail (44 fixtures)
```

Where it stops today: the Exchange broker is implemented as a library with an end-to-end conformance test, but the shipped `secretless broker` daemon does not yet construct the grant resolver, so `POST /grant` returns 404 until grant-binding configuration lands (see the Reference implementation section below).

### An agent checks out with your money

An agent authorized to buy holds a stored card. It can be argued into a second purchase, and a helper agent it delegates to inherits the whole card. Stored payment credentials give software standing authority, with an expiry measured in years and no per-operation scope.

Under AAP the agent holds a Capability Grant Token that names the trust class and scope a broker will honor; the broker denies anything outside a matching policy clause by default; and a Delegation Assertion must stay within its delegator's grant, so a delegated helper gets less, never more. A valid ATX is never permission on its own.

What you can do today: `fixtures/da-compact-scope-superset.json` in the conformance suite rejects a delegation wider than its delegator, `fixtures/cgt-compact-expired.json` rejects an expired grant, and the valid token bytes are in [`examples/tokens/`](./examples/tokens/).

Where it stops today: the same daemon limit applies. The tokens can be minted and verified; the shipped daemon does not yet resolve a `grant://` reference against them.

Why you can check this yourself: [`AAP-SPEC.md`](./AAP-SPEC.md) and [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md); the Internet-Draft [draft-fane-opena2a-aap](https://datatracker.ietf.org/doc/draft-fane-opena2a-aap/); [aap-conformance](https://github.com/opena2a-standards/aap-conformance), 44 byte-pinned fixtures with Node and Python verifiers; the published token bytes in [`examples/tokens/`](./examples/tokens/); and the broker library in [Secretless](https://github.com/opena2a-org/secretless-ai) under `src/broker/`.

## Contributing

This specification is early and authored in the open. We are looking for co-authors, an independent second implementation, and review of the authorization and delegation model before it goes to an external standards body. See [CONTRIBUTING.md](CONTRIBUTING.md).

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

`AAP-SPEC.md` is at `0.5.1-draft`; the companion `AAP-BROKER-PROFILE.md` is at `0.4.1-draft`.
Authored in the open as an IETF Internet-Draft: `draft-fane-opena2a-aap-02` (the 0.5.1-draft text,
submitted 2026-10-02) is the current revision on the
[datatracker](https://datatracker.ietf.org/doc/draft-fane-opena2a-aap/); its source and rendered
text are in this repository. Each document carries its own version at the top;
`CHANGELOG.md` records what moved between drafts and which draft revision pairs with which version.

## Reference implementation

A v1 **Exchange** broker (RFC 8693) is implemented in the Secretless broker library, with an
end-to-end conformance test proving the §4 invariant over the broker's Unix socket. Two limits are
worth stating plainly rather than discovering later. The exchange is exercised against a fake
transport injected into the provider adapter, not against a live identity-provider tenant. And the
shipped `secretless broker` daemon does not yet construct the grant resolver, so `POST /grant`
returns 404 until an operator-facing grant-binding configuration lands
([opena2a-standards/agent-authorization-protocol#1](https://github.com/opena2a-standards/agent-authorization-protocol/issues/1)).

The developer surface is the `@agent.perform_action` decorator of
OpenA2A AIM (Agent Identity Management). See
[`examples/orders-db-exchange.md`](./examples/orders-db-exchange.md) and
[`AAP-BROKER-PROFILE.md` §14](./AAP-BROKER-PROFILE.md#14-reference-implementation-informative).

## Specification

- [`AAP-SPEC.md`](./AAP-SPEC.md), the AAP token model (AIT/CGT/DA/BAC, federation, revocation).
- [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md), the broker & resolution layer.
- [`examples/`](./examples/), worked examples (resolution flow, policy grammar, transport bindings).

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
