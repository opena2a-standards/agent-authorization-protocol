# Changelog

All notable changes to the Agent Authorization Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Changed

- `trust_class` (Section 4.2, and the DA through Section 5.3) uses the capability grammar of
  AIP Section 4.1: a reserved namespace, or a namespace prefixed with the defining
  organization's domain, then a colon and an action (`acme.com/orders:read`). The CGT and
  DA claim schemas accept that grammar and keep accepting the legacy `namespace:action`
  form (`^[a-z0-9_-]+:[a-z0-9_-]+$`), so no value valid before this change is rejected; a
  verifier treats the legacy form as well formed under claim schema version 1, and
  removing it requires a new claim schema version. A broker SHOULD mint the AIP grammar.
  Section 4.2 no longer carries the dated sentence on the pattern of the claim schemas and
  the reference verifiers. Every CGT and DA example in the specification, the broker
  profile, `examples/orders-db-exchange.md` and `examples/tokens/` carries
  `acme.com/orders:read`; the generated CGT and DA fixtures and their embedded bytes change
  accordingly (Section 9.7), and the AIT and BAC fixtures and `test-keys.json` are
  unchanged. AIP is a normative reference. One MUST and one SHOULD are added to
  AAP-SPEC.md; the broker profile's requirement counts are unchanged.
  `scripts/test_trust_class_grammar.py` pins the accepted and rejected values for both
  schemas and checks that the five CGT and DA claim sets in `examples/tokens/` and the
  `trust_class` values of the JSON examples in AAP-SPEC.md carry the domain-prefixed class.
- The specification and the broker profile no longer carry dated statements that no
  implementation provides a feature (eight sentences: AAP-SPEC Section 4.2 preamble and
  `authorization_details` row, Sections 4.6 and 7.3; broker profile Sections 6.8, 6.9, 7.3
  and 14). Each is replaced by an undated statement of what the text defines (the 0.5
  members are outside the ratified baseline) or by a non-normative "Implementation status"
  note naming where current status is recorded: broker profile Section 14, the reference
  implementation's repository, and the aap-conformance repository's `conformance.json`.
  No requirement changes: the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both
  documents are unchanged.
- In `README.md`, `AAP-SPEC.md` (the reference implementation paragraph),
  `AAP-BROKER-PROFILE.md` (Section 6.7), `examples/orders-db-exchange.md` and the ML-DSA-65
  decision note, the first use of the name reads "OpenA2A AIM (Agent Identity Management)",
  so the name is not read as another agent identity acronym. Editorial: no requirement
  changes, and the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both documents are
  unchanged. `scripts/check_naming.py` checks the first use in every Markdown file in the
  repository and in the XML source of each Internet-Draft, so a new document is covered
  without being listed, and runs in CI through `scripts/validate_examples.py`.
- `scripts/check_naming.py` skips fenced code blocks when it looks for the first use of the
  name, so a diagram label or sample output in a code block is not counted as the first
  use; the first use must be in prose. `scripts/validate_examples.py` also runs the unit
  tests in `scripts/` (`test_*.py`), so CI runs them, and fails if none are found.
- AAP-SPEC no longer dates implementation status or states it as an unscoped negative
  ("no implementation"): Section 3.2 (no reference implementation mints AITs yet), the
  `trust_class` row of Section 4.2 (what the aap-conformance verifiers match "as of the
  date of this revision"), the `fga_constraints` row (no implementation minted it) and
  Section 6.3 (no implementation mints BACs yet). Sections 3.2 and 6.3 carry a
  non-normative "Implementation status" note naming the issuing Registry implementation's
  repository as the record; the `trust_class` row states the pattern the claim schemas in
  this repository match and names the aap-conformance `conformance.json` as the record for
  the verifiers; the `fga_constraints` row reads "no known implementation", as the -02
  Internet-Draft text does. `scripts/check_status_claims.py` fails on `as of <YYYY-MM-DD>`,
  "as of the date of this revision", "no implementation" and "no reference implementation"
  in AAP-SPEC.md, AAP-BROKER-PROFILE.md and every Internet-Draft source after -02, and runs
  in CI through `scripts/validate_examples.py`. No requirement changes: the counts of
  MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both documents are unchanged.
- The References entries for ATP (in both documents), for AIP (in the broker profile) and
  for the broker profile (in the specification) name the text file whose section numbers
  the documents cite: `ATP-SPEC.md`, `AIP-SPEC.md` and `AAP-BROKER-PROFILE.md`, as the AIP
  entry of the specification already did. A family document can have more than one
  numbered text: the capability format is Section 4.1 of `AIP-SPEC.md` and Section 5.1 of
  draft-fane-opena2a-aip-04. In `examples/orders-db-exchange.md` the resolution flow was
  cited as "Section 6 of the spec"; it is Section 6 of the broker profile (Section 6 of
  the specification is the BAC), and the heading now says so. Editorial: no requirement
  changes, and the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both documents
  are unchanged.
- AAP-SPEC Sections 5.5, 8.2 and 9.3 and broker profile Section 14 no longer state
  implementation, deployment or registration status with "not yet" or "yet": whether the
  reference implementation mints standalone DAs, and whether its daemon serves
  `POST /grant`, is recorded in its own repository; the ML-KEM row stays reserved until a
  final JOSE registration, whose record is the IANA "JSON Web Signature and Encryption
  Algorithms" registry; and Section 9.3 states why `EdDSA` is the RECOMMENDED default on
  foreign-interop paths (a verifier that does not implement the RFC 9964 suites rejects an
  `ML-DSA-65` token). The reconciliation note no longer cites the superseded March 2026
  draft by a file path outside this repository. No requirement changes: the counts of
  MUST, MUST NOT, SHOULD, SHOULD NOT, MAY and RECOMMENDED in both documents are unchanged.
- `scripts/check_status_claims.py` also fails on "as of" followed by a month-name date
  ("October 2026", "6 October 2026", "October 6, 2026"), a year, or a moving anchor ("this
  writing", "this revision", "today", "now"); on "no" with one word before
  "implementation" ("no current implementation"), on "none of the implementations", and on
  either wording split by emphasis, a code span or an inline element such as `<em>`.
  "No known implementation" still passes, and a normative statement ("no conforming
  implementation accepts ...", also with "compliant" or "conformant") and "no
  implementation" used as a modifier ("no implementation requirement") now pass. A unit
  test covers every month name and its abbreviation. It covers the XML source of every
  Internet-Draft (`draft-*.xml`) except the filed `draft-fane-opena2a-aap-00` to `-02`,
  each failure line names the accepted wording, and its run time is linear in the number
  of matches.
- `scripts/check_status_claims.py` also checks `README.md`, whose use cases and Reference
  implementation section state what the reference implementation does, so a dated status
  ("as of" followed by a date) or an unscoped "no implementation" there fails CI as it does
  in the specification. Its run lists the README after the two specification documents,
  and a missing README fails as a missing specification document does. The README passes
  unchanged.
- `scripts/check_status_claims.py` also fails on a status stated with "yet": "not yet"
  ("does not yet construct"), "yet to", "as yet", and "yet" closing a negative in the same
  clause ("no reference implementation yet"). "yet" as a conjunction and a token's own
  validity window ("not yet valid", "not yet expired") pass. It also checks
  `schemas/README.md`, whose Status column states what the reference implementation mints,
  and a covered document that is not valid UTF-8 fails with a `FAIL` line naming the line of
  the first byte that does not decode, instead of a traceback. `README.md` and
  `schemas/README.md` no longer state status with "not yet" or "yet": whether a given
  release of the `secretless broker` daemon constructs the grant resolver, and whether the
  reference implementation mints standalone DAs, is recorded in the reference
  implementation's repository, as broker profile Section 14 and AAP-SPEC Section 5.5 state;
  the AIT and BAC rows name the implementation status notes of AAP-SPEC Sections 3.2 and
  6.3. `.gitignore` lists `secrets.json` with the other secret-file patterns, and
  `scripts/test_gitignore.py` checks the patterns with `git check-ignore`. Editorial: no
  requirement changes.
- A Markdown document that is not valid UTF-8 fails each check that reads it with a `FAIL`
  line naming the line of the first byte that does not decode, as
  `scripts/check_status_claims.py` already did, and `scripts/validate_examples.py` no
  longer stops with a `UnicodeDecodeError` traceback at the first such document.
  `check_naming.py`, `check_raw_html.py`, `check_spelling.py`,
  `check_section_citations.py`, `check_references.py`, `check_requirement_references.py`
  and `check_status_claims.py` read their documents through one function,
  `check_naming.read_text`, and the documents and checks that follow still run. A document
  that a mapped example is read from stops `validate_examples.py` on one `error:` line
  with the same reason.
- The broker profile lists AIP among its normative references, as AAP-SPEC.md does, and no
  longer among its informative ones. The MUST NOT of Section 6.8 (a broker that can obtain
  neither verification key does not accept a network presentation) depends on the key
  registered for the agent DID under AIP, and a reference that must be read to implement
  a requirement is normative. `scripts/check_requirement_references.py` reads references
  named by RFC number and does not see this one. No requirement changes: the counts of
  MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both documents are unchanged.
- The newest Internet-Draft render is read the same way: `scripts/check_references.py` and
  `scripts/check_section_citations.py` read it through `check_naming.read_text` and parse
  it in one function, `check_references.read_render`. A render that is not valid UTF-8 or
  not well-formed XML fails with a `FAIL` line naming the line where reading stops
  (`FAIL  reference classes: <render>: <reason>`, and `FAIL  <render>: <reason>` with the
  census line, whose Markdown documents are still checked), instead of stopping
  `scripts/validate_examples.py` with an `xml.etree` `ParseError` traceback; the checks
  that follow still run.
- `scripts/check_requirement_references.py` finds the HTML comments inside a paragraph in
  one forward pass, from each `<!--` to the first `-->` before the next blank line. The
  pattern it replaces read the paragraph again to its end from each `<!--` that has no
  `-->`, so a 64 KB paragraph of them took seconds and one twice that size four times as
  long. What is read as a comment or a code span is unchanged. Its test counts the
  characters the scan reads instead of timing it, so a loaded runner does not fail it,
  and a scan that reads the paragraph again from each `<!--` still does. Its bound is four
  times the length of the text, not three: a scan that resumes its search for `<!--` one
  character past the last one found reads each `<!--` twice and still reads the paragraph
  in one pass, and the test now runs that scan and one that searches for the blank line
  again from each `<!--`, which it fails. Those two scans are copies of `inline_spans()`,
  and a test now checks that both find the spans `inline_spans()` finds on every text of up
  to five pieces mixing backtick strings, `<!--`, `-->` and blank lines, and on five more
  texts: one that mixes them in prose; one of six pieces in which a backtick inside a
  comment opens a code span that begins inside the comment, so the first search for code
  spans does not return the code span that begins where the comment ends, and resuming
  that search later than the comment's end misses it (in the six texts of five pieces in
  which a code span begins where a comment ends, the first search already finds it); one
  in which a `-->` begins inside a later `<!--`, which those pieces cannot build; and the
  64 KB paragraph of unclosed `<!--`, alone and with a `-->` after a blank line, on which
  the tests count the characters read. A change to either copy, or to the loop of
  `inline_spans()` that merges code spans and comments, fails it when it changes the spans
  found on one of those texts. A copy that stops moving past the span it last found fails
  it instead of running without end, which a test now checks with a scan that never moves
  forward; that failure carries the first 80 characters of the text. The failure line
  names "in contrast with" among the contrast phrases that pass, as the check accepts it;
  it named five of the six.
- `scripts/check_raw_html.py` finds code spans in one forward pass: `code_spans()` reads
  each backtick string once and pairs it with the next string of the same length, and
  replaces the `CODE_SPAN` pattern that `prose()` and
  `scripts/check_requirement_references.py` used. The pattern read the paragraph again to
  its end from each backtick string that no later string of the same length closes, so a
  312 KB paragraph of them took about four seconds. What is read as a code span is
  unchanged. Its tests, one per check, count the characters the scan reads instead of
  timing it, so a loaded runner does not fail them, and a scan that reads the paragraph
  again from each backtick string still does. Each also reads a second paragraph whose
  backtick strings close the first one's, so the scan's searches for a blank line are
  counted too.
- `schemas/da-claims-v1.schema.json` describes `exp`: it MUST NOT be later than the
  delegator's `exp`, and in a chain the bound holds link by link (AAP-SPEC Section 5.3), a
  verifier check, as the descriptions of the scope subset rule and of `max_depth` name
  theirs. The schema accepts the same claim sets.
- `check_references.read_render` returns the parsed root of the newest Internet-Draft
  render with its text, and `render_references` in `scripts/check_references.py` and
  `scripts/check_section_citations.py` reads the references from that root. Each check
  parses the render once; it parsed it twice, once to prove it well-formed and once to
  read its references. The output of both checks is unchanged.
- `README.md` no longer calls the tokens in `examples/tokens/` "the valid token bytes". The
  aap-conformance Node and Python verifiers at commit `99e213a` match `trust_class` against
  `^[a-z0-9_-]+:[a-z0-9_-]+$` alone, so they accept `ait-v1.jwt`, `bac-v1.jwt` and
  `bac-v1.session.jwt` and reject the seven CGT and DA tokens, which carry the
  domain-prefixed `acme.com/orders:read`. The second use case names the tokens on each side,
  the pattern those verifiers match, and the suite's `conformance.json` as the record of
  that pattern. `scripts/test_readme_tokens.py` reads each token's payload and checks that
  the README names the tokens on each side. No requirement, schema or token changes.
- The reference implementation paragraph of `AAP-SPEC.md` no longer credits the reference
  implementation with the whole resolution flow of broker profile Section 6. It names the
  verification, policy, minting, exchange and worker steps, and cites the implementation
  status note of broker profile Section 14 for the parts outside the implemented surface:
  presentation binding (6.8), the grant revocation list (6.9), the data clearance rules
  (6.10), revocation after resolution (6.13) and the policy compile step (7.3).
  `scripts/test_reference_status.py` reads the sections that note names and checks that
  the paragraph cites each of them and the note. Editorial: no requirement changes.
- The policy binding for `grant://orders-db` in `examples/orders-db-exchange.md` and in
  broker profile Section 7.1 names the reference implementation's spelling of the two
  `resolve` keys its policy loader refuses as the grammar writes them: a comment on the
  `provider` line gives `providerId`, and a comment on the `ttl: 300s` line gives
  `ttlSeconds: 300`. A note under each binding lists the keys the loader accepts at commit
  `660af0d` (`mode`, `providerId`, `scope`, `audience`, `ttlSeconds`) and names
  `src/broker/grant-policy.ts` in the reference implementation's repository as the record
  for a given release. The keys of the grammar are unchanged.
  `scripts/test_resolve_key_spelling.py` reads the `resolve` clause of both bindings and
  fails on a key the loader does not accept that carries no such comment. Editorial: no
  requirement changes.
- The version line of AAP-SPEC.md reads "0.5.1-draft plus unreleased changes (see
  [Unreleased] in CHANGELOG.md)", and that of the broker profile "0.4.1-draft plus
  unreleased changes" in the same form. Both documents carried their released label while
  the entries in this section changed their requirements, so a reader comparing main with
  `draft-fane-opena2a-aap-02` found different requirements under the same version. The
  Status section of `README.md` names 0.5.1-draft and 0.4.1-draft as the last released
  versions and says that the text on main moves ahead of them between releases. At a
  release both lines move to the new versions without the suffix. Editorial: no
  requirement changes, and the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both
  documents are unchanged. `scripts/check_version_labels.py` fails when the [Unreleased]
  section records a change and a version line lacks the suffix, when the section records
  none and a line carries it, and when the version AAP-SPEC.md names is not that of the
  newest released section. It runs in CI through `scripts/validate_examples.py`.
- The SDK sample in `examples/orders-db-exchange.md` called `db.query(...)` with a SQL
  string on a `db` name the AIM Python SDK does not provide, so the sample did not run as
  written. The function now declares the `grant` parameter through which the
  `@agent.perform_action` decorator passes the broker-backed handle, and calls the handle's
  one method, `grant.request("GET", "/orders", query={"customer": customer_id})`. A
  paragraph after the sample states that `aim_sdk.current_grant()` returns the same handle
  and that `request` carries a logical HTTP operation to the broker.
  `scripts/test_sdk_sample.py` parses the sample and checks that every name the decorated
  function reads is defined, that the function obtains the handle, and that it calls only
  `request` with that method's parameters. Editorial: no requirement changes.
- `CONTRIBUTING.md` names one address for security findings and coordinated disclosure,
  info@opena2a.org. The line named that address on both sides of an "or", which
  suggested a second channel that does not exist. `scripts/test_contact_addresses.py`
  fails on any line of a document that names the same address twice. It runs in CI
  through `scripts/validate_examples.py`.
- `examples/orders-db-exchange.md` and `AAP-BROKER-PROFILE.md` (Section 12.1) name AI Agent
  Threat Matrix technique T-3002 "Environment Variable Leakage", the name its page carries;
  they named it "Environment Variable Exposure". `scripts/test_threat_matrix_names.py` holds
  the matrix's name for each of the four techniques the two documents cite (T-3002, T-3003,
  T-3006, T-8002) and fails when a citation names one otherwise. Editorial: no requirement
  changes.
- Section 9.4 names ATX and ATP, not AIP, as the specifications that cite its signature
  gate for their own signature arrays. ATX `core.md` and `ATP-SPEC.md` cite AAP Section
  9.4; `AIP-SPEC.md` does not mention it. The 0.5.1-draft entry below is corrected the
  same way. `scripts/test_signature_gate_citers.py` checks that the Section 9.4 sentence
  names exactly the specifications recorded as citing it. Editorial: no requirement
  changes, and the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY are unchanged.
- `scripts/test_signature_gate_citers.py` also reads the Section 9.4 sentence in the XML
  source of every Internet-Draft after the filed revisions -00 to -02 and fails when the
  sentence is missing or does not name exactly ATX and ATP. The text render is generated
  from that source. `draft-fane-opena2a-aap-02` is left as filed: its sentence still reads
  "ATX, ATP and AIP cite this rule", as the 0.5.1-draft entry records, and the test pins
  that reading. A `draft-fane-opena2a-aap-03` source passes only with "ATX and ATP cite
  this rule". Editorial: no requirement changes.
- Broker profile Section 8.5 cites the specification that defines each of two transport
  bindings. The `Agent-Trust-Credential` header was attributed to ATP, whose `ATP-SPEC.md`
  does not name it; the ATX specification does (`atx-spec/core.md` Sections 1.2 and 3.2),
  and the HTTP binding cites it. The A2A agent card binding placed the ATX under the `atp`
  object of the card; that object (ATP Section 3.4) has the members `did`, `trustProof`
  and `trustAuthorityDid`, and the ATX specification reads the credential from the `atx`
  field of the card (`atx-spec/core.md` Section 3.2), which the binding now names. The MCP
  manifest binding is unchanged. No requirement changes: the counts of MUST, MUST NOT,
  SHOULD, SHOULD NOT and MAY in both documents are unchanged.
  `scripts/test_transport_bindings.py` reads the list of Section 8.5 and checks both
  citations, the `atx` field, and that the agent card binding does not place the ATX in
  the `atp` object.
- The ML-DSA-65 decision note states the range of token lifetimes as "60 s BAC to 4 h
  STANDARD CGT"; it read "60 s BAC to 3600 s AIT", which left out the STANDARD tier of
  Section 4.3 (4 hours), four times the stated upper end. The note's conclusion, that
  signatures have no harvest-now-decrypt-later exposure, does not depend on the figure.
  Editorial: no requirement changes. `scripts/test_decision_ttl_range.py` checks that the
  range runs from the BAC's 60-second TTL (Section 6.1) to the longest TTL tier of Section
  4.3, named by its tier.
- The policy binding for `grant://orders-db` in broker profile Section 7.1 carries
  `audience: https://api.orders.internal`, as the binding in
  `examples/orders-db-exchange.md` does. At commit `660af0d` the policy loader of the
  reference implementation refuses a `resolve` clause in which `providerId`, `scope` or
  `audience` is not a non-empty string, so it still refused the Section 7.1 binding once
  `provider` and `ttl` were respelled as the comments on those lines say. The keys of the
  grammar are unchanged. `scripts/test_resolve_key_spelling.py` fails when either binding,
  read in the reference spelling, lacks one of those three keys. Editorial: no requirement
  changes.
- The reference implementation paragraph of `AAP-SPEC.md` names `authorization_details` and
  `aap_crit` in the minted claim set among the parts outside the implemented surface. The
  implementation status note of broker profile Section 14 lists them, without a section
  number, and the paragraph left them out. `scripts/test_reference_status.py` compared
  section numbers only; it also reads the items that note lists without a section number
  and fails when the paragraph does not name each name such an item carries. Editorial: no
  requirement changes.
- `scripts/test_examples_bindings.py` no longer imports `pathlib` without using it.
  `scripts/test_unused_imports.py` fails when a script in `scripts/` imports a name it
  never reads, and runs in CI through `scripts/validate_examples.py`.
- `python3 -m unittest scripts/test_examples_bindings.py` runs from the repository root: the
  file inserts its own directory into `sys.path` before it imports `check_naming`, as the
  other test files in `scripts/` that import a sibling script do, where it raised
  `ModuleNotFoundError`. `scripts/test_sibling_imports.py` imports each test file in
  `scripts/` under the module name that command uses, in a new interpreter started in the
  repository root, and fails with the error the import raised and, when the module it did
  not find is a sibling script, the line that inserts the directory. The new interpreter is
  given each `PYTHONPATH` entry of the run except one that is `scripts/`, so a package
  installed through `PYTHONPATH` is found, and it prints the error without color. The check
  imports each file without running its tests, then looks on `sys.path` for each sibling
  script the file imports inside a function and fails when one is not found. It does not
  import that script, so a script that fails to import where the test that imports it is
  skipped is not reported. Inside a function the check reads an `import` or
  `from ... import` statement and a call of `import_module` or `__import__` that names the
  module with a string literal; it does not read a name the function computes. It imports
  each file a second time with the `jsonschema` package made unavailable:
  `scripts/test_trust_class_grammar.py` and `scripts/test_validate_examples.py` skip the
  tests that need the package, where a run by path without the package failed to load them.
  The second import reports only an error the first did not raise, so one cause has one
  message; on an interpreter without the package, the first import's message for a file
  that fails because `jsonschema` is not found carries the advice to skip with
  `unittest.skipUnless`. The check runs in CI through `scripts/validate_examples.py`.
- The ML-DSA-65 decision note no longer credits its recommendation to a group it does not
  define or names a role by an abbreviation. Its status line says the decision proceeded
  with the option the ESCALATION section recommends, option (B) is marked "recommended",
  and the threat-model bullet of RATIONALE reads "Threat model:". The decision and its
  reasoning are unchanged. `scripts/test_decision_note_terms.py` checks that no note in
  `decisions/` credits a recommendation to a group by a possessive or qualifies a threat
  model with an abbreviation. Editorial: no requirement changes.
- The ML-DSA-65 decision note records when option (B) was adopted and when the -01
  resubmission condition was set (2026-07-16) without naming who approved them, and its
  ESCALATION heading no longer names who was asked. The decision and its reasoning are
  unchanged. `scripts/test_decision_note_terms.py` also fails when a note in `decisions/`
  contains a word ending in 's directly followed by go-ahead, gate, approval or sign-off
  ("Xyz's go-ahead"), or the phrase "requested from"; the match is case-sensitive.
  Editorial: no requirement changes.
- `examples/transport-bindings.md` agrees with broker profile Section 8.5. Its HTTP section
  said the ATX travels in a request header "as in ATP"; it now names the
  `Agent-Trust-Credential` header and cites the ATX specification for it
  (`atx-spec/core.md` Sections 1.2 and 3.2). Its A2A agent card section, its heading, the
  card in its message sequence, the first item of what the broker reads, and the summary
  table row placed the ATX in the card's `atp` object; each now names the `atx` field
  (`atx-spec/core.md` Section 3.2), and the section says that the `atp` object of the same
  card (`ATP-SPEC.md` Section 3.4) carries the agent's DID and trust proof, not the ATX.
  The entry under Added that introduced the example is corrected the same way. Informative:
  no requirement changes. `scripts/test_transport_bindings.py` now also reads the example
  and checks the header citation, the `atx` field in the agent card section and the summary
  table, and that no sentence of the example places the ATX in the `atp` object.
- Section 3.2 states that the issuing Registry named in `iss` sets the AIT lifetime,
  `exp - iat`, and that this specification sets no upper bound on it, unlike the CGT
  (Section 4.3), the DA (Section 5.3) and the BAC (Section 6.1). The `iat` / `exp` row
  described the window only as a "Validity window". The section names what a longer
  lifetime lengthens: the time for which a verifier accepts an AIT whose trust level or
  referenced ATX has since changed, and the time for which a receiver tracks its `jti`
  (Section 8.1). No requirement changes: the counts of MUST, MUST NOT, SHOULD, SHOULD NOT
  and MAY are unchanged. `scripts/test_ait_lifetime.py` checks that the `iat` / `exp` row
  of the AIT, CGT and BAC claim tables each states what governs `exp - iat`, and that the
  3600-second lifetime Section 3.2 cites for its example is the `exp - iat` of
  `examples/tokens/ait-v1.claims.json` and of the claim set the section prints.
- `scripts/test_decision_note_terms.py` finds each form its description names, and the
  description names only those. A possessive before recommendation, go-ahead, approval or
  sign-off is found in the singular and the plural ("the group's recommendation", "the
  editors' approval"), directly or with one word between ("Xyz's explicit go-ahead"), with
  the noun in any letter case and in the plural; the check on recommendation found only a
  plural possessive directly before the word, and the check on the other three only a
  singular one. "requested of" and "approved by" are found as "requested from" is, each in
  any letter case. A possessive before gate is found only when its word starts with a
  capital letter ("Xyz's gate"), so a sentence on a verification gate ("the verifier's
  gate rejects a missing family") no longer fails the test. The contractions it's, that's,
  there's, here's, what's, who's and let's are not read as possessives. Each form has a
  test phrase, so removing "approval" or "sign-off" from the pattern fails a test where
  all five tests passed. No decision note changes.
- The description of `scripts/test_decision_note_terms.py` no longer says its tests find
  the listed forms and no others. It names the two forms that credit no one and are found
  where a possessive would be: a word ending in s and closed by a straight or curly
  quotation mark ("the 'editors' approval"), and a contraction other than it's, that's,
  there's, here's, what's, who's and let's ("she's the approval"). A test checks that the
  patterns find both and that the description names them. The patterns and the decision
  notes are unchanged.
- `scripts/test_decision_note_terms.py` pins the two-letter minimum of its check on an
  abbreviation before "threat model". Its test phrases now include two capital letters,
  which are found ("XY threat model"), and one, which is not ("A threat model"). With a
  three-letter phrase alone, the test did not fail when the pattern read one capital
  letter as an abbreviation or required three. The pattern and the decision notes are
  unchanged.
- The description of `scripts/test_decision_note_terms.py` states a limit of its check on a
  possessive before gate: the capital letter is the only sign of a name it reads, so a
  common noun written with one is found as a name is ("Xyz's gate"), at the start of a
  sentence or a list item ("Verifier's gate rejects a missing family") and in a heading in
  title case. A note writes such a noun in lower case, with a word before it where it would
  start a sentence ("The verifier's gate"), and the failure of the test on a possessive
  before gate now prints that rewrite. The forms found are unchanged, and each case named
  here has a test phrase. No decision note changes.
- A test in `scripts/test_decision_note_terms.py` pins the paragraph of its description on a
  possessive before gate: the description must carry the sentence "The capital letter is
  the only sign of a name the tests read", the two examples found as a name ("Verifier's
  gate rejects a missing family", "The Verifier's Gate") and the rewrite that is not found
  ("The verifier's gate rejects a missing family"), and the printed rewrite must carry
  ("The verifier's gate"). Rewriting or removing that sentence passed all 14 tests before;
  it now fails one. The patterns and the decision notes are unchanged.

### Added

- Broker profile Section 6.13, revocation after resolution. The revocation checks of
  Section 6 steps 2 and 5 ran at resolution only, and no text said what a revocation that
  becomes visible to the broker after them does to an operation the broker has not issued,
  to an operation waiting on the escalation hook of Section 6.10 or in a queue, or to a
  downstream credential obtained before it. Before each downstream operation of step 8 the
  broker MUST repeat the following checks, whose outcome can change after a resolution has
  passed them and all of which read local state and the clock: the validity window of the
  ATX and the cached CRL under the freshness bound of Section 6.12 (step 2), the grant
  revocation list (step 5), and the expiry of the grant itself. The list is closed. The
  `created` and `nonce` checks of the HTTP binding and the challenge check of the A2A and
  MCP bindings (step 3) belong to one presentation and are checked once, since repeating
  them would fail every operation after the first, and policy (step 6) is not evaluated
  again: a policy change reaches an outstanding grant through the grant revocation list.
  If any of the repeated checks fails, whether the agent's ATX is on the CRL, the cached
  CRL is older than the bound for the grant's tier, the grant is revoked, or the ATX or
  the grant has expired, the broker MUST NOT issue the operation, MUST end the ephemeral
  worker, where one exists, and discard the downstream credential, and MUST return the
  opaque denial of Section 6.6. An approval, a place in a queue and a deferred start carry
  no authorization across a revocation or an expiry. Because the expiry of the grant is a
  repeated check, a downstream credential is not used for an operation issued after its
  grant has expired, whatever lifetime its issuer gave it. A broker SHOULD revoke a
  downstream credential at an issuer that supports RFC 7009 when the grant is revoked, and
  an operator SHOULD keep the lifetime of a downstream credential within the TTL of the
  grant tier. An operation already issued when the revocation becomes visible to the
  broker or when the grant expires, and the validity at a downstream of a credential the
  broker cannot revoke, are stated as outside the revocation and expiry guarantees.
  Section 6 step 2 points to Section 6.13 from its ATX revocation sentence, the Level 1
  row of Section 13 lists it, the implementation status note of Section 14 lists it
  outside the surface that section describes, and the broker profile lists RFC 7009 among
  its normative references, since its SHOULD in Section 6.13 cannot be implemented without
  reading it. AAP-SPEC Section 7.3 states the same in two sentences that carry no
  requirement keyword. The broker profile gains three MUST, one MUST NOT and two SHOULD;
  the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in AAP-SPEC.md are unchanged.
- AAP-SPEC Section 5.3 bounds the lifetime of a delegation by the delegator's grant: a DA's
  `exp` MUST NOT be later than its delegator's `exp`. The minting broker enforces the bound
  at mint time and a verifier that can resolve the delegator's grant MUST re-check it, as
  for `scope`, `trust_class` and `authorization_details`; in a chain the bound holds link
  by link. Section 5 bounded what a DA carries and not how long it lives, so a DA minted
  with an `exp` later than that of its delegator's CGT kept passing the expiry check that
  broker profile Section 6.13 repeats, which reads the `exp` of the grant being exercised,
  after the CGT had expired. With the bound that check covers every grant in the `act`
  chain, and Section 6.13 says so. Each generated DA fixture carries the `exp` of its CGT,
  so no fixture changes. AAP-SPEC.md gains one MUST NOT and one MUST; the counts of MUST,
  MUST NOT, SHOULD, SHOULD NOT and MAY in the broker profile are unchanged.
- `scripts/check_requirement_references.py` fails on an RFC that a Markdown document lists
  only under its informative references and cites in a sentence with a requirement
  keyword (MUST, SHOULD, MAY and the others of RFC 2119, in capitals), since a reference
  that must be read to implement a requirement is a normative reference. It reads every
  Markdown document with a References section sorted into Normative and Informative
  lists, takes the RFC numbers in the label of each entry, and does not read the
  References section itself or fenced code blocks; a sentence ends at a full stop before a
  capital letter, at a blank line, and before a heading, a list item or a table row. Each
  finding names the line and the keywords. It runs in CI through
  `scripts/validate_examples.py`.
- `scripts/check_requirement_references.py` reads citations and Markdown structure more
  closely. A citation is "RFC" or "RFCs" and a number, with each further number joined to
  it by a comma, a slash, "and" or "or" ("RFCs 6749 and 6750", "RFC 6749 and 6750"), in a
  sentence and in the label of a reference entry, and the full stop of "e.g.", "i.e.",
  "cf.", "vs." or "viz." does not end a sentence, so "SHOULD revoke it at the issuer, e.g.
  RFC 7009 revocation" fails. It does not read as prose a code span, an HTML comment, an
  indented code block (a line indented four or more spaces past the margin, or past the
  text of the list item that holds it, that does not continue a paragraph), or a fenced
  code block, whose fence closes only on a fence of the same character and at least the
  same length. A longer fence can therefore hold a shorter one, and an odd number of fence
  lines before the References section no longer hides that section, which made the check
  pass the whole document unread. A heading is a unit by itself and is not joined to the
  line after it, and a thematic break or a setext underline ends a unit. An RFC named only
  for contrast passes: a citation inside a phrase that begins with "unlike", "in contrast
  to", "in contrast with", "as opposed to", "rather than" or "instead of" and ends at the
  next comma, semicolon, colon or requirement keyword ("Unlike an RFC 6750 bearer token, a
  CGT MUST be bound to a key."), unless a relative clause follows the phrase; each failure
  line names that wording. The unit tests pin each of these, and six properties that no
  test covered: a sentence that ends at "?" or "!", an opening quote or bracket before the
  capital, the splits before a heading, a numbered list item and a table row, and a fence
  inside the References section.
- Section 11 lists the conformance suite, [AAP-CONFORMANCE], as an informative reference,
  as the -02 Internet-Draft does; the specification cites its reference verifiers and
  `conformance.json`. Editorial: no requirement changes.
- `scripts/check_references.py` checks that every reference listed in both the
  specification's Section 11 and the newest Internet-Draft render is in the same class
  (normative or informative) in both, and that the specification lists every OpenA2A
  family reference the render lists. A class the specification gives a reference after
  the render was made passes only while the [Unreleased] section of this changelog records
  it in the form `<label> is a normative reference` (or `an informative reference`), as it
  does for AIP above, so the next render must carry it. The check prints one class-parity
  line and runs in CI through `scripts/validate_examples.py`.
- `scripts/check_section_citations.py` checks each citation in which a family document is
  named next to a section number ("broker profile §8.1", "AIP Section 4.1", "Section 4.4.1
  of AAP-SPEC"), with the numbers listed directly after that number ("broker profile §7,
  §11"), in the Markdown documents of the repository, except this changelog and the dated
  notes in `decisions/`, and in the newest Internet-Draft render. A number further along
  the sentence is not read: in "the broker profile (§6, step 3, and §6.8)" the check reads
  §6 only. A citation that names the ATX text `core.md` rather than `atx-spec/core.md` is
  not read. A number cited from the
  specification or the broker profile must be a numbered heading of that document. Where
  the citing document's References section lists the cited document, the entry names its
  text file, and a document outside this repository is named by its text file in the
  citation or in that entry. A citation of "the spec" outside the specification fails, and
  in the render each document cited by number must have a reference entry. The check
  prints one census line: the citations per document, and the printed address of each
  document the render cites by number, with whether that address or the entry's annotation
  names the text file. For draft-fane-opena2a-aap-02 the [AIP] address names `AIP-SPEC.md`
  and the [AAP-BROKER-PROFILE] address does not name `AAP-BROKER-PROFILE.md`. It runs in CI
  through `scripts/validate_examples.py`; its unit tests pin the citation forms and the
  rules.
- `scripts/check_references.py` and `scripts/check_section_citations.py` tell a submitted
  render from the next one. A render is submitted when a released section of this changelog
  records it as "`draft-fane-opena2a-aap-NN` (submitted YYYY-MM-DD", as the 0.5.1-draft
  section does for -02; any other render is the next render. A submitted render cannot
  change, so there a recorded class change and a printed address that does not name its
  text file are reported. In the next render both fail: a class change the [Unreleased]
  section records fails until the render carries it, and a document cited by section number
  fails until the address or the annotation of its reference entry names its text file. A
  render made from the -02 source therefore lists [AIP] as a normative reference and, for
  broker profile Section 8.1, prints an address of `AAP-BROKER-PROFILE.md` or names it in the
  annotation (the -02 address, https://specs.opena2a.org/aap/broker-profile, does not name
  it). Both check lines end with the render's status, and unit tests run both checks on a
  copy of the -02 render as the next render.
- `scripts/check_raw_html.py` fails on an HTML tag in the prose of any Markdown file, such
  as an angle-bracket placeholder (`<YYYY-MM-DD>`) that a rendered page does not show, and
  on the other raw HTML CommonMark reads, where neither a blank line nor a line that
  begins a block quote splits it: a processing instruction (`<?x?>`), a declaration
  (`<!DOCTYPE html>`) and a CDATA section (`<![CDATA[x]]>`). A code span, a fenced code
  block and its info string, an escaped bracket, an autolink, the destination of an
  inline link (`[text](<...>)`, also after spaces or a line break) and an HTML comment
  pass, and so does a tag inside a paragraph that a blank line or a line that begins a
  block quote splits, which CommonMark does not read as raw HTML. The check takes a line
  to begin a block quote where it begins with more block quote markers (`>`) than any
  earlier line after the last blank line holds, and does not read the block quote markers
  of any other line as text. A tag that opens an HTML block at the start of a line (`<div`,
  `</div`, `<p`, `<pre`, `<table`, ...) fails even when a blank line splits it, as
  CommonMark reads that line as raw HTML. A processing instruction, a declaration or a
  CDATA section that a blank line or a line that begins a block quote splits passes, even
  where it begins a line and CommonMark reads it as an HTML block that continues past that
  line. It runs in CI through `scripts/validate_examples.py`.
- `scripts/check_spelling.py` fails on a British spelling of two word families in every
  Markdown file and Internet-Draft source, outside code (in Markdown, fenced code blocks
  and code spans; in the Internet-Draft source, `<sourcecode>`, `<artwork>` and `<tt>`
  elements): -our where American spelling has -or, and -ise or -isation where it has -ize
  or -ization, on the word stems the script lists, with any prefix. An -our word fails with
  any ending. An -is- word fails where one of the endings the script lists follows the -is-
  (-e, -ed, -er, -ers, -es, -ing, -ingly, -able, -ably, -ation, -ations, -ational), and
  passes with any other ending. Each finding names the line and the American spelling to
  write. Words whose American spelling ends in -our or -ise ("hour", "detour", "advertise",
  "exercise", "improvisation") pass. README.md now spells "honor" the American way, as the
  rest of the repository does. It runs in CI through `scripts/validate_examples.py`.
- `examples/transport-bindings.md`, a worked example of each initial binding of broker
  profile Section 8.5: the HTTP `Agent-Trust-Credential` header, the `atx` field of an A2A
  agent card and the reference in an MCP server manifest. For each it shows where the ATX
  travels, the proof of presenter identity of Section 6.8 (an RFC 9421 HTTP Message
  Signature, or a signed challenge), and what the broker reads before it evaluates policy.
  README.md described `examples/` as covering transport bindings while the directory held
  none; its entry now names each worked example and what it covers. Informative: no
  requirement changes, and the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in both
  documents are unchanged. `scripts/test_examples_bindings.py` fails when a binding that
  Section 8.5 lists has no heading in a Markdown file in `examples/`, and runs in CI through
  `scripts/validate_examples.py`.

## [0.5.1-draft] - 2026-10-02

Internet-Draft pairing: `draft-fane-opena2a-aap-02` (submitted 2026-10-02; document date
2026-09-30) is the current datatracker revision and carries this 0.5.1-draft;
`draft-fane-opena2a-aap-01` (submitted 2026-07-23; document date 2026-07-22) is the prior
revision there and carries 0.4.0-draft. The broker profile moves to 0.4.1-draft in lockstep.

### Changed

- Section 9.4 is marked as the one home of the family signature gate (every declared
  entry verifies; an ML-DSA-65 entry requires a verifying EdDSA entry; otherwise
  `HYBRID_INCOMPLETE`), which ATX and ATP cite. This release's Section 9.4, and
  `draft-fane-opena2a-aap-02`, also name AIP as citing it; AIP does not. The broker
  profile's validity window cites the family clock-skew bound in ATP Section 10.2.
- The `trust_class` example uses a domain-prefixed namespace (`acme.com/orders:read`), the
  AIP Section 4.1 grammar; a bare unreserved namespace is not a valid capability.
  Section 4.2 states that both aap-conformance reference verifiers match `trust_class`
  against a pattern that admits no domain prefix, that the claim schemas carry the same
  pattern, and that the JSON examples carry the unprefixed `orders:read`.
- Section 4.4 no longer dates the conformance verifiers' `aap_crit` status: both
  aap-conformance reference verifiers implement it, and that repository's
  `conformance.json` is the record of what they verify.
- RFC 9162 (Certificate Transparency Version 2.0) is an informative reference.
  `draft-fane-opena2a-aap-02` cites it once, at the transparency log in the Registry
  definition, and no requirement of this specification depends on it. The specification's
  list named RFC 6962 and the Internet-Draft renders named RFC 9162, both as normative.

## [0.5.0-draft] - 2026-09-08

Internet-Draft pairing: `draft-fane-opena2a-aap-00` carried the 0.3.0-draft text
(document date 2026-07-06, refreshed to the 0.4.0 content in #9),
`draft-fane-opena2a-aap-01` carries 0.4.0-draft (submitted 2026-07-23; document date
2026-07-22), and no datatracker revision carries this 0.5.0-draft (the -02 render moved
to 0.5.1-draft). The broker profile moves to 0.4.0-draft in lockstep. `draft-fane-opena2a-aap-02` was not submitted to the
datatracker by this release; `-01` remained the current revision there until 2026-10-02.

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
