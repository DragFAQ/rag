---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/tokenization-while-transacting/
title: Tokenization while Transacting
topic: token_creation
retrieved: 2026-07-20
---

# Tokenization while Transacting

Cardholders can initiate payment with a card that is not yet tokenized. In this case, create a token by enrolling a PAN into Secure Card on File during the transaction, and associate the token with the cardholder's profile for future transactions.

*(Sequence diagram: Cardholder initiates checkout. Integrator calls Enroll Card (PAN, Expiry Date, CVC2). Mastercard sends a Tokenization Authorisation Request to the Issuer, which responds Approved. Mastercard provisions/creates the token and returns a Card Enrollment Response (CardID, Status: Active, authenticationMethods) to the Integrator, which stores the digital card details against the customer profile. The Integrator then calls Checkout (POST /transaction/credentials) and receives a checkout JWS response containing the encryptedPayload.)*

Detailed steps are explained below:

**Integrator initiates tokenization request**

1. Cardholder initiates a transaction on an existing card stored on file or by adding a new card on a merchant/commerce platform's website.
2. Integrator encrypts the card object using the public `src-fpan-encryption` key, and Mastercard decrypts the card using the private `src-fpan-encryption` key. Refer to [Public Keys Mastercard Provides](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/key-management/#public-keys-mastercard-provides) for more details on how to obtain these public keys.
3. Integrator sends an [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) request with the encrypted PAN details.
   - Use the `srcCorrelationId` to keep track of each unique request.
   - If collecting the CVC2, then it must be sent in the Enroll Card request. Ensure to use the correct CVC2 to avoid Issuer rejection of the tokenization request.

**Note**: Mastercard recommends that you also populate `cardSource` (with the string `CARDHOLDER`) and include additional information in the `decisioningData` object to support the issuer's decision on tokenization.

**Mastercard sends card to Issuer for tokenization decisioning**

4. Mastercard contacts the issuer to check tokenization eligibility via Tokenize Authorization Request.
5. The Issuer responds with an approved or declined tokenization decision.
6. Mastercard Checkout Solutions creates a unique token for the Account PAN.

**Integrator receives tokenization results**

7. On successful tokenization and token provisioning, you will receive the card enrollment response with the `srcDigitalCardId`.
8. Associate the `srcDigitalCardId` to the cardholder's profile.

**Note**: [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) response also contains available authentication methods. To use them for transaction authentication, refer to the integration steps in the [Integrate with Secure Card on File](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/step5/) tutorial and review the [Authentication with Passkey](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/token-authentication/secure-card-on-file/by-mastercard/authentication-with-passkey/create-passkey/) use cases.

**Make payments with the token**

9. Call the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) with the `srcDigitalCardId` to fetch the payload.
10. The response is encoded, digitally signed and wrapped in a JWS structure, which needs to be decoded to extract the `encryptedPayload`. Decrypt the `encryptedPayload` to send payload for authorization for the cardholder to complete the purchase.

**Note**: While making back-to-back API calls (that is, calling Enroll API to create the token, then calling Checkout API to make a payment), ensure to use the same `X-Src-Cx-Flow-Id` returned from the first API call to call the next API call, to avoid site replication errors.

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
| Other 400 Errors | Do not retry tokenization with the same request. | Work with your Mastercard representative to understand the potential issue. |
| 5xx Errors | Indicates a server outage. | Retry immediately or after some time. |
