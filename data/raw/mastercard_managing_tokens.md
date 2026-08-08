---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/managing-tokens/
title: Manage Tokens
topic: token_management
retrieved: 2026-07-20
---

# Manage Tokens

Manage the tokens generated in the following different scenarios:

| Scenario | Details |
|---|---|
| [Receive Token Updates](#receive-token-updates) | Receive and respond to the notifications when the status of the token changes to Cancelled, Suspended or Active. |
| [Delete a Token](#delete-a-token) | Delete the token associated with the PAN (Primary Account Number) by calling Delete Card API when consumer deletes a card. |
| [Get Transaction List for a Token](#get-transaction-list-for-a-token) | Retrieve recent transactions for the specified card identifier using an API. |

## Receive Token Updates

---

**Lifecycle management events** are events that can take place throughout the card's lifecycle, such as an expiring PAN, or when a card is lost, stolen or compromised by an imposter. When such events occur, Issuers may update the card.

**Events that trigger Issuer account updates**

An Issuer may initiate an account update within the account range or across another account range due to:

- PAN replacement within the same account range
- PAN replacement in a different account range
- Routine Issuer maintenance, such as moving from a 6 to 8-digit BIN (Bank Identification Number), which may result in the token number being updated (even if underlying PAN does not change)
- Token expiry extension

As these events can affect the token, the Integrator must keep tokens updated by receiving and responding to Card Notifications sent by Mastercard. Mastercard can deliver outbound notifications to customers in either fully encrypted or unencrypted formats (If you are seeking fully encrypted Card Notifications, speak to your account manager to initiate this request).

To keep tokens updated, build an endpoint capable of receiving token lifecycle updates from the request URI associated with [Card Notification](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#notifications).

**Note**: Failure to listen and respond to timely notifications may result in outdated tokens. If these outdated tokens are used in payment authorization, it may impact approval rates.

Support the following updates and take the necessary action for each status:

| Token Status | Description | Action required | Authorization |
|---|---|---|---|
| **SUSPENDED** | Token is suspended and unable to transact. | Show grayed card without `panLastFour` on the UI. Update the stored token's status to SUSPENDED. | Token cannot be used (nor should be attempted) for payment authorization. |
| **ACTIVE** | Token has been unsuspended and is active to use for transactions. | Show Card with `panLastFour` on the UI. Update the stored token's status to ACTIVE and save the token details in the [maskedCard](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/sdk-reference/common-objects/#masked-card) object. | Token can be used for payment authorization. |
| **CANCELLED** | Token has been permanently cancelled. | Do not show the card on the UI. Delete the card from your database. Update the stored token's status to CANCELLED, and archive all information related to this token. | Token cannot be used (nor should be attempted) for payment authorization. |

Whenever Mastercard sends a card notification, it means that the underlying PAN, token, and/or digital data have changed. The `reasonCode` provided in the notification is directional, and can guide the Integrator to take the required action.

### Reason Code Updates

---

| Reason Code | Description | Action required from Integrator |
|---|---|---|
| **TOKEN_REFRESH** | The token and/or token expiry may have changed. | When you receive a TOKEN_REFRESH notification, use your payload encryption keys stored on Mastercard Connect to decrypt the `paymentData` object and update the stored token record. Use the decrypted DPAN and expiry values to refresh the corresponding [maskedCard](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/sdk-reference/common-objects/#masked-card) details—this includes updating PAN last four, PAN expiry, token last four, and token expiry.<br><br>If both token number and expiry change, call the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) (**Checkout POST /transaction/credentials**) to obtain a new cryptogram before the next transaction. If only expiry changes, calling the Checkout API is optional.<br><br>For TOKEN_REFRESH, you will receive both `maskedCard` and encrypted `paymentData` (containing DPAN and DPAN expiry). For events other than TOKEN_REFRESH, you will only receive `maskedCard`. |
| **Other reason codes** | Any reason code other than TOKEN_REFRESH | Update the [maskedCard](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/sdk-reference/common-objects/#masked-card) object for the associated token with the new status and other parameters that may have changed. |

**Warning**: Failure to fetch the new token and other token related information after receiving a **TOKEN_REFRESH** notification may cause future transactions to fail. It is important to call the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) to retrieve the latest token information before attempting to perform another transaction.

In the case of a Merchant Initiated Transaction (MIT), if the token number has changed, you should restart the series with Security Level Indicator (SLI) value to 247 and establish domain control with a Digital Secure Remote Payment (DSRP) cryptogram.

**Example of a successful token update scenario**

*(Sequence diagram: Issuer sends a PAN update to Mastercard Checkout Solutions, which updates the token mapping and notifies the Integrator; the Integrator responds HTTPS 200 (OK) and updates its card/token info; if the token number changed, the Integrator calls the Checkout API to fetch a new cryptogram.)*

Steps in detail:

1. **Issuer sends a PAN update.**
   Issuer sends a PAN update to Mastercard Checkout Solutions, who updates the token mapping.

2. **Mastercard sends a Card Notification to the Integrator.**
   Integrator receives the [Card Notification](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#notifications) and sends an acknowledgement response to Mastercard Checkout Solutions.

3. **Integrator updates the card/token info.**
   - **Update token details using `paymentData` (for TOKEN_REFRESH only):** When the notification reason is TOKEN_REFRESH, use your payload encryption keys stored on Mastercard Connect to decrypt the `paymentData` object and update the stored token record. Use the decrypted DPAN and expiry values to refresh the token details—this includes token number (`paymentToken`), token expiry (`tokenExpirationMonth`, `tokenExpirationYear`), and any other changed parameters.
   - **Update `maskedCard` details:** Update the corresponding [maskedCard](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/sdk-reference/common-objects/#masked-card) object using the new DPAN last four, PAN expiry, token last four, token expiry, and any other updated fields.
     - For TOKEN_REFRESH, both `maskedCard` and encrypted `paymentData` are provided.
     - For all other notification reasons, only `maskedCard` is provided and should be updated accordingly.
   - **Request a new cryptogram when needed:** If the `reasonCode` is TOKEN_REFRESH **and** both the token number and token expiry have changed:
     1. Delete the old cryptogram.
     2. Call the [Checkout API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#checkout) (Checkout POST /transaction/credentials) to obtain a new cryptogram (`dynamicData`) before the next transaction. If **only the token expiry changed**, calling the Checkout API is optional.

For more information about retry policy if a card notification request fails, see [Retry Policy for Notifications](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/code-and-formats/#retry-policy-for-notifications).

## Delete a Token

---

Call the [Delete Card API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) for the deleted token (`srcDigitalCardId`) anytime a token is removed from your database under the following scenarios:

- Cardholder deletes a card from their profile or by contacting a call center.
- Cardholder deletes a card during the transaction.
- Service Provider off-boards or removes a Merchant account and the associated tokens.

**Note**:

- Ensure to evaluate all channels in which a card is removed – for instance, through profile management, during a transaction, a call center, and/or when a Service Provider removes a merchant account. The Delete API must be called for all such touch-points (or any other incidents not listed here), to inform Mastercard that the token was deleted.
- If the Delete API is not called to delete a token from your database, the token will remain active and available to transact in Mastercard's system.

**Example of a successful deleted card scenario**

*(Sequence diagram: Cardholder deletes a saved card on file; the Integrator calls Delete Token; Mastercard Checkout Solutions sends a Tokenization Event Notification (deactivate) to the Issuer, which responds; Mastercard deactivates the token mapping and confirms Delete OK to the Integrator; the saved card is removed for the Cardholder.)*

Steps in detail:

1. **Cardholder deletes a saved card stored on file.**
   1. Integrator calls the [Delete Card API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) request containing the `srcdigitalcardId` for the card the consumer has chosen to delete.
   2. Mastercard Checkout Services sends the Issuer a Tokenization Event Notification request to deactivate the card.
   3. Issuer sends deactivate response to Mastercard Checkout Services.

2. **Mastercard deactivates token mapping.**
   Mastercard Checkout Services deactivates token mapping and responds back to Integrator to delete card.

3. **Integrator updates card status.**
   1. If the request is successful, Integrator archives the token-related information based on the internal policies and update the token status stored in system as CANCELLED.
   2. Integrator updates the cardholder that the saved card is removed.

**Tip**: Mastercard recommends that you delete the token, token information and cryptograms related to the deleted card. Based on your own internal policies and any regulatory requirements, you can delete all archived information about this token when a certain amount of time has passed, such as two years.

## Get Transaction List for a Token

---

To retrieve recent transactions for the specified card identifier, use the [Get transactions by Card Id API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card).

If Issuer of the card does not support the Transaction Detail Service, the above request will return an error.

**Note**: This scenario is valid for Commerce Platform program type only.