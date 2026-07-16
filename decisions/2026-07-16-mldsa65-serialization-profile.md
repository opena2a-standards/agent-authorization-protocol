# [CHIEF-CA + CHIEF-CSR] DECISION: ML-DSA-65 activation and hybrid serialization profile

**Date:** 2026-07-16
**Status:** Decided. The one escalated knob (see ESCALATION) proceeded on the chiefs'
recommendation — option (B), `EdDSA` default on foreign-interop paths through an
adoption window — with Abdel's go-ahead to continue (2026-07-16). Flipping to (A)
remains a one-sentence §9.3 change plus the broker's foreign-lane default; the
re-evaluation triggers in ESCALATION stand either way.
**Trigger:** RFC 9964 ("ML-DSA for JOSE and COSE", Standards Track, May 2026) registers
the JOSE `alg` values `ML-DSA-44` / `ML-DSA-65` / `ML-DSA-87` and the `AKP` JWK key type
(`pub`, plus `priv` pinned to the 32-byte seed). AAP-SPEC v0.3.0 §8.2/§9.5 gate ML-DSA-65
on exactly this registration ("Reserved. Adopted on IETF registration of ML-DSA for
JOSE"). The gate condition is satisfied; the row flips or the spec is stale.

## DECISION

1. **ML-DSA-65: Reserved → Active** in the §9.5 suite registry. RFC 9964 becomes a
   normative reference. The `alg` identifier is the registered string `ML-DSA-65`.
   Published PQ key material uses the RFC 9964 JWK form: `kty` `AKP`, `pub`
   (base64url, FIPS 204 §5.3), `priv` = 32-byte seed where a private JWK exists at
   all. `ctx` is always empty (RFC 9964 mandate); pure ML-DSA only, no HashML-DSA
   (RFC 9964 registers none).

2. **Path mapping (three lanes):**
   - **AAP-native lane** (broker↔broker, broker↔Registry, any path where both ends
     implement AAP): hybrid Ed25519 + ML-DSA-65 as JWS General JSON (§9.4) is the
     RECOMMENDED form. Two `signatures[]` entries, one per suite, same payload.
   - **Foreign-interop lane** (RFC 8693 `subject_token`, OIDC-style verifiers):
     compact, unchanged (§9.3; structurally forced — compact carries exactly one
     signature). The suite on this lane is verifier-capability-driven; the
     RECOMMENDED default is the escalated knob below.
   - **PQ-interop lane:** compact ML-DSA-65, minted when the counterparty
     advertises RFC 9964 support. Legal as of this decision.

3. **Hybrid verification policy (fail closed),** reconciling §8.2 with §9.4 and
   matching the production ATX verifier (`opena2a-registry/pkg/atcverify`) family
   gate:
   - Every declared `signatures[]` entry MUST verify (§9.4, already normative).
   - Family gate: a general-form token that declares any `ML-DSA-65` entry is on
     the hybrid profile and MUST carry ≥1 Ed25519 entry AND ≥1 ML-DSA-65 entry,
     all verifying. A missing family rejects with the new conformance category
     `HYBRID_INCOMPLETE`; it never silently degrades to single-suite acceptance.
   - General-form tokens with multiple entries of one suite (e.g. 2× Ed25519
     co-signature) remain legal; they are multi-signature, not hybrid.

4. **Downgrade rules** (existing §8.2 "MUST reject rather than silently downgrade"
   and §9.4 "MUST NOT accept on a subset" stand; two additions):
   - Suite acceptance is verifier-policy-pinned per path, never token-selected.
     (Lesson from AIM's `X-Algorithm` header gap, where a hybrid-capable agent can
     still authenticate classical-only because the client picks the algorithm.)
   - A producer configured for hybrid on a path MUST NOT emit classical-compact on
     that path; fallback is a broker-profile §8.1 version-negotiation event, never
     a per-token choice.

5. **Signing details:** deterministic ML-DSA-65 signing is REQUIRED for fixtures
   (byte-exact CI); hedged signing is permitted in production (verification is
   identical either way). Both suites sign the identical JWS Signing Input bytes;
   no per-suite domain separation (matches ATX; the registry package-signer's
   split-domain construction is explicitly NOT copied).

6. **Implementation stack:** `@noble/post-quantum` ^0.6.1 for the reference broker
   (Secretless; engines bump to Node >=20.19.0 — Node 18 and 20 are both EOL) and
   for the Node conformance verifier (its single third-party dependency, documented
   as such); `dilithium-py` ^1.4.0 (pure-Python FIPS 204) for the spec example
   generator and the Python conformance verifier. Fixture bytes are cross-checked
   by three independent ML-DSA implementations: dilithium-py (mint + self-verify),
   noble (Node verifier), and OpenSSL via Node ≥25 native `crypto.verify` (local
   cross-check). Ed25519 paths are unchanged (node:crypto / pyca cryptography).

## RATIONALE

- RFC 7515 compact serialization carries exactly one signature; a two-signature
  hybrid structurally requires the General JSON form. §9.3's foreign-lane compact
  mandate is already ratified (PR #5) because foreign verifiers understand exactly
  one thing, a standard JWT. The three-lane split is therefore not a new design; it
  is the ratified design with the PQ rows activated.
- Family precedent: the ATX per-signature `{keyId, algorithm, value}` model is
  isomorphic to JWS General `signatures[]` entries (§9.4 says so explicitly), and
  ATX PR #215 already migrated away from a combined classical+PQ blob. atcverify's
  gated-AND policy is running in production.
- CSR threat model: AAP tokens are short-TTL (60 s BAC to 3600 s AIT). Signatures
  have no harvest-now-decrypt-later exposure; the quantum risk is future forgery of
  then-live tokens. Hybrid AND-verification buys downgrade resistance and
  continuity of trust if either algorithm falls (FIPS 204 is two years old;
  Ed25519 has two decades of cryptanalysis but no PQ resistance) — either break
  alone forges nothing on hybrid paths.
- RFC 9964 registers no composite algorithms, so JWS-layer hybrid is the only
  standards-conformant vehicle today.

## ALTERNATIVES REJECTED

- **Composite single-`alg` blob** (`Ed25519+ML-DSA-65` concatenated signature):
  no IANA JOSE registration exists; contradicts the family's per-signature suite
  model; ATX already migrated away from exactly this; the in-house split-domain
  concatenation (registry package-signer) is the cautionary example.
- **Hybrid-everywhere** (General JSON on the RFC 8693 lane): foreign STSes cannot
  parse General JSON as a `subject_token`; violates ratified §9.3.
- **ML-DSA-65-only, drop Ed25519** (PQ-only default): loses the classical safety
  net against implementation-maturity flaws in two-year-old FIPS 204 code and
  contradicts §8.2's hybrid design.
- **OR / accept-on-subset verification:** a downgrade vector; violates §9.4;
  precisely the failure mode the `cgt-general-one-bad-signature` fixture pins.
- **Waiting for a composite-signature JOSE RFC:** unbounded delay for no security
  gain; the General JSON profile is standard JWS today and degrades gracefully if
  a composite registration later appears (a new registry row, per §9.5).

## ESCALATION (the one contested knob — ratification requested from Abdel)

**Does the RECOMMENDED default suite on the foreign-interop compact lane flip to
ML-DSA-65 now, or stay EdDSA through an adoption window?**

- **(A) Flip now:** strongest possible PQ-first posture; today there are ~zero
  deployed foreign consumers of AAP subject_tokens, so "breaking interop" is
  hypothetical and the default is pure spec signaling.
- **(B) EdDSA default + adoption window (chiefs' recommendation):** the lane exists
  *because* foreign verifiers only understand standard JWTs, and in mid-2026 the
  deployed JWT ecosystem (Keycloak, Auth0, Okta, stock jose libraries) verifies
  EdDSA, not a two-month-old RFC. A lane whose default the lane's own targets
  cannot verify contradicts its stated purpose. Short-TTL tokens carry no
  retroactive quantum risk, so the default costs nothing in security; hybrid
  remains the AAP-native recommendation, and ML-DSA-65 compact is Active and
  mintable on negotiation from day one — the "credibly first" claim rests on
  shipped hybrid + PQ code and byte-exact fixtures, not on a default flag.
  Re-evaluation triggers (whichever first): RFC 9964 verification ships in ≥2
  mainstream STS/JOSE stacks used by AAP integrations, or the v2 negotiation
  round, or 2027-06.

Everything else in this decision is invariant to this knob; the knob's blast
radius is one RECOMMENDED sentence in §9.3/§9.5 and the reference broker's
foreign-lane default (a one-line change either way).

## Consequences

- AAP-SPEC.md §8.2 and §9.5 rewritten (ML-DSA-65 Active, RFC 9964 normative);
  §9.4's example becomes a real generated hybrid token.
- `schemas/jose-header-v1.schema.json` `alg` enum gains `ML-DSA-65`;
  `jws-general-v1` description updated; conformance suite gains hybrid ACCEPT +
  hybrid-negative fixtures and the `HYBRID_INCOMPLETE` and `REPLAYED_JTI`
  categories (the latter implements §8.1's jti-replay MUST, previously
  unimplemented).
- draft-fane-opena2a-aap resubmits as -01 only after all of the above lands
  (Abdel's gate, 2026-07-16).
