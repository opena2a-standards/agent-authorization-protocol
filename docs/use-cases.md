# Use cases

Each use case states the problem, how AAP addresses it, what you can check today and where it
stops today. The [README](../README.md) repeats what the second says about the published tokens.

## The key an agent should never hold

You paste an API key into an agent's environment. The agent reads web pages, documents and tool results, and it cannot reliably tell your instructions from text hidden in what it reads. One hidden instruction can ask it to send the key somewhere, and whoever receives it has standing access to your customers' data for as long as the key lives.

AAP removes the key from the agent. The agent emits an abstract `grant://name` reference. A local broker verifies the agent's ATX, evaluates the resource policy, obtains a scoped credential through one of three provider modes, performs the operation and returns the result. No secret, temporary credential, backend address or vendor name reaches the agent or the model behind it.

What you can do today: run the token conformance suite, then read the worked example [`examples/orders-db-exchange.md`](../examples/orders-db-exchange.md).

```bash
git clone https://github.com/opena2a-standards/aap-conformance
cd aap-conformance
npm install
node verifiers/node/verify.mjs fixtures
# summary: 44 pass, 0 fail (44 fixtures)
```

Where it stops today: the Exchange broker is implemented as a library with an end-to-end conformance test. A `secretless broker` daemon that does not construct the grant resolver from operator configuration returns 404 on `POST /grant`, and whether a given release constructs it is recorded in the reference implementation's repository (see [Reference implementation](./reference-implementation.md)).

## An agent checks out with your money

An agent authorized to buy holds a stored card. It can be argued into a second purchase, and a helper agent it delegates to inherits the whole card. Stored payment credentials give software standing authority, with an expiry measured in years and no per-operation scope.

Under AAP the agent holds a Capability Grant Token that names the trust class and scope a broker will honor; the broker denies anything outside a matching policy clause by default; and a Delegation Assertion must stay within its delegator's grant, so a delegated helper gets less, never more. A valid ATX is never permission on its own.

What you can do today: `fixtures/da-compact-scope-superset.json` in the conformance suite rejects a delegation wider than its delegator, `fixtures/cgt-compact-expired.json` rejects an expired grant, and the token bytes this specification publishes are in [`examples/tokens/`](../examples/tokens/). The suite's Node and Python verifiers at commit `99e213a` accept three of them: `ait-v1.jwt`, `bac-v1.jwt` and `bac-v1.session.jwt`.

Where it stops today: the same daemon limit applies, and the suite's verifiers at commit `99e213a` match `trust_class` against `^[a-z0-9_-]+:[a-z0-9_-]+$` alone. They reject the seven CGT and DA tokens in [`examples/tokens/`](../examples/tokens/) (`cgt-v1.jwt`, `cgt-v1.fgc.jwt`, `cgt-v1.mldsa65.jwt`, `cgt-v1.general.json`, `cgt-v1.hybrid.general.json`, `da-v1.jwt` and `da-v1.fgc.jwt`), which carry the domain-prefixed `acme.com/orders:read` that AAP-SPEC Section 4.2 says a broker should mint; the suite's `conformance.json` records the pattern its verifiers match. The claim schemas in [`schemas/`](../schemas/) accept both forms. The tokens can be minted; whether a given release of the daemon resolves a `grant://` reference against them is recorded in the reference implementation's repository.

Why you can check this yourself: [`AAP-SPEC.md`](../AAP-SPEC.md) and [`AAP-BROKER-PROFILE.md`](../AAP-BROKER-PROFILE.md); the Internet-Draft [draft-fane-opena2a-aap](https://datatracker.ietf.org/doc/draft-fane-opena2a-aap/); [aap-conformance](https://github.com/opena2a-standards/aap-conformance), 44 byte-pinned fixtures with Node and Python verifiers; the published token bytes in [`examples/tokens/`](../examples/tokens/), of which those verifiers at commit `99e213a` accept the three named above; and the broker library in [Secretless](https://github.com/opena2a-org/secretless-ai) under `src/broker/`.
