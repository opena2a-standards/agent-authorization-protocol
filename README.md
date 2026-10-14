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

## Specification

- [`AAP-SPEC.md`](./AAP-SPEC.md), the AAP token model (AIT/CGT/DA/BAC, federation, revocation).
- [`AAP-BROKER-PROFILE.md`](./AAP-BROKER-PROFILE.md), the broker & resolution layer.
- [`examples/`](./examples/), worked examples: the resolution flow and a policy grammar clause
  ([`orders-db-exchange.md`](./examples/orders-db-exchange.md)), and the HTTP, A2A agent card and
  MCP manifest transport bindings ([`transport-bindings.md`](./examples/transport-bindings.md)).

## Use cases

The full text of each use case, with the sources to check it against, is in [`docs/use-cases.md`](./docs/use-cases.md).

### The key an agent should never hold

You paste an API key into an agent's environment. One hidden instruction can ask it to send the key somewhere, and whoever receives it has standing access to your customers' data for as long as the key lives.

AAP removes the key from the agent. The agent emits an abstract `grant://name` reference.

What you can do today: run the token conformance suite, then read the worked example [`examples/orders-db-exchange.md`](./examples/orders-db-exchange.md).

```bash noexec
git clone https://github.com/opena2a-standards/aap-conformance
cd aap-conformance
npm install
node verifiers/node/verify.mjs fixtures
```

Where it stops today: the Exchange broker is implemented as a library with an end-to-end conformance test. A `secretless broker` daemon that does not construct the grant resolver from operator configuration returns 404 on `POST /grant`, and whether a given release constructs it is recorded in the reference implementation's repository (see [Reference implementation](./docs/reference-implementation.md)).

### An agent checks out with your money

An agent authorized to buy holds a stored card. It can be argued into a second purchase, and a helper agent it delegates to inherits the whole card. Stored payment credentials give software standing authority, with an expiry measured in years and no per-operation scope.

Under AAP the agent holds a Capability Grant Token that names the trust class and scope a broker will honor; the broker denies anything outside a matching policy clause by default; and a Delegation Assertion must stay within its delegator's grant, so a delegated helper gets less, never more. A valid ATX is never permission on its own.

What you can do today: `fixtures/da-compact-scope-superset.json` in the conformance suite rejects a delegation wider than its delegator, `fixtures/cgt-compact-expired.json` rejects an expired grant, and the token bytes this specification publishes are in [`examples/tokens/`](./examples/tokens/). The suite's Node and Python verifiers at commit `99e213a` accept three of them: `ait-v1.jwt`, `bac-v1.jwt` and `bac-v1.session.jwt`.

Where it stops today: the same daemon limit applies, and the suite's verifiers at commit `99e213a` match `trust_class` against `^[a-z0-9_-]+:[a-z0-9_-]+$` alone. They reject the published CGT and DA tokens, which carry the domain-prefixed class AAP-SPEC Section 4.2 says a broker should mint ([the token list](./docs/use-cases.md#an-agent-checks-out-with-your-money)). The claim schemas in [`schemas/`](./schemas/) accept both forms.

## Documentation

- [`docs/use-cases.md`](./docs/use-cases.md): each use case in full, with the sources to check it against.
- [`docs/overview.md`](./docs/overview.md): the one principle, the decision and enforcement split,
  the three credential-provider modes, and the two documents that define AAP.
- [`docs/reference-implementation.md`](./docs/reference-implementation.md): the Exchange broker in
  the [Secretless](https://github.com/opena2a-org/secretless-ai) broker library, its limits, and
  its developer surface.
- [`docs/status.md`](./docs/status.md): the last released versions and the current Internet-Draft
  revision.
- [draft-fane-opena2a-aap](https://datatracker.ietf.org/doc/draft-fane-opena2a-aap/): the
  Internet-Draft on the datatracker.
- [aap-conformance](https://github.com/opena2a-standards/aap-conformance): byte-pinned token
  fixtures with Node and Python verifiers.
- [`CHANGELOG.md`](./CHANGELOG.md): what changed between drafts, which draft revision pairs with
  which version, and the changes on main since the last release.
- [`CONTRIBUTING.md`](./CONTRIBUTING.md): co-authoring, review, and an independent second
  implementation.

## License

Apache-2.0. See [`LICENSE`](./LICENSE).
