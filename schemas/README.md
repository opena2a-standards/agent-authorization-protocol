# AAP machine-readable schemas

This directory holds the JSON Schemas for AAP structures whose wire form the
specification actually pins. As of AAP-SPEC 0.2 that is a short list, and that
is deliberate: publishing a schema for a structure whose canonical form is
still unpinned would freeze illustration bytes as if they were normative.

## Published

| Schema | Source of truth | Status |
|---|---|---|
| `grant-reference-v1.schema.json` | AAP-BROKER-PROFILE.md §4.2 ABNF | Pinned, normative |

## Blocked, and what unblocks each

The remaining AAP token structures cannot be schema-tized (or fixture-tested —
this list is also the prerequisite list for an `aap-conformance` suite) until
the specification pins:

1. **A canonical signing serialization for AIT/CGT.** Unlike ATP §4.3
   (pipe-delimited seven-field string) or ATX §1.3a.2 (JCS over a projected
   TBS), AAP defines no byte-level canonical form for any token. Without one
   there is no deterministic signing, and therefore no byte-stable fixture.
2. **The signature representation.** AAP-SPEC §3.2/§4.2 show a scalar
   `signature` member; §8.2 says signatures follow the named, swappable
   per-signature suite model (the ATX/ATP `signatures[]` array of
   `{keyId, algorithm, value}`). One of the two must be chosen.
3. **Replay and versioning members.** §8.1 requires a unique token identifier
   (`jti`) and the broker profile §8.1 requires a version member on every
   message; neither appears in the §3.2/§4.2 structures.
4. **Field-level value formats.** The §3.2/§4.2 blocks carry type annotations
   ("uuid", "ISO 8601") rather than instances; the DA (§5) and BAC (§6)
   structures are prose-only with no field inventory at all.

Until then, the Secretless broker (the AAP reference implementation) plus its
in-repo end-to-end tests are the executable evidence for the broker profile.

Interim structural anchors that are already unambiguous if needed by tooling:
CPI modes (`Retrieve` / `Assume` / `Exchange`, §5), CGT TTL tiers
(`STANDARD` / `PRIVILEGED` / `SUPER_PRIVILEGED`, §4.3), broker conformance
levels 1-3 (broker profile §13), and the CGT `scope` member key set (§4.2).
