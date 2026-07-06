# AAP machine-readable schemas

This directory holds the JSON Schemas for AAP structures whose wire form the
specification pins. As of AAP-SPEC 0.3 the token canonical form is pinned
(AAP-SPEC §9, ratified byte-for-byte from the Secretless reference broker), so
every AAP token structure is schema-tized. Spec examples are validated against
these schemas in CI (`scripts/validate_examples.py` via
`schemas/examples-map.json`), and the token fixtures are generated — never
hand-authored — by `scripts/generate_examples.py`, with a CI drift gate.

## Published

| Schema | Source of truth | Status |
|---|---|---|
| `grant-reference-v1.schema.json` | AAP-BROKER-PROFILE.md §4.2 ABNF | Pinned, normative |
| `jose-header-v1.schema.json` | AAP-SPEC §9.2 | Pinned, normative |
| `ait-claims-v1.schema.json` | AAP-SPEC §3.2 | Pinned, normative (no reference implementation yet) |
| `cgt-claims-v1.schema.json` | AAP-SPEC §4.2 (ratified from Secretless `src/broker/cpi/assertion.ts`) | Pinned, normative, reference-implemented |
| `da-claims-v1.schema.json` | AAP-SPEC §5.3 | Pinned, normative (reference realizes delegation via Exchange; no standalone `act`-chain minting yet) |
| `bac-claims-v1.schema.json` | AAP-SPEC §6.4 | Pinned, normative (no reference implementation yet) |
| `jws-general-v1.schema.json` | AAP-SPEC §9.4 | Pinned, normative (multi-suite container; v1 tokens are compact) |

## The former blockers, and what pinned each

The 0.2 revision of this README listed four spec decisions that blocked these
schemas (and an `aap-conformance` suite). All four are resolved by AAP-SPEC 0.3:

| # | Blocker (0.2) | Pinned by (0.3) |
|---|---|---|
| 1 | No canonical signing serialization for AIT/CGT | AAP-SPEC §9.1: JWS Signing Input — serialization **is** canonicalization; compact JWT baseline ratified byte-for-byte from the reference broker assertion. |
| 2 | Scalar `signature` member (§3.2/§4.2) vs §8.2 `signatures[]` suite model | Neither: the signature is the JWS segment. Single-suite tokens are compact (§9.3); the multi-suite model is JWS General JSON Serialization (§9.4), isomorphic to the family `{keyId, algorithm, value}` form. |
| 3 | Missing `jti` / version members | `jti` REQUIRED in every claim set (§8.1: 16 random bytes hex); `aap_ver` defined in §9.6 (OPTIONAL in v1, REQUIRED at federation Level 3); message-level version negotiation unchanged (broker profile §8.1). |
| 4 | Type-annotation placeholders in §3.2/§4.2; DA/BAC prose-only | §3.2/§4.2 rewritten as normative claims tables with generated example bytes; DA claim set pinned in §5.3; BAC claim set pinned in §6.4. |

With the token form pinned, the prerequisite list for an `aap-conformance`
fixture suite is satisfied: fixtures are byte-stable (deterministic generator,
published test keys), and ACCEPT/REJECT verdicts are decidable against these
schemas plus the signature rules of AAP-SPEC §9 and the claim-semantics rules
of §4–§6 (TTL tiers, the BAC 60-second window, DA scope subsetting — prose
rules a suite encodes as verifier checks, not schema checks; the schema
descriptions state which is which).

Interim structural anchors (unchanged): CPI modes (`Retrieve` / `Assume` /
`Exchange`, §5), CGT TTL tiers (`STANDARD` / `PRIVILEGED` / `SUPER_PRIVILEGED`,
§4.3), and broker conformance levels 1-3 (broker profile §13).
