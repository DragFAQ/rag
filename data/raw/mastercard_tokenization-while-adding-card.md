---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-while-adding-card/
title: Tokenization While Adding a Card
topic: token_creation
retrieved: 2026-07-20
---

# Tokenization While Adding a Card

Cardholder adds a PAN to their merchant website/app and the Integrator creates a token for future transactions.

*(Sequence diagram: Cardholder submits new card details. Integrator calls Enroll Card (PAN, Expiry Date, CVC2). Mastercard sends a Tokenization Authorisation Request to the Issuer, which responds Approved. Mastercard provisions/creates the token and returns a Card Enrolment Response (CardID, Status: Active, authenticationMethods) to the Integrator, which stores the digital card details against the customer profile.)*

Detailed steps are explained below:

**Integrator initiates tokenization request**

1. Cardholder enters new card details and saves credentials on a merchant/commerce platform's website.
2. Integrator encrypts the card object using the public `src-fpan-encryption` key, and Mastercard decrypts the card using the private `src-fpan-encryption` key. Refer to [Public Keys Mastercard Provides](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/key-management/#public-keys-mastercard-provides) for more details on how to obtain these public keys.
3. Integrator sends an [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) request with the encrypted PAN details.
   - Use the `srcCorrelationId` to keep track of each unique request.
   - If collecting the CVC2, then it must be sent in the Enroll Card request. Ensure to use the correct CVC2 to avoid Issuer rejection of the tokenization request.

**Note**: Mastercard recommends that you also populate `cardSource` (with the string `CARDHOLDER`) and include additional information in the `decisioningData` object to support the issuer's decision on tokenization.

**Mastercard sends card to Issuer for tokenization decisioning**

4. Mastercard contacts the issuer to check eligibility for tokenization via Tokenize Authorization Request.
5. The Issuer responds with an approved or declined tokenization decision.
6. Mastercard Checkout Solutions creates a unique token for the PAN.

**Integrator receives tokenization result and provision the token**

7. On successful tokenization and token provisioning, you will receive the card enrollment response with the `srcDigitalCardId`.
8. Associate the `srcDigitalCardId` to the cardholder's profile.

**Note**: [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) response also contains available authentication methods. To use them for transaction authentication, refer to the integration steps in the [Integrate with Secure Card on File](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/step5/) tutorial and review the [Authentication with Passkey](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/token-authentication/secure-card-on-file/by-mastercard/authentication-with-passkey/create-passkey/) use cases.

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
