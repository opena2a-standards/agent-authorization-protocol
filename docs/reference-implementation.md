# Reference implementation

A v1 **Exchange** broker (RFC 8693) is implemented in the Secretless broker library, with an
end-to-end conformance test proving the §4 invariant over the broker's Unix socket. Two limits are
worth stating plainly rather than discovering later. The exchange is exercised against a fake
transport injected into the provider adapter, not against a live identity-provider tenant. And a
`secretless broker` daemon that does not construct the grant resolver from operator configuration
returns 404 on `POST /grant`; whether a given release constructs it is recorded in the reference
implementation's repository, and the operator-facing grant-binding configuration is tracked in
[opena2a-standards/agent-authorization-protocol#1](https://github.com/opena2a-standards/agent-authorization-protocol/issues/1).

The developer surface is the `@agent.perform_action` decorator of
OpenA2A AIM (Agent Identity Management). See
[`examples/orders-db-exchange.md`](../examples/orders-db-exchange.md) and
[`AAP-BROKER-PROFILE.md` §14](../AAP-BROKER-PROFILE.md#14-reference-implementation-informative).
