---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/displaying-tokenized-pan-details/
title: Display Tokenized PAN Details
topic: token_display
retrieved: 2026-07-20
---

# Display Tokenized PAN Details

Cardholders may view, use, or manage their cards during the profile management or checkout experience.

Integrators can also choose to provide a visual representation of their cards (that is, by using card art) that allows consumers to easily recognize and select a specific card – enhancing the overall checkout experience and improving the conversion rates.

Use the [GET Card API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#card) endpoint to fetch the most updated card details for a specific PAN in the following scenarios:

- Creating a screen for cardholders to manage cards associated with their profile.
- Providing an option for cardholders to select between cards before making a payment.

## Key Considerations

---

- If you maintain a local version of the token (`srcDigitalCardId`), keep it updated using the GET Card API and by listening to the [Card Notifications](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#notifications).
- If you decide to display card art, utilize the `artUri` found in the [maskedCard.digitalCardData](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/sdk-reference/common-objects/#masked-card) object. Any future updates to card art will always result in a newly-issued `artUri`.
- Display the consumer's card details on your UI according to the [Mastercard Brand guidelines](https://brand.mastercard.com/brandcenter/mastercard-brand-mark.html).

## Token Status and Card Details

---

**Guidelines for displaying card details:**

| Token Status | Description | UI Recommendation | Authorization |
|---|---|---|---|
| **SUSPENDED** | Token is suspended and unable to transact. | Show grayed card without `panLastFour`. | Token cannot be used (nor should be attempted) for payment authorization. |
| **ACTIVE** | Token has been unsuspended/reactivated and can be used for transactions. | Show card with `panLastFour`. | Token can be used for payment authorization. |
| **CANCELLED** | Token has been permanently cancelled. | Do not show card or `panLastFour`. | Token cannot be used (nor should be attempted) for payment authorization. |

**Tip**: To minimize network congestion, keep a local copy of the token and keep it updated by [listening to the Card Notifications](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/managing-tokens/), instead of retrieving the token details by making repeated GET Card API requests.

*(Sequence diagram: Integrator calls Get Card (GET /cards/{cardId}) with srcClientId, srcDigitalCardId, and tokenRequested=false. Mastercard Checkout Solutions looks up the cardId and returns masked card info. If tokenRequested=true, Mastercard additionally looks up the cardId, retrieves the encrypted token detail data, and returns a Token Data Response containing card metadata with encrypted token details.)*
