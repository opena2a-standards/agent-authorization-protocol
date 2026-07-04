# Changelog

All notable changes to the Agent Authorization Protocol specification are
documented here. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
Versions follow the OpenA2A spec-family ladder `MAJOR.MINOR.PATCH-{draft|rcN|final}`.

## [Unreleased]

### Changed

- Authorship normalized to the spec-family convention (`OpenA2A`), matching
  `AAP-BROKER-PROFILE.md`, AIP-SPEC, and ATP-SPEC; named individual authors
  will be attributed at IETF Internet-Draft submission.

### Added

- This changelog.

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
