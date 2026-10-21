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
  Both schemas also reject a `trust_class` that holds a line break, through a `not` keyword
  with the pattern `\n`: an ECMA-262 engine rejects `acme.com/orders:read` or `orders:read`
  followed by a line break under the two patterns alone, but the jsonschema package
  evaluates `pattern` with Python's `re.search`, where `$` also matches before a final line
  break, so without the `not` keyword both validated there.
  `scripts/test_trust_class_grammar.py` pins the accepted and rejected values for both
  schemas, those two among the rejected, and checks that the domain-prefixed class is
  carried by each claim set in `examples/tokens/` with a `trust_class` member (five CGT and
  DA claim sets), by the `trust_class` values of the JSON examples in AAP-SPEC.md, and by
  the `trustClass` of the broker policy examples in the broker profile and
  `examples/orders-db-exchange.md` and the `capability` of the SDK call in the latter.
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
  import that script, so a sibling script that is found but fails to import is not reported
  by the check, whether or not the test that imports it is skipped; the test that imports
  it reports the error when it runs. Inside a function the check reads an `import` or
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
  contains a singular possessive directly before go-ahead, approval or sign-off ("Xyz's
  go-ahead") or, when the word in the possessive starts with a capital letter, A to Z,
  before gate ("Xyz's gate"), or the phrase "requested from"; the nouns and the phrase are
  found in any letter case. Editorial: no requirement changes.
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
  capital letter, A to Z ("Xyz's gate"), so a sentence on a verification gate ("the
  verifier's gate rejects a missing family") no longer fails the test. The contractions
  it's, that's, there's, here's, what's, who's and let's are not read as possessives. Each
  form has a test phrase, so removing "approval" or "sign-off" from the pattern fails a
  test where all five tests passed. No decision note changes.
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
  possessive before gate: the capital letter, A to Z, is the only sign of a name it reads,
  so a common noun written with one is found as a name is ("Xyz's gate"), at the start of a
  sentence or a list item ("Verifier's gate rejects a missing family") and in a heading in
  title case. A note writes such a noun in lower case, with a word before it where it would
  start a sentence ("The verifier's gate"), and the failure of the test on a possessive
  before gate now prints that rewrite. The forms found are unchanged, and each case named
  here has a test phrase. No decision note changes.
- When docstrings are stripped (`python3 -OO`, `PYTHONOPTIMIZE=2`), `__doc__` is `None`, and
  `scripts/test_decision_note_terms.py` now reads its description from its source file into
  `__doc__`. Such a run raised `AttributeError` in the two tests that check the description;
  they now pass. A new test runs them with `-OO` in a subprocess, and another checks that the
  description read from the file is the docstring. The patterns, the description and the
  decision notes are unchanged.
- `scripts/test_sibling_imports.py` also reads its description from its source file into
  `__doc__` when docstrings are stripped, as `scripts/test_decision_note_terms.py` does. A
  `python3 -OO` run raised `AttributeError` in the test that checks the description; it now
  passes. A new test runs it with `-OO` in a subprocess, and another checks that the
  description read from the file is the docstring. The checks and the description are
  unchanged.
- `scripts/test_sibling_imports.py` parses its source with `optimize=0` to read its
  description, because on Python 3.14 the parse drops the docstrings when they are stripped.
  The validation workflow runs Python 3.12, where the parse keeps them, so the `-OO` test
  passed there without `optimize=0` and only a Python 3.14 run failed. A new test reads the
  description through a parse that drops stripped docstrings as Python 3.14 does, so the
  removal of `optimize=0` fails on every version. The checks and the description are
  unchanged.
- `scripts/test_decision_note_terms.py` parses its source with `optimize=0` to read its
  description, because on Python 3.14 the parse drops the docstrings when they are stripped.
  On Python 3.12, which the validation workflow runs, the parse keeps them with or without
  `optimize=0`. A new test reads the description through a parse that drops stripped
  docstrings as Python 3.14 does, on Python 3.12 as well, and checks that the same parse
  without `optimize=0` reads no description. The patterns, the description and the decision
  notes are unchanged.
- A test in `scripts/test_decision_note_terms.py` pins the paragraph of its description on a
  possessive before gate: the description must carry the sentence "The capital letter is
  the only sign of a name the tests read", the two examples found as a name ("Verifier's
  gate rejects a missing family", "The Verifier's Gate") and the rewrite that is not found
  ("The verifier's gate rejects a missing family"), and the printed rewrite must carry
  ("The verifier's gate"). Rewriting or removing that sentence passed all 14 tests before;
  it now fails one. The patterns and the decision notes are unchanged.
- That test in `scripts/test_decision_note_terms.py` now pins the whole paragraph, word for
  word, as a paragraph of the description, and checks each of its clauses against the
  patterns: a common noun with a capital letter, A to Z, before gate is found at the start
  of a sentence, after one, in a list item and in a heading in title case. Rewording a
  clause outside the four pinned phrases ("prints that rewrite" to "prints nothing", "at
  the start of a sentence or a list item" to "in the middle of a sentence or a table cell",
  "is found as a name is" to "is never found"), or adding a sentence to the paragraph,
  passed all 15 tests before; each now fails one. The patterns, the description and the
  decision notes are unchanged.
- The entry on the ML-DSA-65 decision note that records when option (B) was adopted
  describes the approval check of `scripts/test_decision_note_terms.py` as the later entry
  on that test does. It said a word ending in 's before gate fails the test and that the
  match reads letter case; the test finds a possessive before gate only when its word
  starts with a capital letter, A to Z, and finds go-ahead, approval, sign-off, gate and
  "requested from" in any letter case ("with Xyz's Go-Ahead", "REQUESTED FROM Xyz"). Tests
  in the same file read each entry under [Unreleased] that has the path
  `scripts/test_decision_note_terms.py` directly between two backticks. One fails when a
  sentence of such an entry has case-sensitive directly after is or are, unless the
  sentence names threat model and none of the nouns and phrases the checks find in any
  letter case. Another fails when a sentence of such an entry has the lower-case word gate
  and at least one of the lower-case words go-ahead, approval and sign-off, and does not
  contain "capital letter". These tests split an entry into sentences only where a period
  and then whitespace come directly before a capital letter A to Z, a backtick, a straight
  double quotation mark or an opening parenthesis. The patterns and the decision notes are
  unchanged.
- The resolution flow of `examples/orders-db-exchange.md` marks the three steps the v1
  reference implementation does not perform as drawn, with a `v1:` note in the form the
  policy sample uses for `jurisdiction`: version negotiation (step 2) is marked as a
  conformance Level 2 requirement and not performed, the broker's signing key (step 4) as
  held in memory and not rotated, and the audit record (step 7) as written and not signed.
  A paragraph after the flow names the broker profile section that defines each (Section
  8.1 for version negotiation, Section 11 for the rotating signing key, Section 6.7 for the
  signed audit log) and Section 13 for the Level 2 requirement, writing the broker profile's
  name next to each number so that `scripts/check_section_citations.py` resolves every one.
  The implementation status note of broker profile Section 14 adds the signature on audit
  records of Section 6.7 to what its list does not describe, and the reference
  implementation paragraph of `AAP-SPEC.md` cites it (broker profile §6.7) with the other
  parts outside that surface. Editorial: no requirement changes, and the counts of MUST,
  MUST NOT, SHOULD, SHOULD NOT and MAY in the three documents are unchanged.
  `scripts/test_worked_example_status.py` checks that each of the three steps carries its
  note, that the paragraph cites for each step a broker profile section whose text defines
  that step, that the citation check reads every section number in the paragraph, written
  after "Section", "Sections", "§" or "§§" or listed after such a number (the markers the
  citation check reads, so a "§99" or a "Sections 99" without the broker profile's name
  fails it, as does a number listed without its own marker after "Section" or "§", which
  that check does not read), and that the Section 14 note names the audit signature;
  `scripts/test_reference_status.py` checks that the AAP-SPEC paragraph cites Section 6.7.
- Three entries above state the rule of `scripts/test_decision_note_terms.py` on a
  possessive before gate with the letters its pattern reads: the word "starts with a
  capital letter, A to Z", as the description of the tests says. They named a capital
  letter without that range, and a word whose first letter is a capital outside it is not
  found ("Émile's gate"). The three are the entry on the ML-DSA-65 decision note that
  records when option (B) was adopted, the entry on the forms the description names, and
  the entry that corrected the first of them. The rewrite the test prints on such a
  possessive says "A to Z" as well. A new test fails when a sentence of an entry the tests
  read, of the description or of the printed rewrite has the five words before the comma
  in "starts with a capital letter, A to Z" and not "A to Z" directly after them, with or
  without the comma. The test that runs the tests on the description with docstrings
  stripped (`python3 -OO`) runs it as well. The pattern and the decision notes are
  unchanged.
- The changelog test of `scripts/test_decision_note_terms.py` on case-sensitive, written
  with a hyphen or a space and in any letter case, reads sentences. It failed on those
  words directly after is or are anywhere in an entry it read, so an entry could not say
  what is true of another check. The check on an abbreviation before "threat model" is
  case-sensitive ("xyz threat model" is not found). Of the sentences of an entry that have
  those words directly after is or are, the test now passes only one that names threat
  model and none of the nouns and phrases the checks find in any letter case:
  recommendation, go-ahead, approval, sign-off or gate, singular or plural, "requested
  from", "requested of" or "approved by"; a sentence ends only where the earlier entry
  says, where a period and then whitespace come directly before a capital letter A to Z, a
  backtick, a straight double quotation mark or an opening parenthesis. The test reads
  characters, not grammar: a sentence that names one of them fails whatever it calls
  case-sensitive, and a sentence that names threat model and none of them passes whatever
  it calls case-sensitive. Its failure says where a statement on the check on threat model
  goes. The patterns and the decision notes are unchanged.
- Two descriptions of which changelog entries the tests of
  `scripts/test_decision_note_terms.py` read match what the tests look for. The earlier
  entry said they read each entry under [Unreleased] "that contains the code span", and the
  docstring of the function that selects the entries said "that names this file"; an entry
  is read only when the path of the file stands directly between two backticks. An entry
  that names the file only without backticks, or only with a space or other text between a
  backtick and the path, is not read, so none of these tests applies to it. Both now
  describe that selection, and the docstring of the test class and the names of two tests
  speak of an entry that is read, where they spoke of any entry. A new test pins the
  selection with each of those forms, and another fails when a sentence of an entry read
  names [Unreleased] and does not have "directly between two backticks", or when no
  sentence of an entry read names [Unreleased].
- The changelog test of `scripts/test_decision_note_terms.py` on case-sensitive no longer
  passes a sentence because it names none of the nouns and phrases of the approval check.
  An entry could name go-ahead in one sentence and call its match case-sensitive in the
  next ("Its match"), or say the same of the check on recommendation, a noun the test did
  not list, and every test passed. A sentence that has those words directly after is or
  are now passes only when it names threat model, in any letter case, and none of the five
  nouns and three phrases the checks find in any letter case, recommendation among them.
  The entry above on that test said "a sentence that names none passes"; it and the entry
  that first described the test now state this rule. The failure says that a statement on
  the check on an abbreviation before threat model goes in such a sentence. The test still
  reads characters, not grammar: a sentence that names threat model and none of them
  passes whatever it calls case-sensitive. The patterns and the decision notes are
  unchanged.
- Two more entries above give the letters the pattern of
  `scripts/test_decision_note_terms.py` reads where they say that a common noun with a
  capital letter, A to Z, before gate is found: the entry on the limit the description
  states and the entry on the test that pins the whole paragraph. They named a capital
  letter without that range, and a common noun whose first letter is a capital outside A
  to Z is not found ("Église's gate rejects a missing family"). The second of the two now
  names the file with its path directly between two backticks, so the tests read it; it
  named only "That test". A new test fails when a sentence of an entry read has "common
  noun" and "capital letter", in any letter case, and not "A to Z", and when no sentence
  of an entry read has the first two. The pattern, the description and the decision notes
  are unchanged.
- A test of `scripts/test_decision_note_terms.py` pins where its changelog tests end a
  sentence: where a period and then whitespace come directly before a capital letter A to
  Z, a backtick, a straight double quotation mark or an opening parenthesis. No test
  covered the last three, and a split that read only a capital letter A to
  Z there passed all 24 tests; it now fails one. The test has a phrase for each of the
  four, for a lower-case letter, a digit, a capital letter outside A to Z, a curly and a
  single quotation mark and an opening bracket, before which no sentence ends, and for a
  period with no whitespace after it and whitespace with no period directly before it. It
  also checks that a statement on threat model after a sentence that names go-ahead passes
  the test on case-sensitive with each of the four at its start. The split is unchanged.
- The test of `scripts/test_decision_note_terms.py` on the changelog sentence that says
  which entries the tests read fails when no sentence of an entry read says it. It read
  only a sentence with the words "read each entry under" before the name of the section
  and passed when none had them, so the sentence in the entry above could be reworded
  ("read every entry", "that contains the code span") with every test passing. It now
  reads each sentence of an entry read that names [Unreleased] and fails when one does not
  have "directly between two backticks", or when no sentence names the section. The entry
  above that described the test states this, and a new test pins both failures. The
  patterns and the decision notes are unchanged.
- The test of `scripts/test_decision_note_terms.py` that pins where its changelog tests end
  a sentence reads each printable ASCII character other than whitespace on both sides of
  the whitespace. It read one phrase for each of a few characters, so a split that also
  ended a sentence before a hyphen, an asterisk or "<", or after "!" or ":", passed all 27
  tests, as did a split that read only B to Z or only A to Y. For each such character
  directly after the whitespace, the test now checks that a sentence ends before it when,
  and only when, it is a capital letter A to Z, a backtick, a straight double quotation
  mark or an opening parenthesis; for each directly before the whitespace, that a sentence
  ends after it when, and only when, it is a period. The split is unchanged.
- The changelog test of `scripts/test_decision_note_terms.py` on a common noun with a
  capital letter, A to Z, before gate reads "common noun" and "capital letter" in any
  letter case. It read only the lower-case words, so an entry read whose sentence starts
  with either ("Common nouns with a capital letter before gate are found as names are.")
  passed all 27 tests without A to Z, while the same sentence starting "The common nouns"
  failed. Such a sentence now fails the test, which has a passing and a failing sentence
  that starts with each of the two. The entry above that first described the test says
  so. The pattern, the description and the decision notes are unchanged.
- The changelog test of `scripts/test_decision_note_terms.py` on a common noun with a
  capital letter, A to Z, before gate says what to write when no sentence of an entry read
  states it. With "common noun" reworded in every entry, it failed with only "False is not
  true"; the failure now says that no sentence of an entry read has "common noun" and
  "capital letter", and that the sentence that says such a noun is found before gate has
  both and "A to Z". A new test pins that failure and the failure on a sentence that has
  both and not "A to Z". The patterns and the decision notes are unchanged.
- `scripts/test_worked_example_status.py` counts each section number of a list in the
  paragraph after the resolution flow of `examples/orders-db-exchange.md`, reading a list
  after "Sections" or "§§" as `scripts/check_section_citations.py` does ("Sections 6.8 and
  6.9", "§§6.8, 6.9"). It counted only the first number of a list, so a named list could
  hide an unnamed number: "broker profile Sections 6.8 and 6.9. Step 4 is Section 6.9."
  passed the comparison with the numbers the citation check reads, although that check
  does not read the unnamed "Section 6.9", and "broker profile Sections 6.8 and 6.9."
  failed it, although that check reads both. The first now fails and the second passes, in
  each of three list forms a new test pins. Counting with the grammar of that check also
  counts the other numbers it reads: a number written without a space after "Section" or
  "Sections" ("Section8"), a number after "Section" or "Sections" joined to the word before
  it ("appliesSections 77"), and a number with a letter suffix, counted as "6.8a" where the
  test counted "6.8". The paragraph cites no list and none of these forms, so the test
  passes on it as before; the entry above that describes the test says that lists are
  counted. The citation check is unchanged.
- `scripts/test_worked_example_status.py` counts once a section number that two
  citations of the broker profile read, and counts a number listed without its own marker
  after "Section" or "§". The comparison took every number of every citation of the broker
  profile that `scripts/check_section_citations.py` returns, and that check returns two
  citations of "broker profile Sections 6.8 and 6.9 of the broker profile", one for the name
  before the numbers and one for the name after them. So that phrase followed by "Step 4 is
  Section 6.8 and step 5 is Section 6.9." passed the comparison, although that check reads
  neither unnamed number, and the phrase alone failed it, although that check reads both.
  After "Section" or "§" that check reads a later number of a list only when it has its own
  marker, and the test counted with the same grammar, so neither read the 6.9 of "broker
  profile Section 6.8 and 6.9" and the comparison passed. The test now compares where each
  number is written with where that check reads one, and counts each later number of a list
  after any of the four markers. The first phrase with the unnamed numbers and "broker
  profile Section 6.8 and 6.9" now fail, the phrase alone passes, and new tests pin each,
  with the same for one number and for "§" lists. Each citation the check returns also
  records where its numbers start; what the check reads and reports is unchanged. The
  paragraph is unchanged and the test passes on it.
- `scripts/test_worked_example_status.py` pins the two rules of its comparison that no test
  failed without: it compares section numbers by where they are written, so "Step 4 follows
  broker profile Section 6.8, and step 5 also follows broker profile Section 6.8." passes
  it, and it reads only citations of the broker profile, so the paragraph with "(AAP-SPEC
  §4.4)" or "(AIP Section 4.1)" added fails it. A new test pins each. The test now pairs
  the numbers of a citation with where they start strictly, so a citation that records no
  positions raises an error instead of adding no numbers, and a third new test pins that.
  The entry above now says that the comparison took the numbers of citations of the broker
  profile only. The paragraph and the citation check are unchanged.
- `scripts/test_worked_example_status.py` names both context managers of the test for a
  citation that records no positions in one `with` statement, where one `with` statement
  held the other; what the test checks is unchanged. `scripts/test_nested_with.py` fails
  when a script in `scripts/` holds a `with` statement whose body is one other `with`
  statement of the same kind and nothing else, and runs in CI through
  `scripts/validate_examples.py`. Six test files hold one such statement each
  (`test_check_naming.py`, `test_check_raw_html.py`, `test_check_requirement_references.py`,
  `test_check_spelling.py`, `test_check_status_claims.py` and
  `test_check_version_labels.py`): they are unchanged, the new test lists them, and it
  fails when one of them holds a second.
- `scripts/test_nested_with.py` holds each script to the number of nested `with`
  statements its table records, not to at most that number, and fails when the table
  names a file that is not in `scripts/`. A listed file whose statement had been combined
  still passed, as did an entry for a file that had been deleted or renamed, so a stale
  entry stayed in the table although the comment above `KNOWN` says a file leaves the
  table when its statements are combined. New tests pin a listed file that holds fewer
  than its entry records, an entry naming no file, and both stale entries failing the
  check of the scripts. The six files the table lists each hold one such statement, and
  the test passes on them.
- `scripts/test_nested_with.py` fails when this changelog gives the rule the entry above
  takes from the comment above `KNOWN`, the table of that test, after any words but "the
  comment above `KNOWN` says", when the changelog does not give the rule, and when that
  comment no longer states it. The entry above now reads those words where it read "the
  test's docstring says": before the change that entry records, the docstring of the test
  had no such sentence and only the comment did. Two more tests pin how the changelog and
  the comment are read. The table and what the other tests check are unchanged.
- `scripts/test_nested_with.py` reads the Python files in the directories below `scripts/`
  as well as those in `scripts/` itself, as its docstring says, where it read only
  `scripts/*.py`; no such file exists today, so no result changes. The six files its table
  lists are named by their path relative to `scripts/`, so a file of the same name in a
  directory below is held to none and does not keep an entry in the table. Two new tests
  pin the function that lists the files and how a path is held to the table.
- `scripts/test_nested_with.py` fails when its check of the scripts stops reading the
  directories below `scripts/`. The two tests the entry above records call the functions
  the check is built from and not the check, so every test passed with the check reading
  only `scripts/*.py` again. A new test runs the check over a temporary directory tree: the
  check fails once when a file one or two directories down holds a nested `with`
  statement, and passes when that file names both context managers in one statement. The
  entry above now says what its two tests pin, where it said they pin both changes. What
  the check reads and its table are unchanged.
- `scripts/test_nested_with.py` reads a capital letter of this changelog as its small one
  when it looks for the rule it takes from the comment above `KNOWN` and for the words the
  rule is given after. It compared the letters as written, so an entry that gave the rule
  as a sentence of its own, with a capital first letter, after "As the test's docstring
  says:" passed, although the entry on that test above says it fails after any words but
  those it names. Such an entry now fails, and a sentence that opens with "The comment
  above `KNOWN` says" and then gives the rule counts as naming the comment. Two new tests
  pin how a capital letter is read and that the test of this changelog fails when such an
  entry is added to it. This changelog gives the rule once, after those words, and the
  test passes on it.
- `scripts/test_nested_with.py` reads only the Python files of the repository in `scripts/`
  and the directories below it. In a git checkout these are the files git lists there: the
  ones it tracks, and the ones it does not track and does not ignore. The test read every
  `*.py` file there, so with a local virtual environment in `scripts/.venv/`, which
  `.gitignore` lists, it failed on each file of that environment that holds a `with`
  statement nested in another. Where git is not installed or `scripts/` is not in a git
  checkout, the test reads the files in no directory whose name starts with ".", so a
  directory that git would ignore and that is not hidden, such as `scripts/venv/`, is still
  read there. Three new tests pin the files read in a git checkout that carries this
  repository's `.gitignore`, where a tracked file deleted from the working tree is left
  out, the files read without git, and that git gives no list when it fails or is not
  installed. The test for subdirectories now runs without git's list, so its result does
  not depend on where the temporary directory is. In a checkout with no ignored Python file
  below `scripts/` the test reads the files it read before, and the six files its table
  lists are unchanged.
- `scripts/test_nested_with.py` runs its test of the check over a temporary directory tree
  without git's list. The entry above says the test for subdirectories runs without it:
  that was the test of the function that lists the files, and the test of the check still
  asked git, which gives an empty list for a temporary directory in a git work tree whose
  `.gitignore` lists it. There the subtest that expects the check to pass failed, and the
  two that expect one failure passed on the first assertion of the check, that the test
  file is among the files read, and not on the nested `with` statement. A new test runs
  that test with its temporary directories in such a work tree and fails without the
  change. What the check reads and its table are unchanged.
- `scripts/test_nested_with.py` pins that the function listing the Python files of the
  repository gives a path once when the list it reads names that path three times. The
  function already read the list as a set, and no test failed with the set removed: the 25
  tests the file held passed. Two new tests fail with it removed. One gives the function a
  list that names one path three times. The other builds a git checkout whose index holds
  stages 1, 2 and 3 of one file, the entries a merge leaves for a file with a content
  conflict, and git lists that path three times there. The function and the table of the
  test are unchanged.
- `scripts/check_naming.py` lists the documents git tracks only when the directory it
  checks is the top directory of a git work tree. Below the top of one, as a temporary
  directory inside a work tree is, git listed none of the files a test had written there,
  so the check and the checks that take their documents from `check_naming.documents`
  (`check_raw_html.py`, `check_requirement_references.py`, `check_section_citations.py`
  and `check_spelling.py`) read no document. With the temporary directory inside a work
  tree that ignores it, that gave eight failures in seven tests: one in
  `test_check_raw_html.py` and three each in `test_check_requirement_references.py` and
  `test_check_section_citations.py`. Such a directory is now read as a directory outside
  git is, every matching file outside a hidden directory, and those tests pass there. A new
  test pins it for a directory below the top of a work tree that the work tree ignores and
  for one it does not. At the top of a checkout the check reads the tracked files, as
  before.
- `README.md` is shorter: under its unchanged header it holds the Specification list first,
  a short form of the two use cases, a Documentation list and the License. Its reference
  text moved, as written, to pages it links: the use cases in full to `docs/use-cases.md`;
  the one principle, the decision / enforcement split, the three CPI modes and the two
  layers to `docs/overview.md`; the Reference implementation section to
  `docs/reference-implementation.md`; and the Status section, with the released versions
  and the current Internet-Draft revision, to `docs/status.md`. The Contributing paragraph
  is covered by `CONTRIBUTING.md`, which the Documentation list links. The README's
  conformance-suite command is marked `noexec`, with its reason in `docs/examples.json`,
  and shows no output; the summary line it printed is in `docs/use-cases.md`.
  `scripts/check_status_claims.py` also checks `docs/use-cases.md`,
  `docs/reference-implementation.md` and `docs/status.md`, and
  `scripts/test_readme_tokens.py` reads the tokens the suite rejects from
  `docs/use-cases.md`, the tokens it accepts from both pages, and checks that the README
  states the pattern limit and links the token list. No requirement, schema or token
  changes.
- `README.md` is shorter again: the two use cases, with the conformance-suite command, are
  in `docs/use-cases.md` only, and the README keeps the second one's statements on the
  published tokens under the Specification list, with the `examples/` line split in two. No requirement, schema or
  token changes.
- `scripts/check_section_citations.py` says on its census line whether the address or the
  annotation of a render's reference entry names the text file. For an entry whose
  annotation alone named it, the line said "names", as for an address that names it; it
  now says "annotation names", and "address names" for an address. It reads a link target
  after a name up to 256 characters, so a run of "AIP](" without a closing parenthesis is
  not read to its end again from each name in it: 100,000 characters of it took about 5 s
  and take 0.03 s. The entry under Added that describes the check and the check's docstring
  now list the same forms the check does not read, among them two that neither stated: a
  number in parentheses after the bare name AIP, ATP or ATX, and a number listed without
  its own marker after "Section" or "§". Both also say that a number after a link target
  longer than 256 characters is not read and that the render's citations of AAP-SPEC are
  not checked. The docstring of `citations()` says that it returns the citations in which
  a name sits next to a section number. New tests pin the census wording, the bound, the
  run time and the forms the docstring lists, and the two exemptions that no test pinned:
  "Section 4 of the spec" passes in `AAP-SPEC.md` and fails in another document, and the
  render's citations of AAP-SPEC are not resolved, need no reference entry and are not
  counted.
- `scripts/test_validate_examples.py` patches the `check` of `scripts/check_references.py`
  and of `scripts/check_requirement_references.py` in its tests of `validate_examples.main`,
  which ran both on the repository, and asserts that `main` calls once each check it
  patches, `scripts/check_naming.py` included; two new tests pin that a failure of either
  of the two fails validation.
- The CGT and DA claim schemas reject a `trust_class` that holds a line break, as the
  `trust_class` entry above describes. `scripts/test_trust_class_grammar.py` reads the
  claim sets it checks from `examples/tokens/*.claims.json`, taking each with a
  `trust_class` member, where it read a list of five file names, and reads the
  `trustClass` of the broker policy examples in the broker profile and
  `examples/orders-db-exchange.md` and the `capability` of the SDK call in the latter. It
  reads the same five claim sets, and each of the three Markdown values is
  `acme.com/orders:read`.
- In `schemas/`, each member whose `pattern` ends with `$` rejects a value that holds a
  line break, as `trust_class` in the CGT and DA claim schemas already did: a `not`
  keyword with the pattern `\n` sits beside each of the other 16 such patterns. They are
  `atx_reference` and `jti` in the AIT claim schema; `atx_reference`, `binary_hash` and
  `jti` in the BAC claim schema; `jti`, `cnf.jkt` and the `type` of an
  `authorization_details` entry in the CGT and DA claim schemas, and `delegator_atx` in
  the DA claim schema; the grant reference itself in `grant-reference-v1.schema.json`;
  and `payload` and the `protected` and `signature` of a `signatures` entry in
  `jws-general-v1.schema.json`. An ECMA-262 engine rejects a well-formed value followed by
  a line break under each of those patterns, but the jsonschema package evaluates `pattern`
  with Python's `re.search`, where `$` also matches before a final line break: with
  jsonschema 4.26.0, for each of those members, a published example with a line break
  appended to that member's value validated against its schema. The patterns are unchanged
  and no character they match is a line break, so the `not` keyword changes no verdict of
  an ECMA-262 engine, and under the jsonschema package a value that holds no line break
  gets the same verdict as before. The description of each of the six schemas says why the
  `not` keyword is there. `scripts/test_schema_line_breaks.py` lists the 18 members whose
  subschema holds a pattern that ends with `$`, the two `trust_class` members among them,
  and fails when a schema holds such a pattern at a member it does not list or it lists a
  member that holds none. For each member it appends a line break to the value of a
  published example and checks that the schema rejects the example at that member, and it
  checks that the schema accepts the value, the value followed by a line break or by a
  carriage return and a line break, and the value preceded by a line break exactly when
  ECMA-262 matches it, reading the final `$` of a pattern as Python's `\Z`. It runs in CI
  through `scripts/validate_examples.py`, which runs the unit tests in `scripts/`.

### Added

- `draft-fane-opena2a-aap-03`, the next Internet-Draft revision (document date
  2026-10-21): its XML source and the text render generated from it. Its Section 9.4
  sentence reads "ATX and ATP cite this rule", where `draft-fane-opena2a-aap-02`, left as
  filed, reads "ATX, ATP and AIP cite this rule". It carries these changes recorded in
  this section for AAP-SPEC.md into the render: the capability grammar of AIP Section 4.1
  for `trust_class`, with the legacy `namespace:action` form a verifier accepts under
  claim schema version 1, and `acme.com/orders:read` in the four JSON examples that carry
  `trust_class`; the bound on a DA's `exp`; the checks a broker repeats before each
  downstream operation of a resolution (broker profile Section 6.13); the paragraph on
  the AIT lifetime, which the issuing Registry sets; the term DID, with a DID-OPENA2A
  entry among the normative references; the implementation status sentences, which name
  the record that holds the status and carry no date and no "yet"; the reserved ML-KEM
  row and the RECOMMENDED `EdDSA` default on foreign-interoperability paths, stated
  without "yet"; and the Section 9.4 sentence. The render lists AIP among its normative references, as
  AAP-SPEC.md does, and its broker profile entry prints the address of
  `AAP-BROKER-PROFILE.md`, whose section numbers the render cites. The abstract's
  paragraph on what the revision changes describes -03, and the passages that said "this
  revision" of what -02 changed name revision -02. Against the -02 source it has one
  more MUST NOT (a DA's `exp`), two more MUST (a verifier treats the legacy `trust_class`
  form as well formed, and re-checks a DA's `exp` where it can resolve the delegator's
  grant) and one more SHOULD (a broker mints the AIP grammar); the counts of SHOULD NOT,
  MAY, REQUIRED, RECOMMENDED and OPTIONAL are unchanged. No released section of this
  changelog records it as submitted, so `scripts/check_references.py` and
  `scripts/check_section_citations.py` read it as the next render; both pass on it, as do
  `scripts/check_status_claims.py`, `scripts/check_naming.py` and
  `scripts/check_spelling.py`. Rendered with xml2rfc 3.34.0 (exit 0; its one warning is
  the consensus default, which the -02 source also produces); no line of the text render
  exceeds 72 characters. `scripts/test_signature_gate_citers.py` fails when the newest
  render is not a revision after -02, or when its XML source or its text render does not
  name exactly ATX and ATP as citing Section 9.4.
- Section 2 defines the term DID: a `did:opena2a` identifier, the value type the claim
  tables name DID. The entry cites `did-method-opena2a` Sections 3.1 and 3.1.1, the two
  sections that Section 3.1 of that specification names as the one home of the
  `did:opena2a` string form for the specification family, and restates no rule of its
  ABNF. DID-OPENA2A is a normative reference (`did-method-opena2a.md`); the submitted
  `draft-fane-opena2a-aap-02` render is unchanged. Editorial: no requirement changes, and
  the counts of MUST, MUST NOT, SHOULD, SHOULD NOT and MAY in AAP-SPEC.md are unchanged.
  `scripts/check_section_citations.py` reads a citation of `did-method-opena2a` as it
  reads one of AIP-SPEC, ATP-SPEC or atx-spec/core.md, so the citation must resolve to a
  References entry that names `did-method-opena2a.md`, and
  `scripts/test_did_syntax_citation.py` checks that AAP-SPEC.md carries the citation and
  the entry and defines none of the ABNF rules `opena2a-did`, `resource-type` and
  `resource-id`.
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
  notes in `decisions/`, and in the newest Internet-Draft render, except the render's
  citations of AAP-SPEC, the specification it renders. It does not read a number further
  along the sentence (in "the broker profile (§6, step 3, and §6.8)" it reads §6 only, and
  in "AAP-SPEC §9 and the claim-semantics rules of §4–§6" §9 only), a number listed without
  its own marker after "Section" or "§" ("AIP §4.1, 4.2" reads 4.1 only), a number in
  parentheses after the bare name AIP, ATP or ATX, which also names a protocol or a
  credential (nothing is read in "AIP (Section 4.1)"), a citation that names the ATX text
  `core.md` rather than `atx-spec/core.md`, or a number after a link whose target is longer
  than 256 characters. A number cited from the
  specification or the broker profile must be a numbered heading of that document. Where
  the citing document's References section lists the cited document, the entry names its
  text file, and a document outside this repository is named by its text file in the
  citation or in that entry. A citation of "the spec" outside the specification fails, and
  in the render each document cited by number must have a reference entry. The check
  prints one census line: the citations per document, and the printed address of each
  document the render cites by number, with whether that address or the entry's annotation
  names the text file ("address names", "annotation names" or "does not name"). For
  draft-fane-opena2a-aap-02 the [AIP] address names `AIP-SPEC.md`
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
