# Contributing to AAP

The Agent Authorization Protocol is authored in the open and published with a working reference implementation. It is early, and we are looking for co-authors and contributors to help shape it before it goes to an external standards body. Your review, critique, and independent implementation work all carry weight on the spec.

## What we are looking for

- Review and critique. Read [AAP-SPEC.md](AAP-SPEC.md) and the [broker profile](AAP-BROKER-PROFILE.md) and tell us where they are ambiguous, where they leave interoperability gaps, or where the decision and enforcement split does not hold up.
- An independent second implementation. A non-reference broker, or an independent implementation of the three credential-provider modes (retrieve, assume, exchange), is the strongest signal that the spec is sound.
- Security audit and threat modeling of the spec itself, not just an implementation.
- Authorization and delegation expertise. AAP resolves trust into scoped access without the credential value entering the agent's reasoning context. We want input from people who have built OAuth token exchange, STS-style credential brokering, policy engines, or delegation chains, and who can stress-test the default-deny model.
- We need the broker reference implementation (RFC 8693 token exchange, see this repo's issue #1) and review of the delegation model from authorization and identity experts.

## Who we are looking for

We especially welcome:

- Security and cryptography researchers, including academic and PhD-level work.
- Standards-process experts (W3C, IETF, OpenTelemetry) who can help take these specifications to external bodies.
- Engineers building agent platforms and runtimes, for independent implementations and adoption.
- Red teamers and security auditors.

## How to contribute

- Open an issue or pull request on this repository.
- Or email info@opena2a.org with "co-author" in the subject line.
- For security findings or coordinated disclosure, email info@opena2a.org or info@opena2a.org.

Small fixes (typos, broken links, clarifications) can go straight to a pull request. For anything that changes the protocol surface, the broker profile, or the credential-provider modes, open an issue first so the change can be discussed before implementation work begins.

## Ground rules

- Contributions are licensed under Apache-2.0, consistent with the project license.
- Be specific and evidence-based. Point to the section, the field, or the failing case.
- No purely theoretical claims without a path to validation. If you propose a change, describe how it could be tested or implemented.
