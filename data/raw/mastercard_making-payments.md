---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/making-payments/
title: Make Payments
retrieved: 2026-07-20
---

# Make Payments

Once cardholders store their cards and the Integrator [tokenizes their PAN details](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/create-tokens/), these tokens (instead of the PAN or Primary Account Numbers) are used for seamless and secure transactions.

**Note**: Once a token is created for the consumer, use that token for all future transactions done by that consumer. Do not re-tokenize every time a transaction occurs or when consumer checks out.

## Cardholder-Initiated Transaction

---

When the cardholder is present while completing the payment, it is called a *cardholder-initiated transaction*. You can facilitate this payment by:

1. Calling the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) and passing the token identifier (`srcDigitalCardId`) associated with that consumer.
2. Retrieving the encrypted payload containing a token and cryptogram and submitting it for payment authorization. Cryptogram acts as a 'one-time' code that is required to validate the cardholder-initiated transactions.

*(Sequence diagram: Integrator calls Checkout (POST /transaction/credentials) — the request and response may contain `assuranceData` for transaction authentication. Mastercard Checkout Solutions returns an encoded checkout JWS response containing a JWE (which contains the cryptogram). The Integrator sends a Payment Authorization Request to the Acquirer or Payment Processor, which returns an Authorization response.)*

Detailed steps are explained below:

**Call the Checkout API request**

1. Use the `srcDigitalCardId` from the [Enroll Card](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) response and call the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) request. Pass the `assuranceData` for transaction authentication in Checkout API request. For integration steps, see the [Integrate with Secure Card on File](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/step7/) tutorial, and for use cases see [Authentication with Passkey](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/token-authentication/secure-card-on-file/by-mastercard/authentication-with-passkey/create-passkey/).
2. Decode the `checkoutResponseJWS` to extract the `encryptedPayload`. Decrypt the `encryptedPayload` to extract the token and cryptogram. The decrypted payload may also contain authentication results in `assuranceData` object. For examples, see the [Integrate with Secure Card on File](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/step7/) tutorial.

**Submit the token details for payment authorization**

3. Submit the token (instead of the PAN), cryptogram and token expiry date (returned in the checkout response) to your acquirer or payment processor for payment authorization.
4. Acquirer or Payment processor sends an authorization response to the Integrator.

**Note**: In case of On-Behalf-Of programs, the merchant can submit the authorization request through an alternative payment gateway, provided the payment gateway and acquirers support [DSRP (Digital Secure Remote Payment)](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis/step8/).

**Warning**:

- The acquirer that will process these transactions must accept DSRP card-on-file tokens and e-commerce Security Level Indicator (SLI) values of **246** for standard payments and **247** for recurring/partial shipment payments. DSRP cryptogram is required to be sent in the DE104 – DPD (Digital Payment Data) field. Please refer to [AN 3363](https://www.mastercardconnect.com/-/sign-in?MCCRedirectTo=https://w204.mastercardconnect.com%2FFIMIDP%2Fsps%2Fauth) for more details.
- If a transaction declines, the Acquirer must request the Token Requester for the latest token and cryptogram for authorization. Retrying the invalid cryptogram more than 10 times may potentially lock the token.

### Managing Cryptograms

---

Cryptograms validate cardholder-initiated transactions, and they must be unique for each transaction request. Note that reusing the cryptogram will result in transaction getting declined as a replayed attempt.

If re-attempting a transaction, submit a new cryptogram with the correct token details from the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout).

**Key Considerations:**

- [PCI SSC](https://www.pcisecuritystandards.org/) has defined Cryptograms as sensitive information and hence Mastercard strongly recommends not to store Cryptograms.
- Tokens and cryptograms are protected under the requirements of PCI DSS, and so storing both items together presents similar risks as storing a cardholder's PAN.
- It is recommended to use the cryptograms generated for a particular token in the order they are obtained.

**Note**: Cryptograms may expire 5 days after they are generated from the Checkout API. See [AN 6302](https://techdocs.mastercard.com/bundle/m_AN6302/page/tqi1649380838881.html) for details.

### Checkout with Enhanced Data

---

Integrators can provide additional, optional data for use by Issuers to further improve transaction performance.

**Digital Transaction Data**

Cardholder data provided in the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) will be available in the subsequent authorization approval request, providing Issuers with increased assurance on cardholder identity.

The following data will be provided to Issuers in the payment authorization message if shared in the checkout request. Not all data are required, individual data can be provided and shared with the issuer:

- `digitalTransactionData.phoneNumber`
- `digitalTransactionData.deviceLocation`
- `digitalTransactionData.emailAddressFormat`
- `digitalTransactionData.emailAddress`
- `digitalTransactionData.ipAddress`
- `shippingAddress.address.line1`
- `shippingAddress.address.countryCode`
- `shippingAddress.address.zip`

**Note**:

- The `transactionAmount` must be >0 in the Checkout API request for the data to be shared to the Issuer.
- To provide Digital Transaction Data to Issuers, client configuration is required. Please contact your Mastercard representative for more information.

**Digital Transaction Insights (DTI) fraud risk score**

Integrators can generate and include a [Mastercard Identity Check](https://developer.mastercard.com/product/identity-check) Digital Transaction Insights fraud score in the authorization approval request by providing additional data in the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) request. This enriches Issuer approval logic and can lead to increased transaction performance.

The following data are required for the DTI score to be generated:

- `dpaData.dpaURI` or `dpaData.dpaData` or `dpaData.PresentationName`
- `dpaData.dpaName`
- `dpaTransactionOptions.transactionAmount.transactionAmount`
- `dpaTransactionOptions.transactionAmount.transactionCurrencyCode`
- `dpaTransactionOptions.merchantCategoryCode`
- `dpaTransactionOptions.threeDsInputData.browser.javascriptEnabled`
- `dpaTransactionOptions.threeDsInputData.browser.javaEnabled`
- `dpaTransactionOptions.threeDsInputData.browser.acceptHeader`
- `dpaTransactionOptions.threeDsInputData.browser.language`
- `dpaTransactionOptions.threeDsInputData.browser.colorDepth`
- `dpaTransactionOptions.threeDsInputData.browser.screenHeight`
- `dpaTransactionOptions.threeDsInputData.browser.screenWidth`
- `dpaTransactionOptions.threeDsInputData.browser.browser.tz`
- `dpaTransactionOptions.threeDsInputData.browser.browser.userAgent`

The following data are optional but will enhance the DTI score if provided:

- `billingAddress.address.line1`
- `billingAddress.address.line2`
- `billingAddress.address.line3`
- `billingAddress.address.zip`
- `billingAddress.address.city`
- `billingAddress.address.state`
- `billingAddress.address.countryCode`
- `shippingAddress.address.line1`
- `shippingAddress.address.line2`
- `shippingAddress.address.line3`
- `shippingAddress.address.zip`
- `shippingAddress.address.city`
- `shippingAddress.address.state`
- `shippingAddress.address.countryCode`
- `dpaTransactionOptions.merchantCountryCode`
- `dpaTransactionOptions.threeDsInputData.acquirer.bin`
- `dpaTransactionOptions.threeDsInputData.acquirer.merchantID`

**Note**: The `transactionAmount` must be >0 in the Checkout API request for data to be shared to the Issuer.

## Merchant-Initiated Transaction

---

Consumers may also store their cards and allow the business to make payments (merchant-initiated transaction) on their behalf. For instance, businesses submit payments for consumers on a recurring basis for subscription-based services.

To facilitate recurring or partial shipment payments, ensure that the original payment is made with a [DSRP (Digital Secure Remote Payment)](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis/step8/) cryptogram. The subsequent recurring or merchant-initiated transaction may be sent without the DSRP cryptogram.

| Recurring/Partial Shipment Payment Series | DSRP Cryptogram | E-commerce Security Level Indicator (SLI) Value |
|---|---|---|
| Original Payment / First Payment of Recurring Series | [Required](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/step8/). Retrieved from the Checkout API | 247 |
| Subsequent Payments | Optional | 247 |
