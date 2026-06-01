# Worked example: `grant://orders-db` via Exchange (RFC 8693)

This walks the canonical v1 resolution end to end: an agent reads the orders database through a
grant reference, and no credential value or backend identifier ever enters the agent context.

## 1. What the agent sees and emits

The agent's code references only the grant. With the AIM developer surface:

```python
from aim_sdk import secure

agent = secure("orders-reader")

@agent.perform_action(capability="orders:read", grant="grant://orders-db")
def recent_orders(customer_id):
    # `db` here is provided by the broker-backed result handle.
    # No connection string, no token, no hostname is ever in scope.
    return db.query("SELECT * FROM orders WHERE customer_id = ? LIMIT 20", customer_id)
```

Everything the model can see is `grant://orders-db` and the returned rows. It cannot tell that the
grant resolves through an OAuth token exchange rather than a vaulted secret or a cloud role.

## 2. What the broker holds (configuration — never on the wire)

```yaml
# broker policy: maps a trust class to a concrete resource + CPI mode.
# Lives on the operator's host. The agent never sees any of this.
- grant: grant://orders-db
  match:
    issuerChainIncludes: { partnersSet: trusted-partners }   # v1: parsed, treated as satisfied in-org
    oasbLevel: ">=L2"                                         # from ATX scanSummary
    trustClass: orders:read                                   # ATX capability
    jurisdiction: { in: [us, eu] }                            # v1: parsed, not enforced
  resolve:
    mode: exchange
    provider: orders-idp        # thin adapter (e.g. Okta) — name lives ONLY here
    scope: orders.read
    audience: https://api.orders.internal
    ttl: 300s
```

## 3. Resolution flow (Section 6 of the spec)

```
agent ──grant://orders-db + ATX──▶ broker (unix socket)
                                   │ 1. verify ATX: sig + suite + expiry + cached CRL  (AIM path)
                                   │ 2. negotiate AAP version
                                   │ 3. evaluate policy → mode=exchange, scope=orders.read  (default-deny)
                                   │ 4. mint broker assertion from ATX claims (subject, orders:read, ttl)
                                   │       signed with broker's rotating delegated key
                                   │ 5. RFC 8693 token exchange ▶ orders-idp
                                   │       grant_type=urn:ietf:params:oauth:grant-type:token-exchange
                                   │       subject_token=<broker assertion>  scope=orders.read
                                   │    ◀ scoped downstream access token (lives only here)
                                   │ 6. ephemeral worker runs the query with the scoped token
                                   │ 7. signed audit: verify + decision + exchange + result
agent ◀──────── rows only ────────┘
```

The scoped downstream token exists only inside the broker's ephemeral worker (step 6). It never
enters the agent process or context. A denial at any step returns the same opaque typed error.

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

This is deliverable 3 in the reference implementation — the artifact that demonstrates the standard.

## Threat-matrix mapping

This flow neutralizes the substrate for AI Agent Threat Matrix techniques
[T-3002](https://threats.opena2a.org/techniques/T-3002) (Environment Variable Exposure),
[T-3003](https://threats.opena2a.org/techniques/T-3003) (Tool Response Credential Capture),
[T-3006](https://threats.opena2a.org/techniques/T-3006) (Context Window Credential Leak), and
[T-8002](https://threats.opena2a.org/techniques/T-8002) (HTTP Callback exfiltration): a compromised
agent can exfiltrate only grant references and results, never a reusable credential.
