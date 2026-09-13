# Configuring Fluent Forms Pro Webhook Integration

This guide details how Fluent Forms Pro (WordPress) is configured to connect to this webhook processing service in a real production environment.

---

## 1. Prerequisites in WordPress
1. WordPress 6.0+ installed with **Fluent Forms Pro** active.
2. Webhook integration feed enabled under **Fluent Forms > Integrations > Webhook**.

---

## 2. Setting Up the Webhook Feed

1. Navigate to your target form in WordPress:
   - Go to **Fluent Forms > All Forms > [Your Lead Form] > Settings & Integrations**.
2. Click on **Marketing & CRM Integrations** in the left sidebar.
3. Click **Add New Integration** and select **Webhook**.
4. Configure the webhook settings:

| Field | Configuration Value | Notes |
| :--- | :--- | :--- |
| **Name** | `Central Lead Processing Pipeline` | Descriptive label |
| **Request URL** | `https://api.yourdomain.com/api/v1/webhook/fluent-forms` | Target webhook server endpoint |
| **Request Method** | `POST` | Standard HTTP method |
| **Request Format** | `JSON` | Ensures payload is serialized as valid JSON |
| **Request Headers** | `X-Webhook-Secret` : `[Your Secret Token]` | Matches `WEBHOOK_SECRET_KEY` in server `.env` |
| **Request Body** | `All Fields` (or Selected Fields) | Automatically includes form fields and submission metadata |

---

## 3. Recommended Form Field Mapping
When designing the Fluent Forms form fields, use standard field names:

- **First Name:** `first_name`
- **Last Name:** `last_name`
- **Email:** `email`
- **Phone:** `phone`
- **Company Name:** `company`
- **Service Inquiry:** `service_interest`
- **Budget Range:** `estimated_budget`
- **Message:** `message`

### Capturing Hidden Marketing UTM Tags
In Fluent Forms, add **Hidden Fields** to automatically capture URL campaign query parameters:
- `utm_source` $\rightarrow$ Dynamic Default Value: `{get_param.utm_source}`
- `utm_medium` $\rightarrow$ Dynamic Default Value: `{get_param.utm_medium}`
- `utm_campaign` $\rightarrow$ Dynamic Default Value: `{get_param.utm_campaign}`

---

## 4. Testing the Feed in WordPress
1. Submit a test form on your WordPress staging site.
2. Check Fluent Forms **Entries > Activity Logs** to verify the webhook request was delivered with HTTP status `200`.
3. Check the destination channels:
   - SQLite database table `leads`
   - Google Sheet new row
   - Telegram team chat notification
