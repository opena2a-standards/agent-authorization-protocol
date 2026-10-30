# Use cases

Each use case states the problem, how AAP addresses it, what you can check today and where it
stops today. The [README](../README.md) repeats what the second says about the published tokens.
The page opens with who reads the specification and where each reader's question is answered.

## Who reads this

Each row names a reader, the question that brings them here and the text that answers it. A
`AAP-SPEC.md:N` or `AAP-BROKER-PROFILE.md:N` reference is the line in that document at the commit
that added this table; the section link stays stable when lines move.

| Reader | The question they bring | Where it is answered |
|---|---|---|
| Security leader or CISO | What risk does AAP remove, what do I require of a team that deploys a broker, and what evidence does it leave? | [The key an agent should never hold](#the-key-an-agent-should-never-hold); [An auditor asks for the record of every access an agent was given or refused](#an-auditor-asks-for-the-record-of-every-access-an-agent-was-given-or-refused); the conformance levels of [broker profile Section 13](../AAP-BROKER-PROFILE.md#13-conformance-levels) (`AAP-BROKER-PROFILE.md:764`); the security considerations of [broker profile Section 12](../AAP-BROKER-PROFILE.md#12-security-considerations) (`AAP-BROKER-PROFILE.md:722`) |
| IAM professional or identity architect | How do AAP's tokens line up with the OAuth 2.0 and OpenID Connect tokens I run, and does AAP replace my authorization server? | [Your IAM team asks how AAP tokens line up with OAuth 2.0 and OpenID Connect](#your-iam-team-asks-how-aap-tokens-line-up-with-oauth-20-and-openid-connect); [AAP-SPEC Section 3.1](../AAP-SPEC.md#31-purpose) (`AAP-SPEC.md:109`); [AAP-SPEC Section 4.1](../AAP-SPEC.md#41-purpose) (`AAP-SPEC.md:175`); [AAP-SPEC Section 5.1](../AAP-SPEC.md#51-purpose) (`AAP-SPEC.md:423`); the Exchange mode of [broker profile Section 5.3](../AAP-BROKER-PROFILE.md#53-mode-exchange) (`AAP-BROKER-PROFILE.md:257`) |
| Platform or security engineer | How do I run the broker, and what does a refusal look like? | [The key an agent should never hold](#the-key-an-agent-should-never-hold); the resolution flow of [broker profile Section 6](../AAP-BROKER-PROFILE.md#6-resolution-flow) (`AAP-BROKER-PROFILE.md:281`); opaque denials, [broker profile Section 6.6](../AAP-BROKER-PROFILE.md#66-denials) (`AAP-BROKER-PROFILE.md:324`); revocation-list freshness, [broker profile Section 6.12](../AAP-BROKER-PROFILE.md#612-crl-freshness-by-tier) (`AAP-BROKER-PROFILE.md:434`); the limits recorded in [Reference implementation](reference-implementation.md) |
| Agent developer or implementer | What do I implement first, and how do I show it conforms? | the tokens of AAP-SPEC Sections 3, 4, 5 and 6, and the serialization of [AAP-SPEC Section 9](../AAP-SPEC.md#9-token-serialization-and-signing-normative) (`AAP-SPEC.md:799`); Level 1 of [broker profile Section 13](../AAP-BROKER-PROFILE.md#13-conformance-levels) (`AAP-BROKER-PROFILE.md:768`); the token conformance suite command under [The key an agent should never hold](#the-key-an-agent-should-never-hold) |
| GRC, audit or compliance reader | Which controls does it support, and what does an auditor read? | [An auditor asks for the record of every access an agent was given or refused](#an-auditor-asks-for-the-record-of-every-access-an-agent-was-given-or-refused); the signed audit log of [broker profile Section 6.7](../AAP-BROKER-PROFILE.md#67-audit) (`AAP-BROKER-PROFILE.md:333`); the AI Agent Threat Matrix technique IDs of [broker profile Section 12.1](../AAP-BROKER-PROFILE.md#121-threat-model-and-taxonomy-mapping) (`AAP-BROKER-PROFILE.md:724`) and [AAP-SPEC Section 8.5](../AAP-SPEC.md#85-credential-confinement) (`AAP-SPEC.md:771`); an OASB level as a grant condition, [broker profile Section 7.1](../AAP-BROKER-PROFILE.md#71-canonical-federation-clause) (`AAP-BROKER-PROFILE.md:506`) |
| Standards reviewer (IETF or AIW participant) | What problem does AAP solve, what do OAuth 2.0, SAML and OpenID Connect leave open, and how mature is it? | [AAP-SPEC Section 1](../AAP-SPEC.md#1-introduction) (`AAP-SPEC.md:63`); related work, [broker profile Section 17](../AAP-BROKER-PROFILE.md#17-related-work-informative) (`AAP-BROKER-PROFILE.md:853`); [AAP-SPEC Section 10](../AAP-SPEC.md#10-iana-considerations) (`AAP-SPEC.md:964`); the released versions and the Internet-Draft revision, [`docs/status.md`](status.md) |

### The readers

- **Security leader or CISO**
  - Who: accountable for the organization's security risk, and for which agents and vendors may act on its systems.
  - Why they open it: a team proposes to give agents access to production data or payments, and the question is what an agent could leak or misuse.
  - What they decide: whether agents may hold credentials at all, which broker conformance level to require, and which audit evidence to demand.
  - How they verify: the Level 1 requirements of broker profile Section 13, the audit rules of broker profile Section 6.7, and the token conformance suite.
- **IAM professional or identity architect**
  - Who: runs the identity systems the organization already has, such as OAuth 2.0 and OpenID Connect, X.509 certificates, workload identity such as SPIFFE, DIDs and privileged access management.
  - Why they open it: they run the authorization servers and token services that AAP's tokens are meant to work with.
  - What they decide: where the broker sits relative to the authorization server, which token form a foreign verifier receives, and how tokens are bound to keys.
  - How they verify: the mappings of AAP-SPEC Sections 3.1, 4.1, 4.4, 4.6 and 5.1, and the key-binding and delegation fixtures shown below.
- **Platform or security engineer**
  - Who: deploys, operates and monitors the components that check agents at runtime, and is paged when they fail.
  - Why they open it: they deploy the broker that resolves grant references and need to know what fails and how it shows.
  - What they decide: which credential-provider mode to run, revocation-list freshness for each tier, and how operators read denials.
  - How they verify: the token conformance suite, and the limits recorded in [Reference implementation](reference-implementation.md).
- **Agent developer or implementer**
  - Who: writes the broker, the token issuer, the verifier or the agent that emits grant references.
  - Why they open it: they have to mint or verify tokens that other implementations accept.
  - What they decide: which tokens and which serialization to support first, the compact form being the interoperability baseline, and which broker conformance level to target.
  - How they verify: the fixtures of [aap-conformance](https://github.com/opena2a-standards/aap-conformance) through their verifier, compared with the pinned verdicts.
- **GRC, audit or compliance reader**
  - Who: maps controls to evidence and reads the records an auditor asks for.
  - Why they open it: an auditor asks for the record of every access an agent was given or refused, and which threats the deployment controls.
  - What they decide: whether the signed audit log is evidence they accept, and which technique IDs map to their controls.
  - How they verify: broker profile Section 6.7 for what each record must and must not contain, and broker profile Section 12.1 for the technique IDs.
- **Standards reviewer (IETF or AIW participant)**
  - Who: a participant in an IETF or AIW discussion who judges whether a problem needs new work.
  - Why they open it: to judge whether agent authorization needs a protocol beside OAuth 2.0, SAML and OpenID Connect, as AAP-SPEC Section 1 argues.
  - What they decide: whether to review, implement or co-author it, and what to ask the editors to change.
  - How they verify: the Internet-Draft on the datatracker, [`docs/status.md`](status.md) and the conformance suite.

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

Who acts: the security leader who decides that agents hold no credentials, and the platform
engineer who runs the broker.

Spec text: the core invariant of [broker profile Section 4.1](../AAP-BROKER-PROFILE.md#41-the-core-invariant)
(`AAP-BROKER-PROFILE.md:194`); credential confinement, [AAP-SPEC Section 8.5](../AAP-SPEC.md#85-credential-confinement)
(`AAP-SPEC.md:771`); and the three credential-provider modes of
[broker profile Section 5](../AAP-BROKER-PROFILE.md#5-the-credential-provider-interface-cpi)
(`AAP-BROKER-PROFILE.md:233`).

## An agent checks out with your money

An agent authorized to buy holds a stored card. It can be argued into a second purchase, and a helper agent it delegates to inherits the whole card. Stored payment credentials give software standing authority, with an expiry measured in years and no per-operation scope.

Under AAP the agent holds a Capability Grant Token that names the trust class and scope a broker will honor; the broker denies anything outside a matching policy clause by default; and a Delegation Assertion must stay within its delegator's grant, so a delegated helper gets less, never more. A valid ATX is never permission on its own.

What you can do today: `fixtures/da-compact-scope-superset.json` in the conformance suite rejects a delegation wider than its delegator, `fixtures/cgt-compact-expired.json` rejects an expired grant, and the token bytes this specification publishes are in [`examples/tokens/`](../examples/tokens/). The suite's Node and Python verifiers at commit `99e213a` accept three of them: `ait-v1.jwt`, `bac-v1.jwt` and `bac-v1.session.jwt`.

Where it stops today: the same daemon limit applies, and the suite's verifiers at commit `99e213a` match `trust_class` against `^[a-z0-9_-]+:[a-z0-9_-]+$` alone. They reject the seven CGT and DA tokens in [`examples/tokens/`](../examples/tokens/) (`cgt-v1.jwt`, `cgt-v1.fgc.jwt`, `cgt-v1.mldsa65.jwt`, `cgt-v1.general.json`, `cgt-v1.hybrid.general.json`, `da-v1.jwt` and `da-v1.fgc.jwt`), which carry the domain-prefixed `acme.com/orders:read` that AAP-SPEC Section 4.2 says a broker should mint; the suite's `conformance.json` records the pattern its verifiers match. The claim schemas in [`schemas/`](../schemas/) accept both forms. The tokens can be minted; whether a given release of the daemon resolves a `grant://` reference against them is recorded in the reference implementation's repository.

Who acts: the security leader who lets agents spend, and the broker that enforces the grant.

Spec text: the Capability Grant Token of [AAP-SPEC Section 4](../AAP-SPEC.md#4-capability-grant-token-cgt)
(`AAP-SPEC.md:172`); the attenuation of a Delegation Assertion,
[AAP-SPEC Section 5.4](../AAP-SPEC.md#54-attenuation) (`AAP-SPEC.md:484`); and default-deny,
[AAP-SPEC Section 8.4](../AAP-SPEC.md#84-trust-is-not-authorization) (`AAP-SPEC.md:766`).

## Your IAM team asks how AAP tokens line up with OAuth 2.0 and OpenID Connect

Your organization runs an OAuth 2.0 authorization server and OpenID Connect for its applications.
A team proposes AAP for agents. The identity team wants to know whether this is a second token
system to run beside the first, or tokens its existing servers can verify.

Who acts: the IAM professional or identity architect.

Without the specification: an agent receives an ordinary access token or API key with standing
scope, and when it hands work to another agent, the helper gets the same token or a new grant that
nobody can trace back to the agent that delegated it.

What the specification does: the Agent Identity Token, the Capability Grant Token and the
Delegation Assertion are each defined against an existing OAuth 2.0 or OpenID Connect artifact.
The Behavioral Attestation Claim has no such parallel
([AAP-SPEC Section 6.1](../AAP-SPEC.md#61-purpose), `AAP-SPEC.md:590`).

- The Agent Identity Token is a cryptographic assertion of agent identity, analogous to an OIDC
  ID Token ([AAP-SPEC Section 3.1](../AAP-SPEC.md#31-purpose), `AAP-SPEC.md:109`).
- The Capability Grant Token is a short-lived, scoped authorization token, analogous to an OAuth
  2.0 access token ([AAP-SPEC Section 4.1](../AAP-SPEC.md#41-purpose), `AAP-SPEC.md:175`). In a
  broker deployment it is the RFC 8693 `subject_token`, which the downstream authorization server
  verifies as a standard JWT against the broker's published keys (`AAP-SPEC.md:237`), and the
  compact form is REQUIRED wherever a foreign system verifies the token
  ([AAP-SPEC Section 9.3](../AAP-SPEC.md#93-compact-serialization), `AAP-SPEC.md:838`).
- Structured grants use the RFC 9396 `authorization_details` claim
  ([AAP-SPEC Section 4.4](../AAP-SPEC.md#44-authorization-details), `AAP-SPEC.md:249`), and the
  RFC 7800 `cnf` claim binds a token to the presenter's key
  ([AAP-SPEC Section 4.6](../AAP-SPEC.md#46-proof-of-possession), `AAP-SPEC.md:351`).
- The Delegation Assertion is analogous to OAuth 2.0 Token Exchange (RFC 8693), and the delegated
  scope cannot exceed the delegator's ([AAP-SPEC Section 5.1](../AAP-SPEC.md#51-purpose),
  `AAP-SPEC.md:423`). The broker's Exchange mode is a realization of it over RFC 8693
  ([broker profile Section 5.3](../AAP-BROKER-PROFILE.md#53-mode-exchange), `AAP-BROKER-PROFILE.md:257`).

How to see it work: the suite pins the key binding and the delegation rules. From `aap-conformance`
in the clone made under [The key an agent should never hold](#the-key-an-agent-should-never-hold):

```bash
node verifiers/node/verify.mjs fixtures/cgt-compact-cnf-no-proof.json fixtures/cgt-compact-cnf-mismatch.json fixtures/da-compact-scope-superset.json fixtures/da-compact-authorization-details-widened.json
```

Output at aap-conformance commit `a4ab3d9`, run on 2026-10-30:

```
PASS  fixtures/cgt-compact-cnf-mismatch.json  [cgt]
       expected: REJECT [CNF_MISMATCH]
       observed: REJECT[CNF_MISMATCH: presenter key thumbprint "qI__BOccgAhhH9wob_G7gFVHLKIkS4CutvoSx0bMCY8" does not match the cnf binding "HlHgCcjrhbeyw80VMef51yPwhyRqjiwLdwSLRqo7hSI" (AAP-SPEC §4.6)]
PASS  fixtures/cgt-compact-cnf-no-proof.json  [cgt]
       expected: REJECT [CNF_MISMATCH]
       observed: REJECT[CNF_MISMATCH: token carries cnf but no presenter proof was presented (AAP-SPEC §4.6)]
PASS  fixtures/da-compact-authorization-details-widened.json  [da]
       expected: REJECT [NOT_ATTENUATED]
       observed: REJECT[NOT_ATTENUATED: authorization_details[0] (type data) is not narrower than or equal to any delegator entry of the same type: fieldsAllowed is not a subset of the delegator's (AAP-SPEC §5.4)]
PASS  fixtures/da-compact-scope-superset.json  [da]
       expected: REJECT [SCOPE_NOT_SUBSET]
       observed: REJECT[SCOPE_NOT_SUBSET: DA scope "orders.read orders.write" is not a subset of the delegator scope "orders.read" (AAP-SPEC §5.2)]

summary: 4 pass, 0 fail (4 fixtures)
```

Out of scope: AAP does not replace the authorization server. In a broker deployment the broker
presents the grant to it as the RFC 8693 subject token, and the server mints the scoped downstream
token. The specification defines no mapping onto SAML, SPIFFE or an X.509 workload certificate.

## An auditor asks for the record of every access an agent was given or refused

After an incident, an auditor asks which agents reached the orders database last month, which
requests were refused and why, and whether any credential could have left the deployment. The
security leader has to show evidence, not a description.

Who acts: the auditor or GRC reader, and the security leader who required the broker.

Without the specification: agents reach services with keys they hold, so the record is whatever
each service happened to log, a log can hold the key itself, and each backend refuses in its own
way.

What the specification does: every verification, decision, resolution and denial MUST be written
to a signed audit log, and an audit record MUST NOT contain any credential value or downstream token
([broker profile Section 6.7](../AAP-BROKER-PROFILE.md#67-audit), `AAP-BROKER-PROFILE.md:333`).
The agent receives the same opaque denial whether the grant is unknown, the policy denies, the ATX
is untrusted or the provider fails, and the diagnostic detail goes to the
audit log ([broker profile Section 6.6](../AAP-BROKER-PROFILE.md#66-denials),
`AAP-BROKER-PROFILE.md:324`). Level 1 of the broker profile requires signed audit together with
default-deny, ATX verification and the revocation-list check before resolution, presentation
binding, ephemeral-worker confinement and opaque denials
([broker profile Section 13](../AAP-BROKER-PROFILE.md#13-conformance-levels),
`AAP-BROKER-PROFILE.md:768`). For control mapping, the broker profile names the AI Agent Threat
Matrix techniques the broker is a control against, T-3002, T-3003, T-3006 and T-8002
([broker profile Section 12.1](../AAP-BROKER-PROFILE.md#121-threat-model-and-taxonomy-mapping),
`AAP-BROKER-PROFILE.md:724`), and its policy grammar can make an OASB level a condition of a grant
([broker profile Section 7.1](../AAP-BROKER-PROFILE.md#71-canonical-federation-clause),
`AAP-BROKER-PROFILE.md:506`).

What to require, in the specification's terms: a broker that conforms to Level 1 of the broker
profile, with an audit log the auditor can read and whose signatures they can check.

How to see it work: not runnable here. aap-conformance pins token verdicts and has no fixture for an
audit record or a denial.

Out of scope: [broker profile Section 14](../AAP-BROKER-PROFILE.md#14-reference-implementation-informative)
(`AAP-BROKER-PROFILE.md:777`) lists the signature on audit records among what the reference
implementation's described library surface does not include; whether a given release provides it
is recorded in that implementation's repository. The specification maps the techniques above to no
control framework.

## Why you can check this yourself

Why you can check this yourself: [`AAP-SPEC.md`](../AAP-SPEC.md) and [`AAP-BROKER-PROFILE.md`](../AAP-BROKER-PROFILE.md); the Internet-Draft [draft-fane-opena2a-aap](https://datatracker.ietf.org/doc/draft-fane-opena2a-aap/); [aap-conformance](https://github.com/opena2a-standards/aap-conformance), 44 byte-pinned fixtures with Node and Python verifiers; the published token bytes in [`examples/tokens/`](../examples/tokens/), of which those verifiers at commit `99e213a` accept the three named above; and the broker library in [Secretless](https://github.com/opena2a-org/secretless-ai) under `src/broker/`.
