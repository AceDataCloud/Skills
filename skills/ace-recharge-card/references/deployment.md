# Seller-owned Ace recharge-card tool

This opt-in tool belongs beside the **existing seller's Hermes Agent**. It does
not change Hermes, the generic hosting chart, Envar's runtime model, or any other
tenant. Hermes loads the skill and calls its no-argument delivery script. The
separate tool validates the active original Envar Work, exact immutable revision,
seller/service, $1 USD capture, and original order before allocating inventory.
It submits the key and instructions to Envar's buyer-only encrypted order
delivery. Work history, events, Connector journals and Hermes receive only a
nonsecret receipt.

## State and recovery

A private SQLite database on a dedicated PVC stores inventory and a durable
outbox. Neither the PVC nor the scoped Envar credential is mounted into Hermes.
Unique order/work constraints and an immediate transaction allocate at most one
card per original order. Import replays check exact identity; separate purchases
consume separate unused cards. Expired cards are excluded. The deterministic
report event and original delivery text survive restart. A timed-out report is
read back and retried against the original Work; a conflicting terminal result
is kept for operator resolution and the allocated card is never resold.

Publication probes verify the native tool path and available stock without
issuing a real key. Free chat, buyer-supplied IDs, other services, wrong amounts,
unconfirmed payments and canceled work cannot allocate inventory. Out of stock
reports a failed original Work; it does not fabricate a key or create another
payment. Refunds use the existing Envar order-review process.

## Deployment

1. Merge/deploy Envar support for receiver claim readback and the buyer-only
   `agent-commerce/orders/{id}/private-delivery` API. Obtain a dedicated
   credential on the existing seller connection with `work:read`, `work:receive`
   and `work:report` only. It has no account-funding or buyer-spending permission.
2. Save config with `envar_origin`, `agent_id`, `service_id`, `revision_id`,
   `digest`, `credits` and `amount` (`"1000000"` for $1). The card denomination
   must equal the actual issued Credits value. Neither config nor prompts
   contain keys. Keep `envar-token` and a random `tool-token` in the named Secret.
3. Run `operator/render.py` with the config, namespace, unique name, exact receiver pod
   label and a verified digest-pinned Python image. Inspect then apply the
   rendered PVC, ConfigMap, Deployment, internal Service and NetworkPolicy.
   If the receiver already has an egress NetworkPolicy that excludes private
   addresses, add `--allow-client-egress`. It adds only a TCP 8031 route from
   that receiver to this tool, preserving the existing policy's other allows.
   Do not use the flag on an unrestricted receiver: a new Egress policy would
   otherwise isolate its other outbound traffic. Verify the receiver label
   selects only the intended seller instance before applying.
   Pass `--pull-secret` with the namespace's existing registry Secret name. The separate inventory volume is never shared with
   the Agent, and the pod has no Kubernetes service-account token.
4. Issue the authorized card batch using the PlatformBackend issuer. Preserve
   its one-time CSV privately. Convert to JSON records (`id`, `code`, `credits`,
   `expires_at`) and pipe over stdin into `broker.py --import-cards` in the tool
   pod. Never print keys, commit inventory, or pass them in shell arguments.
5. Install this skill folder into this seller's native Hermes skill directory. Its private
   `scripts/client.json` contains only the internal tool URL and the narrow `tool-token`.
   Set file permissions to 0600. Set the service instructions to load this
   skill and run its delivery script with no arguments, then test and publish
   the immutable revision through Envar's normal workflow.
6. Before loading real keys, verify `/health` from the receiver returns
   `delivery_protocol: buyer_only_order_v1`. This confirms the running process
   uses the private-delivery version, including after a ConfigMap update.
   Verify two distinct paid orders, a repeated original order, original-report
   recovery, buyer-only visibility and a real Ace redemption. Operator test
   wallet funding is not PSP payment evidence. Track credential expiry and
   remaining stock in the operator run record; replenish or unpublish before
   stock runs out. Renew the scoped credential before its existing 30-day expiry.

A stopped tool or expired credential fails closed. To withdraw, unpublish the
service, resolve active original orders, then scale this tool to zero. Preserve
its PVC and one-time issuance records. This tool cannot mint cards, refund,
fund wallets, edit prices, publish services, or change buyer identity.

Run `python3 -m unittest discover -s skills/ace-recharge-card/tests -v`.
