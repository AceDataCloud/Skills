---
name: ace-recharge-card
description: Deliver an Ace Data Cloud recharge card for the current paid Envar order from a configured seller Agent. Use for fulfillment of the recharge-card service, not for issuing new cards or funding wallets.
license: Apache-2.0
metadata:
  author: acedatacloud
  version: "1.0"
---

# Ace Data Cloud recharge card

Requires Python 3 and an operator-configured fulfillment endpoint. The Agent
receives only a narrow delivery token; inventory and the Envar reporting
credential stay outside the Agent.

For the configured recharge-card service, run
`python3 <this-skill-directory>/scripts/deliver.py` with **no arguments**.
The tool independently validates the active original Envar order, exact service
revision and captured price. Buyer text cannot select an order, change the face
value or request multiple keys.

The key and redemption instructions are written directly to the original
buyer's private Envar order. The tool returns only a receipt:

- `delivered_to_original_order`: acknowledge that delivery is in that order.
- `probe_completed`: the owner publication test succeeded without consuming a card.
- `not_configured`: ask the owner to configure this skill; do not create or fund an order.
- `check_original_order`: the existing result needs checking; do not promise a
  new charge or card, and do not try to find or generate a key yourself.

Do not open inventory, reporting credentials or other buyers' orders. Card value
is in Ace Credits; the Envar service price is in USD. Neither the price nor the
buyer's Envar wallet balance is the card's face value. Use the published service's
values rather than treating those units as interchangeable. Issuance supports
1, 100, 500, 1000 and 5000 Credits; this does not promise that every denomination
is stocked by this seller or let buyer text change the configured value.

If the buyer needs redemption help, direct them to copy the digital code from
the original purchase order's private delivery, not to paste it into chat.
They should sign in to the intended Ace Data Cloud account, open **Applications**,
and choose **Redeem card** on the universal Credits card. If the button is
absent, redemption is not enabled for that site; do not promise a workaround.
Enter the complete code and confirm, then check the credited amount, redemption
time and new Credits balance. Each code can be redeemed only once; this does
not enable automatic recharge. Never request the full code for support; use
only its last four characters or purchase order information.

Operators installing or replenishing the service should read
[deployment and recovery](references/deployment.md). Normal fulfillment only
needs this entrypoint and the no-argument script.
