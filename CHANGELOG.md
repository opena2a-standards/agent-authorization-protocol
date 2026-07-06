# Changelog

All notable changes to the Agent Authorization Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

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
