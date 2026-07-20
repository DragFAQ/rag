---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-of-existing-card/
title: Tokenization of an Existing Card
retrieved: 2026-07-20
---

# Tokenization of an Existing Card

Tokenize the PANs of already-existing cards stored on your database to ensure that these tokens are used instead of PANs during future checkouts by cardholders.

**Note**: Only one PAN can be tokenized per API request.

When submitting multiple token requests to Mastercard Checkout Solutions, ensure that:

- The speed of tokenization does not exceed the TPS (transaction per second) limit provided by Mastercard.
- You must tokenize PANs by randomizing them by account range (that is, do not consecutively tokenize cards in the same account range). Doing so maximizes tokenization performance by ensuring tokenization requests are balanced across Issuers.

*(Sequence diagram: Integrator processes existing PANs on file by calling Enroll Card (PAN, Expiry Date). Mastercard sends a Tokenization Authorization Request to the Issuer, which responds Approved. Mastercard provisions/creates the token and returns a Card Enrolment Response (CardID, Status: Active) to the Integrator, followed by a Tokenization Complete Notification. The Integrator stores the Secure Card on File token.)*

Detailed steps are explained below:

**Integrator initiates tokenization request**

1. Integrator sends an [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) request with the encrypted PAN details. Use the `srcCorrelationId` to keep track of each unique request.

**Note**: Mastercard recommends that you also populate `cardSource` (with the string `MERCHANT` or `WALLET`) and include additional information in the `decisioningData` object to support the issuer's decision on tokenization.

**Tip**: To maximize tokenization performance:

- Ensure PAN is still active by calling [Mastercard ABU account inquiry](https://developer.mastercard.com/automatic-billing-updater/documentation/api-reference/#rest-api) API before tokenization.
- Work with your Mastercard representative to ensure that your existing card repository has token-eligible cards, which have BIN (Bank Identification Number) ranges enabled for tokenization by Issuers.

**Mastercard sends card to Issuer for tokenization decisioning**

2. Mastercard contacts the issuer to check eligibility for tokenization via Tokenize Authorization Request.
3. The Issuer responds with an approved or declined tokenization decision.
4. Mastercard Checkout Solutions creates a unique token for the PAN.

**Integrator receives tokenization results**

5. On successful tokenization and token provisioning, you will receive the card enrollment response with the `srcDigitalCardId`.
6. Associate the `srcDigitalCardId` to the cardholder's profile.

## Understanding Tokenization Results

---

**Successful Provisioning**

| Result | Response and Details | Action for Integrator |
|---|---|---|
| 200 | Successful | No additional action is needed. |
| 200 with Successful but *requires additional verification* | You will receive a `200` response code. This is indicated with populating the `pendingEvents` object with the pending cardholder verification type, for example — `PENDING_SCA`, `PENDING_AVS` or `PENDING_CONSUMER_IDV`. In this instance, the token is provisioned in an active state, and can be treated as equivalent to an approved tokenization request | No additional action needed. Any further action to perform cardholder verification is optional. |

**Unsuccessful Provisioning**

| Result | Response and Details | Action for Integrator |
|---|---|---|
| 400 | Error with `ISSUER_DECLINE`. The PAN was not approved by the issuer for tokenization. Do not retry tokenization. | If the CVC2 was provided, prompt the cardholder to provide the correct CVC2 value, and do not retry tokenization without sending the CVC2. |
| 400 | Error with `TOKENIZATION_INELIGIBLE` or `PAN_INELIGIBLE`. The PAN will not be tokenized if it is in an account range that has not yet been enabled by the issuer via Mastercard Digital Enablement Service (MDES). | The PAN provided is not yet tokenizable. Retry again in 3-6 months. |
