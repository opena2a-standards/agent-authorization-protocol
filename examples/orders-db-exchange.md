# Worked example: `grant://orders-db` via Exchange (RFC 8693)

This walks the canonical v1 resolution end to end: an agent reads the orders database through a
grant reference, and no credential value or backend identifier ever enters the agent context.

## 1. What the agent sees and emits

The agent's code references only the grant. With the developer surface of OpenA2A AIM (Agent Identity Management):

```python
from aim_sdk import secure

agent = secure("orders-reader")

@agent.perform_action(capability="acme.com/orders:read", grant="grant://orders-db")
def recent_orders(customer_id, grant):
    # `grant` is the broker-backed handle the SDK passes in. It names a logical
    # operation; no connection string, no token, no hostname is ever in scope.
    return grant.request("GET", "/orders", query={"customer": customer_id})
```

The SDK passes the handle as the `grant` keyword argument when the function declares one, and
`aim_sdk.current_grant()` returns the same handle. Its one method, `request(method, path, query,
body)`, carries a logical HTTP operation to the broker, which resolves it; no query written against
the backend's schema appears in agent code.

Everything the model can see is `grant://orders-db` and the returned rows. It cannot tell that the
grant resolves through an OAuth token exchange rather than a vaulted secret or a cloud role.

## 2. What the broker holds (configuration, never on the wire)

```yaml
# broker policy: maps a trust class to a concrete resource + CPI mode.
# Lives on the operator's host. The agent never sees any of this.
- grant: grant://orders-db
  match:
    issuerChainIncludes: { partnersSet: trusted-partners }   # broker profile §7.1: refused at load by a broker that does not evaluate it
    oasbLevel: ">=L2"                                         # from ATX scanSummary
    trustClass: acme.com/orders:read                          # ATX capability
    jurisdiction: { in: [us, eu] }                            # broker profile §7.1: refused at load by a broker that does not evaluate it
  resolve:
    mode: exchange
    provider: orders-idp        # thin adapter (e.g. Okta), name lives ONLY here (reference loader: providerId)
    scope: orders.read
    audience: https://api.orders.internal
    ttl: 300s                   # reference loader: ttlSeconds: 300
```

**Reference spelling.** The binding above is written in the policy grammar of broker profile §7.1.
At commit `660af0d` the policy loader of the reference implementation accepts `mode`, `providerId`,
`scope`, `audience` and `ttlSeconds` in a `resolve` clause and refuses any other key, so it refuses
the binding as written. It loads the binding once `provider: orders-idp` reads
`providerId: orders-idp` and `ttl: 300s` reads `ttlSeconds: 300`; the `match` clause loads as
written, `issuerChainIncludes` and `jurisdiction` included: at that commit the loader checks the
shape of those two predicates and loads them, and the evaluation of a loaded clause reads neither,
so the clause grants as if both were satisfied, which broker profile §7.1 requires a broker that
does not evaluate them to refuse at load. The keys a given release accepts, and whether it refuses
such a clause, are recorded in the reference implementation's repository, in
`src/broker/grant-policy.ts`.

## 3. Resolution flow (Section 6 of the broker profile)

```
agent ──grant://orders-db + ATX──▶ broker (unix socket)
                                   │ 1. verify ATX: sig + suite + expiry + cached CRL  (AIM path)
                                   │ 2. negotiate AAP version  (conformance Level 2; v1: not performed)
                                   │ 3. evaluate policy → mode=exchange, scope=orders.read  (default-deny)
                                   │ 4. mint broker assertion from ATX claims (subject, acme.com/orders:read, ttl)
                                   │       signed with broker's rotating delegated key
                                   │       (v1: key held in memory, not rotated)
                                   │ 5. RFC 8693 token exchange ▶ orders-idp
                                   │       grant_type=urn:ietf:params:oauth:grant-type:token-exchange
                                   │       subject_token=<broker assertion>  scope=orders.read
                                   │    ◀ scoped downstream access token (lives only here)
                                   │ 6. ephemeral worker runs the query with the scoped token
                                   │ 7. signed audit: verify + decision + exchange + result
                                   │       (v1: audit record written, not signed)
agent ◀──────── rows only ────────┘
```

The scoped downstream token exists only inside the broker's ephemeral worker (step 6). It never
enters the agent process or context. A denial at any step returns the same opaque typed error.

A `v1:` note marks a step the v1 reference implementation does not perform as drawn, in the form
step 7 uses ("v1: audit record written, not signed"). Version negotiation (step 2) is defined in
broker profile Section 8.1 and is a requirement of conformance Level 2 (broker profile Section 13);
the v1 reference targets Level 1. A rotating signing key (step 4) is described in broker profile
Section 11, and a signed audit log (step 7) is required by broker profile Section 6.7. Broker
profile Section 14 lists what the reference implementation provides.

## 4. RFC 8693 request the broker makes (illustrative)

```http
POST /oauth2/v1/token HTTP/1.1
Host: <orders-idp; configured, never exposed>
Content-Type: application/x-www-form-urlencoded

grant_type=urn:ietf:params:oauth:grant-type:token-exchange
&subject_token=<broker assertion derived from verified ATX claims>
&subject_token_type=urn:ietf:params:oauth:token-type:jwt
&scope=orders.read
&audience=https://api.orders.internal
```

The downstream is configured **once** to trust the broker's IdP (static public key on the operator's
domain). OpenA2A is never in this path.

## 5. The invariant the conformance test asserts

After this flow runs, a scan of the agent context / transcript surface MUST find:

- ✅ the grant reference `grant://orders-db`
- ✅ the operation result (order rows)
- ❌ no credential value (no vault secret, no broker assertion, no downstream token)
- ❌ no backend identifier (no hostname, connection string, scope, audience, or provider name)
- ❌ no signal of which CPI mode resolved the grant

This is deliverable 3 in the reference implementation, the artifact that demonstrates the standard.

## Threat-matrix mapping

This flow neutralizes the substrate for AI Agent Threat Matrix techniques
[T-3002](https://threats.opena2a.org/techniques/T-3002) (Environment Variable Leakage),
[T-3003](https://threats.opena2a.org/techniques/T-3003) (Tool Response Credential Capture),
[T-3006](https://threats.opena2a.org/techniques/T-3006) (Context Window Credential Leak), and
[T-8002](https://threats.opena2a.org/techniques/T-8002) (HTTP Callback exfiltration): a compromised
agent can exfiltrate only grant references and results, never a reusable credential.
