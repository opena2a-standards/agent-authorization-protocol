# Worked example: presenting the ATX over each transport binding

Broker profile §8.5 names three initial bindings, three ways an ATX reaches a broker: an HTTP
header, an A2A agent card and an MCP manifest. [`orders-db-exchange.md`](./orders-db-exchange.md)
presents the ATX on the local unix socket. This example sends the same request, an agent that
holds the trust class `acme.com/orders:read` asking for `grant://orders-db`, over each of the three
network bindings. For each one it shows where the ATX travels, the proof of presenter identity the
binding requires (broker profile §6.8), and what the broker reads before it evaluates any policy.

Paths, host names, request bodies and member names that the broker profile does not fix are
illustrative and are marked as such.

## Summary

| Binding | Where the ATX travels | Proof of presenter identity | What the broker reads |
|---|---|---|---|
| HTTP | the `Agent-Trust-Credential` request header | an RFC 9421 HTTP Message Signature over the request | the header, `Signature-Input`, `Signature`, `Content-Digest` and the body |
| A2A agent card | the `atx` field of the agent's `/.well-known/agent.json` | a challenge the broker issues on the A2A channel, signed by the presenter | the card's `atx` field, the signed challenge and the grant reference |
| MCP manifest | a reference in the MCP server's manifest | a challenge the broker issues on the MCP channel, signed by the presenter | the manifest's reference, the ATX it points to, the signed challenge and the grant reference |
| Local unix socket, for contrast | the broker's socket | the OS peer credentials of the connecting process | the ATX and grant reference on the socket, and the peer uid and gid |

## What the three bindings share

Only steps 1 to 3 of broker profile §6 depend on the binding: the broker receives the ATX, the
grant reference and the presentation proof; verifies the ATX locally (signatures, suite, validity
window, cached CRL); and binds the presentation to the presenter. From step 4 on, the flow is the
one in [`orders-db-exchange.md`](./orders-db-exchange.md), whatever the binding.

- **The ATX alone proves nothing about the presenter.** The A2A agent card publishes it, so any
  party can copy it. The step 3 proof is what ties the presentation to the agent the ATX names.
- **The verification key.** For a network binding the broker verifies the proof under the ATX
  subject key where the ATX carries one. The current ATX 1.1 format carries none, so the broker
  uses the key registered for the agent DID under AIP. A broker that can obtain neither does not
  accept a network presentation.
- **A failed binding.** A presentation that fails to bind gets the opaque denial of broker profile
  §6.6, before any policy is evaluated. The audit record names the binding and the failure.
- **The bound key.** A CGT or DA the broker mints for a network presenter carries the step 3 key in
  `cnf` (AAP-SPEC §4.6). A later presentation of that token is checked against that key.
- **One presentation, one proof.** The HTTP `created` and `nonce` parameters and the A2A and MCP
  challenges are checked once. Before each downstream operation the broker repeats the checks of
  the ATX validity window, the cached CRL, the grant revocation list and the grant's expiry, but not
  the proof (broker profile §6.13).
- **Which bindings a broker accepts.** The broker's discovery document, published on the
  operator's own domain, lists the presentation bindings it accepts (broker profile §8.5).

## HTTP binding: the `Agent-Trust-Credential` header

The ATX travels in the `Agent-Trust-Credential` request header, which the ATX specification
defines (`atx-spec/core.md` §1.2 and §3.2). The proof is an RFC 9421 HTTP Message Signature that
covers at least `@method`, `@target-uri` and `content-digest`, with a `created` and a `nonce`
parameter.

```http
POST /grants/resolve HTTP/1.1
Host: broker.acme.com
Content-Type: application/json
Content-Digest: sha-256=:<SHA-256 digest of the body, base64>:
Agent-Trust-Credential: <the agent's ATX>
Signature-Input: aap=("@method" "@target-uri" "content-digest");created=<now, Unix seconds>;nonce="<fresh random value>";keyid="<id of the verification key>"
Signature: aap=:<signature over the covered components, base64>:

{"grant": "grant://orders-db"}
```

The path, the host, the body shape and the signature label `aap` are illustrative. The header name
and the minimum set of covered components are fixed by the broker profile.

What the broker reads, in order:

1. **`Agent-Trust-Credential`**: the ATX. Step 2 verifies its signatures and suite, its validity
   window and the cached CRL.
2. **`Signature-Input` and `Signature`**: the step 3 proof. The covered components include
   `@method`, `@target-uri` and `content-digest`; `created` is inside the clock-skew bound;
   `nonce` has not been seen inside that bound; `keyid` names the verification key, and the
   signature verifies under it.
3. **`Content-Digest`**, against the body. The grant reference is in the body, so the digest is
   what puts it under the signature. A grant reference carried in a header instead is named among
   the covered components.
4. **The body**: the grant reference `grant://orders-db`, which step 6 matches against broker
   policy.

## A2A agent card binding: the `atx` field of `/.well-known/agent.json`

The ATX travels inside the agent's A2A agent card, in the `atx` field, which the ATX specification
defines (`atx-spec/core.md` §3.2). The `atp` object of the same card (`ATP-SPEC.md` Section 3.4)
carries the agent's DID and trust proof, not the ATX. The card is public, so the proof is a signed
challenge on the A2A channel. The host, the order of the messages and their shapes are
illustrative.

```text
1. The broker reads the presenting agent's card (illustrative host):

   GET https://agents.acme.com/.well-known/agent.json

   {
     "name": "orders-reader",
     ...other agent card members...
     "atx": ...the ATX, in the form the ATX specification defines...
   }

2. broker ──challenge: fresh random value, at least 16 bytes, bound to this A2A channel──▶ agent
3. agent  ──the challenge signed under its key, and grant://orders-db───────────────────▶ broker
```

What the broker reads, in order:

1. **The card's `atx` field**: the ATX, verified at step 2 as for HTTP.
2. **The signed challenge**: the step 3 proof. The challenge is the one this broker issued on this
   channel and has not been answered before, and the signature verifies under the verification
   key. An agent that copies another agent's ATX into its own card cannot sign for that ATX's key,
   so its presentation fails here.
3. **The grant reference** sent on the channel, which step 6 matches against broker policy.

## MCP manifest binding: the ATX referenced from the server manifest

The manifest does not carry the ATX itself: the MCP server's manifest references it, and the
broker follows the reference. The proof is the same signed challenge as for an A2A agent card,
issued on the MCP channel. The order of the messages and their shapes are illustrative.

```text
1. The broker reads the MCP server's manifest:

   {
     "name": "orders-reader",
     ...other manifest members...
     ...a member that references the ATX; its name and form are not fixed by the broker profile...
   }

2. The broker fetches the ATX the reference points to.
3. broker ──challenge: fresh random value, at least 16 bytes, bound to this MCP channel──▶ server
4. server ──the challenge signed under its key, and grant://orders-db────────────────────▶ broker
```

What the broker reads, in order:

1. **The manifest's reference**, and the ATX it points to, verified at step 2 as for HTTP. The
   reference only says where the ATX is. A reference changed to point at another agent's ATX
   leaves the presenter to sign for a key it does not hold, so the presentation fails at step 3.
2. **The signed challenge**: the step 3 proof, checked as for an A2A agent card.
3. **The grant reference** sent on the channel, which step 6 matches against broker policy.

## What returns to the agent

The binding changes how the ATX arrives, not how the broker resolves the grant. For this request,
which asks the broker to act on `grant://orders-db`, every binding continues after step 3 with the
flow of [`orders-db-exchange.md`](./orders-db-exchange.md): policy evaluation with default-deny,
resolution inside an ephemeral worker, and only the result of the operation returned to the agent.
The same context-hygiene invariant holds: no credential value, no backend identifier and no signal
of the CPI mode reaches the agent context.
