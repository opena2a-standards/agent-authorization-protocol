# Changelog

All notable changes to the Agent Authorization Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

## [0.5.0-draft] - 2026-09-08

Internet-Draft pairing: `draft-fane-opena2a-aap-00` carried the 0.3.0-draft text
(2026-07-06, refreshed to the 0.4.0 content in #9), `draft-fane-opena2a-aap-01`
carries 0.4.0-draft (2026-07-22), and `draft-fane-opena2a-aap-02` carries this
0.5.0-draft. The broker profile moves to 0.4.0-draft in lockstep.
`draft-fane-opena2a-aap-02` is not submitted to the datatracker by this release;
`-01` remains the current revision there.

### Added

- **`authorization_details` (§4.4).** The RFC 9396 claim, in CGTs and DAs:
  an array of typed entries (`type` REQUIRED), mandatory to understand,
  narrowing within `scope` and `trust_class` and never widening them. Initial
  entry type registry (§4.4.1): `mcp_tool`, `skill`, `peer_agent`, `model`,
  `network`, `data`, `budget`, with the wire value of `type` the registry URI
  `https://specs.opena2a.org/aap/types/<name>`; every type that can carry data
  out carries an `egressCeiling` whose default is the empty set; every type MAY
  carry `requiresApproval`. Producer rule: never emit
  toward a verifier that has not advertised support.
- **Label semantics (§4.4.2)**, normative here: label, label set, ceiling,
  session (the agent's context at this broker, keyed by `sub` in ASC, reset only
  by a recorded context reset), session label, egress ceiling, residency as a
  label family. Sets, not levels, with the reason.
- **`aap_crit` (§4.5).** The claims a verifier must understand or reject;
  `authorization_details` and `cnf` always listed when present.
- **`cnf` (§4.6).** RFC 7800 proof of possession (`jwk` or RFC 7638 `jkt`),
  binding a CGT or DA to the presenter's key; REQUIRED when the token is
  presented to anyone but the minting broker.
- **Attenuation (§5.4).** A "narrower than or equal to" relation per entry
  type and member kind; a DA is valid only if every entry has a parent of the
  same type it is narrower than or equal to, and no entry is an orphan.
- **`session_label` in the L3 BAC (§6.4)**; the sixty second window is
  unchanged.
- **Grant revocation list (§7.3).** Local to the operator, keyed by `jti` and
  `sub`, cascading through DA chains by the delegator's `jti`, checked at
  every resolution.
- Security considerations §8.6 (presentation is not possession) and §8.7 (a
  constraint a verifier may ignore is not a constraint).
- Generated fixtures `cgt-v1.fgc.jwt`, `da-v1.fgc.jwt`, `bac-v1.session.jwt`
  (embedded in §4.7, §5.5, §6.5) and the presenter test keys `agent-key-1`
  (CGT subject) and `agent-key-2` (delegatee), appended to `test-keys.json`
  with `role` `presenter` and their RFC 7638 thumbprints. Every 0.4 fixture is
  byte identical and the 0.4 entries of `test-keys.json` are unchanged.
- Schemas: `cgt-claims-v1` and `da-claims-v1` gain `authorization_details`,
  `aap_crit`, `cnf`; `bac-claims-v1` gains `session_label` (L3 only). The
  claim schema stays at v1 because every new member is optional and a token
  that omits them is byte identical to its 0.4 form. `da-claims-v1` lowers
  `max_depth` to a minimum of 0 so a terminal delegation is expressible.
- RFC 9396, RFC 7800, RFC 7638, RFC 9449 added to Normative References;
  RFC 9421 to Informative References.

### Deprecated

- **`fga_constraints` (§4.2)**, replacedBy `authorization_details`. This is the
  first use of the AAP deprecation convention: a claims table row marked
  "deprecated" with a `replacedBy` target, `deprecated: true` plus a
  description in the schema, and a CHANGELOG entry under "Deprecated". The
  claim is not deleted: it is published in the -00 and -01 Internet-Draft text
  and both reference verifiers accept it; no implementation minted it as of
  2026-09-08. A verifier still ignores it (broker profile §8.3).
- **`max_uses` (§4.2)**, replacedBy `budget.maxUses` under the same convention.
  When both are present `budget.maxUses` MUST NOT exceed `max_uses`.

### Changed

- §7.2 no longer says the broker profile binds revocation "entirely" to the
  ATX CRL; agent revocation rides on the CRL, grant revocation on §7.3.
- §9.6 claim conventions: registered claims keep their registered spelling;
  members inside an `authorization_details` entry are camelCase.
- §5.3 `max_depth` floor lowered from 1 to 0; §5.4 binds a DA's `max_depth` to
  the delegator's matching `peer_agent` `subDelegationDepth`.
- §10 anticipates an entry type registry.
- **Broker profile 0.4.0-draft.** Resolution flow (§6) gains a presentation
  binding step (step 3: OS peer credentials on the local socket, RFC 9421
  message signature on HTTP, signed challenge on A2A and MCP; verification key
  is the ATX subject key where one exists, otherwise the AIP registered key)
  and a grant revocation list check (step 5). New normative subsections: §6.8
  presentation binding, §6.9 grant revocation list, §6.10 the three data
  clearance rules (no read above ceiling with projection and masking in the
  broker; session high water mark written to ASC and exposed in the BAC; no
  write down with a per entry egress ceiling, deny by default, an optional
  escalation hook that assumes no approval mechanism exists), §6.11 unlabeled
  field policy as a deployment setting (default: allow with no manifest, deny
  with a manifest), §6.12 CRL freshness by tier (fail closed for PRIVILEGED
  and SUPER_PRIVILEGED; the stale allowance value is cited from the ATX text,
  not restated). The session high water mark is keyed by `sub` in ASC and
  carries across grants; a CGT lifetime is the minimum session, not its bound.
  §7.3 governance policies compile to
  `authorization_details`; the grant, not the policy, is what the broker
  enforces. §9 jurisdiction slot retained, the ATX side out of scope, the
  enforcement side the residency label family. §13 Level 1 names the new
  requirements. §14 states what the reference does not yet provide as of
  2026-09-08. §17 related work (DAAP -02: budgets and policy languages outside
  its core, the `budget` type and the escalation hook here; no claim about
  sensitivity clearance in other drafts).

## [0.4.0-draft] - 2026-07-16

### Changed

- **ML-DSA-65: Reserved → Active (§8.2, §9.5).** RFC 9964 ("ML-DSA for JOSE and
  COSE", Standards Track, May 2026) registered the `ML-DSA-65` JOSE `alg` and the
  `AKP` key type — the exact adoption condition §9.5 named. The suite registry now
  carries two active entries; ML-DSA-65 keys publish as RFC 9964 `AKP` JWKs
  (seed-form `priv`); signing is pure ML-DSA with empty context, no pre-hash.
  Serialization-profile decision (three lanes: hybrid General JSON AAP-native,
  compact `EdDSA` foreign-interop baseline, compact `ML-DSA-65` PQ-interop) with
  rationale and the one escalated knob recorded in
  `decisions/2026-07-16-mldsa65-serialization-profile.md`.
- **Hybrid family gate (§9.4).** A general-form token declaring any `ML-DSA-65`
  entry is on the hybrid profile and MUST carry ≥1 `EdDSA` and ≥1 `ML-DSA-65`
  entry, every declared entry verifying (conformance category
  `HYBRID_INCOMPLETE`). The §9.4 example is now a real generated hybrid token;
  the 2× Ed25519 co-signature example remains published as
  `examples/tokens/cgt-v1.general.json`.
- **Downgrade rules tightened (§8.2).** Suite acceptance is pinned by verifier
  policy per path, never token-selected; hybrid-configured producers MUST NOT
  fall back to classical-only except via broker-profile §8.1 negotiation.
- **Replay prevention sharpened (§8.1).** Receivers MUST reject a repeated `jti`
  (conformance category `REPLAYED_JTI`); tracked from first acceptance to `exp`.

### Added

- Generated PQ fixtures: `cgt-v1.mldsa65.jwt` (+ claims), embedded in §9.3;
  `cgt-v1.hybrid.general.json`, embedded in §9.4; ML-DSA-65 test key
  `broker-pqc-1` (published seed, `mlDsa65SeedHex` + AKP public JWK) in
  `test-keys.json`. ML-DSA-65 fixtures use FIPS 204 deterministic signing and are
  cross-verified by three independent implementations (dilithium-py,
  @noble/post-quantum, OpenSSL via Node ≥ 25). Generator dependency:
  `dilithium-py>=1.4`.
- RFC 9964 added to Normative References.

## [0.3.0-draft] - 2026-07-05

### Added

- **AAP-SPEC §9 "Token Serialization and Signing" (normative):** the token
  canonical form, ratified byte-for-byte from the Secretless reference broker
  (`src/broker/cpi/assertion.ts`). AAP tokens are JWTs over JWS; the signed
  bytes are the JWS Signing Input — serialization is canonicalization, no JCS
  step and no delimiter grammar (deliberate difference from ATX §1.3a.2 and
  ATP §4.3, because AAP tokens are verified by foreign RFC 8693/OIDC systems).
  Compact serialization is mandatory on interop paths; JWS General JSON
  Serialization (§9.4) is the multi-suite vehicle realizing §8.2's
  per-signature model (isomorphic to the family `{keyId, algorithm, value}`
  form). Suite registry (§9.5): `EdDSA` active, `ML-DSA-65` reserved pending
  IETF JOSE registration. Claim conventions (§9.6): JWT snake_case names
  (documented exception to the org camelCase rule), NumericDate `iat`/`exp`,
  `aap_ver` claim OPTIONAL in v1 / REQUIRED at federation Level 3.
- **Normative claims tables with generated example bytes** for all four
  tokens: AIT (§3.2), CGT (§4.2, exactly the reference broker assertion's
  claim set), DA (§5.3: CGT + RFC 8693 `act` chain, `max_depth`,
  `delegator_atx`), BAC (§6.4: cumulative L1–L3 members, 60-second TTL).
  Implementation honesty labels state which structures the reference mints
  (CGT) and which are specified-but-not-yet-implemented (AIT, standalone DA,
  BAC).
- **Six new schemas** pinning every token structure: `jose-header-v1`,
  `ait-claims-v1`, `cgt-claims-v1`, `da-claims-v1`, `bac-claims-v1`,
  `jws-general-v1` (all self-contained; no cross-file `$ref`).
- **Deterministic fixture generator** `scripts/generate_examples.py`
  (published test-key seeds, fixed timestamps/`jti`; self-verifies every
  signature before writing) and `examples/tokens/` fixtures. Byte-for-byte
  equivalence with the reference TS construction was verified at authoring
  time. CI gains a drift gate: regenerate + byte-compare + require every
  compact token to appear verbatim in AAP-SPEC.md.
- `schemas/examples-map.json` entries validating the five decoded claim-set
  examples in AAP-SPEC.md against their schemas in CI.
- Adversarial-review hardening (pre-merge): §9.2 scopes `typ` to the compact
  form (the general form's per-signature headers carry exactly `alg` + `kid` —
  the spec's own §9.4 example was rejected by §9.2 as first written); v1
  headers are closed (unknown parameters, including `crit`, MUST be rejected;
  `jose-header-v1` gains `additionalProperties: false`); the drift gate also
  compares every embedded decoded claim-set block (values and member order)
  and every protected header shape; four safe-ignore citations corrected to
  broker profile §8.3 (AAP-SPEC §8.3 is Intent Verification); TTL tiers
  clarified as ceilings; the §9.4 example labeled non-conformant-as-hybrid;
  README decidability claim qualified (TTL window, BAC 60-second rule, DA
  scope subsetting are verifier rules, not schema checks). Companion reference
  fix: the broker now throws when minting without a trust class instead of
  falling back to the scope (secretless-ai#92).

### Changed

- **§8.2 rewritten for honesty and agility** (was "Post-Quantum Readiness"):
  the previous text claimed all signatures use hybrid Ed25519 + ML-DSA-65,
  which no implementation does. It now defines the suite field as the JOSE
  `alg`, names Ed25519 as the v1 baseline the reference actually signs, and
  keeps hybrid as the stated post-quantum target via the §9.4 multi-signature
  form.
- §3.2/§4.2 placeholder JSON (type annotations, scalar `signature` member,
  "ISO 8601" timestamps) replaced by the ratified claim sets; timestamps are
  NumericDate. The former §4.2 FGA members survive as optional-to-ignore
  claims (`fga_constraints`, `intent_verified`, `max_uses`,
  `context_required`).
- §8.1 pins the `jti` form (16 random bytes, lowercase hex).
- IANA and References renumbered §9/§10 → §10/§11 (no external documents
  cited the old numbers; verified across the org).
- Broker profile §8.1 gains the token-version rule (`aap_ver`); §11 names the
  broker assertion as the CGT/DA in the AAP-SPEC §9 token form. Broker
  profile version bumped in lockstep.
- `schemas/README.md` blocker list replaced by a "pinned by" table mapping
  each former blocker to the clause that resolved it; the `aap-conformance`
  prerequisite list is now satisfied.

### Carried from the pre-0.3 unreleased window (#3, #4)

- `schemas/grant-reference-v1.schema.json`: machine-readable schema for the
  broker-profile §4.2 grant reference (#4).
- `schemas/README.md` (first version): inventory of the four spec decisions
  that blocked the remaining schemas — resolved by this release (#4).
- CI workflow metaschema-checking the schemas
  (`scripts/validate_examples.py`) (#4).
- Authorship normalized to the spec-family convention (`OpenA2A`); named
  individual authors will be attributed at IETF Internet-Draft submission
  (#3).
- This changelog (#3).

## [0.2.0-draft] - 2026-06-01 (+ errata through 2026-07-02)

### Added

- Secretless named as the AAP broker reference implementation; AIM's AAP role
  scoped to `@agent.perform_action` + the five-step FGA flow. (#2, 2026-07-02)
- §6.1 exclude-and-redistribute erratum context: the composition rules AAP
  consumes from AIP §6.1 gained an anti-gaming ceiling upstream
  (agent-identity-protocol#9).
- OpenA2A specs family header.

### Changed

- Reconciled into one protocol: six-component token model (AAP-SPEC) plus
  broker/resolution profile (AAP-BROKER-PROFILE). Credential renamed
  ATC → ATX; DIDs moved from `did:atp:` to `did:opena2a:`. Supersedes the
  March 2026 `ietf-aap-internet-draft` draft.

## [0.1.0-draft] - 2026-06-01

### Added

- Initial specification: token model, scoped grants, default-deny broker
  policy, worked example, Apache-2.0 license.
