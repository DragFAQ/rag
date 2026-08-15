---
source: https://developer.mastercard.com/mastercard-checkout-solutions/documentation/use-cases/card-on-file/register_entities/
title: Register Entities to Create Tokens
topic: entity_registration
retrieved: 2026-07-20
---

# Register Entities to Create Tokens

Before registering your entities, visit [Mastercard Connect](https://www.mastercardconnect.com/-/sign-in) to onboard, create a project, and get access to Secure Card on File APIs. For further details, view the [Integrate with Secure Card on File](https://developer.mastercard.com/mastercard-checkout-solutions/tutorial/integrate_apis_scof/) tutorial.

Consumers save their card with a business (or a consumer-facing entity) and tokens are created for that card and entity combination.

Each consumer-facing entity must be registered with Secure Card on File by providing the entity name in the `programName` field.

## Program Name

---

The `programName` is shared with the Issuer in the tokenization request. To optimize tokenization approval rates, ensure that the program name is clear, descriptive, and represents the business the cardholder recognizes, avoiding numeric or special characters unless they are part of the name.

If a parent brand owns multiple entities (that is, websites/applications/products), consider the cardholder's experience while storing their card and registering:

- Question: If the cardholder saves their card with one business, would they expect it to appear in another business? Does the cardholder have the same profile, username, and password across different businesses?
  - If yes, consider registering a parent entity under one `programName`
  - If no, consider registering entities separately under different program names.

## ServiceId Creation

---

Using the `programName`, Mastercard creates a `serviceId`, which is a unique identifier for that entity. The Integrator uses this `serviceId` to create tokens for that entity.

Program Types are Mastercard-defined business categories assigned to you during onboarding. Your Program Type determines how your `serviceId` and `srcClientId` are assigned:

| Program Type | Who Integrates (`src-Client-Id` assigned to) | Who has relationship with Mastercard | Who has relationship with Cardholder | `serviceId` assigned to |
|---|---|---|---|---|
| **Merchant Direct** | Merchant | Merchant | Merchant | Merchant / Consumer-facing entities |
| **Commerce Platform Direct** | Commerce Platform | Commerce Platform | Commerce Platform | Commerce Platform |
| **On-Behalf-Of Merchant** | Service Provider | Service Provider | Merchant | Each merchant / Consumer-facing entities under PSP |
| **On-Behalf-Of Commerce Platform** | Service Provider | Commerce Platform | Commerce Platform | Commerce Platform (supported through Digital Activity Service Provider model) |
| **On-Behalf-Of Sub-Merchant** | Payment Facilitator | Payment Facilitator | Sponsored Merchant | Each group of sponsored merchants |

**Note**: Payment Facilitators can group their sponsored merchants under common attributes and each group is assigned a `serviceId`. The token, provisioned under the serviceId, can be shared provided that adequate PAN checks are in-place. Up to 5 shared serviceIds can be created.

**The Digital Activity Service Provider model**

Secure Card on File is also available to Digital Activity Customers or Service Providers, who may want to employ a third party (that is, Technical Enabler) for their tokenization activities. To do so, the Technical Enabler must be registered as a "Digital Activity Service Provider."

If you are a Technical Enabler, you and your customer will have a relationship with Mastercard and the `serviceId` will be assigned based your customer's Program Type.

**Note**: The Technical Enabler operates on behalf of and at the direction of their customer, and their customer is responsible for the acts and omissions of the Service Provider.

Please reach out to your Mastercard representative for more details on how this model suits your requirements.

## Using Merchant Registration APIs to Register your Entities

---

When registering an entity, submit a **POST** request to the [Merchant Registration API](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#registration) with the `programName`.
Payment Facilitators should register each of their sponsored merchants as separate Digital Payment Applications (`srcDpaId`) underneath a `programName`.

Retrieve the `serviceId` for that entity by making a **GET** request to the Merchant Registration API using the `batchId` returned in the previous request.

Alternatively, you can retrieve the `serviceId` by receiving [Merchant status notifications](https://developer.mastercard.com/mastercard-checkout-solutions/documentation/api-reference/apis/#notifications).