# SmartPesa API Contract

**Version:** 0.2  
**Status:** Source-inspected draft — endpoint paths, methods and several validations are confirmed from screenshots of the current Flask route files. Request/response examples and runtime behaviour still require execution-based verification.

## 1. Conventions

- Local backend address shown in the project: `http://127.0.0.1:5000`.
- JSON request bodies should use `Content-Type: application/json`.
- Amounts are represented by integer fields ending in `_cents`. The M-Pesa route specifically validates amounts as whole Kenyan shillings represented in cents (multiples of 100).
- Do not include credentials, tokens, passwords, or `.env` contents in this document.
- Authentication/authorization requirements must be confirmed from source and tests before release.

## 2. Confirmed route inventory

| Method | Path | Purpose | Source-inspection status |
|---|---|---|---|
| `GET` | `/api/health` | API/database health check | Confirmed in `server/app.py`; executes `SELECT 1` and returns status/database indicators |
| `POST` | `/api/auth/register` | Register user | Confirmed route decorator in `server/auth.py` |
| `POST` | `/api/auth/login` | Log in | Confirmed route decorator in `server/auth.py` |
| `POST` | `/api/budgets` | Create budget | Confirmed |
| `GET` | `/api/budgets?user_id=<id>` | List budgets; optional `month` query filter | Confirmed |
| `GET` | `/api/budgets/<budget_id>` | Retrieve budget | Confirmed |
| `PUT` | `/api/budgets/<budget_id>` | Update budget | Confirmed |
| `DELETE` | `/api/budgets/<budget_id>` | Delete budget | Confirmed |
| `POST` | `/api/transactions` | Create transaction | Confirmed |
| `GET` | `/api/transactions?user_id=<id>` | List transactions; optional `budget_id` and `month` filters | Confirmed |
| `GET` | `/api/transactions/<transaction_id>` | Retrieve transaction | Confirmed |
| `DELETE` | `/api/transactions/<transaction_id>` | Delete transaction | Confirmed |
| `GET` | `/api/dashboard?user_id=<id>` | Dashboard summary | Confirmed route family and query usage; exact response needs test |
| `GET` | `/api/users/profile?user_id=<id>` | Read user profile | Confirmed |
| `PUT` | `/api/users/profile?user_id=<id>` | Update user profile | Confirmed |
| `POST` | `/api/mpesa/stkpush` | Initiate M-Pesa STK Push | Confirmed |
| `POST` | `/api/mpesa/callback` | Process callback payload | Confirmed |
| `GET` | `/api/mpesa/status/<checkout_id>` | Retrieve in-memory checkout result | Confirmed |

**Important:** These paths are source-inspected. This is not evidence that every route has been successfully tested end-to-end or that the React frontend calls these routes.

## 3. Budget API

### Create budget — `POST /api/budgets`

Confirmed fields from `server/budgets.py`:

| Field | Type | Required | Validation/notes |
|---|---|---|---|
| `user_id` | integer | Yes | Positive integer; user must exist |
| `category` | string | Yes | Trimmed; 1–50 characters |
| `limit_cents` | integer | Yes | Non-negative and no greater than configured `MAX_BUDGET_CENTS` |
| `month` | string | Yes | `YYYY-MM`, e.g. `2026-10` |

Illustrative request:
```json
{
  "user_id": 1,
  "category": "Food",
  "limit_cents": 1500000,
  "month": "2026-10"
}
```
Here `1500000` represents the stored integer amount in the application's cents-based convention. Confirm display conversion in the UI before presenting it as a user-facing KSh value.

The source returns HTTP `201` for successful creation and handles a duplicate category/month or missing user conflict with HTTP `409` in the shown code path.

### List budgets — `GET /api/budgets?user_id=1&month=2026-10`

- `user_id` is required and must be positive.
- `month` is optional; if supplied, it must use `YYYY-MM`.
- Response key shown in source: `budgets`, containing serialized budget records.

### Single-budget operations

- `GET /api/budgets/<budget_id>` returns a serialized `budget` object or a not-found error.
- `PUT /api/budgets/<budget_id>` requires at least one valid field to update and returns the updated `budget`.
- `DELETE /api/budgets/<budget_id>` deletes the record if found.
- Exact error payloads and all response codes should be confirmed with tests.

## 4. Transaction API

### Create transaction — `POST /api/transactions`

Fields observed in `server/transactions.py`:

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_id` | integer | Yes | Positive; user must exist |
| `description` | string | Yes | 1–200 characters |
| `amount_cents` | integer | Yes | Positive, within configured maximum |
| `transaction_type` | string | Yes in practice/defaulted to `other` in source | Must belong to `TRANSACTION_TYPES` |
| `budget_id` | integer/null | No | If supplied, must belong to the same user |
| `mpesa_code` | string/null | No | Maximum 20 characters |
| `occurred_at` | ISO datetime/date string | No | Invalid values return a validation error |

Illustrative request:
```json
{
  "user_id": 1,
  "description": "Groceries",
  "amount_cents": 25000,
  "transaction_type": "expense"
}
```
Confirm the accepted `TRANSACTION_TYPES` from `server/models.py` before relying on `"expense"` as an example value.

The source returns HTTP `201` for successful creation and handles a duplicate M-Pesa code conflict with HTTP `409`.

### List transactions — `GET /api/transactions?user_id=1&month=2026-10`

- `user_id` is required.
- Optional filters: `budget_id` and `month`.
- Results are ordered by occurrence time, newest first.
- Response key shown in source: `transactions`.

Single-transaction routes:
- `GET /api/transactions/<transaction_id>`
- `DELETE /api/transactions/<transaction_id>`

## 5. Authentication and user profile

Confirmed route decorators:
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/users/profile`
- `PUT /api/users/profile`

The profile routes read `user_id` from query parameters. Document exact registration/login fields, password handling, authentication model and access-control behaviour only after reviewing the full source and tests.

## 6. Dashboard

`GET /api/dashboard` uses a `user_id` query parameter and accepts/derives a `month` value in `YYYY-MM` format. Source references totals such as budget limit and spent amount. Confirm exact response schema and calculations through tests before documenting frontend expectations.

## 7. M-Pesa API

### Initiate STK Push — `POST /api/mpesa/stkpush`

Fields observed in source:
- `user_id` (required positive integer)
- `amount_cents` (required; at least 100, no greater than configured maximum, and a multiple of 100)
- `phone` (optional if a stored user phone can be used; must normalize to a valid Kenyan number)
- `description` (optional with a default description; maximum 200 characters)
- `budget_id` (optional; if supplied, must belong to the same user)

The source contains:
- a simulation branch when `MPESA_MODE` is `simulate`, generating a checkout ID and processing a simulated successful callback;
- a Daraja branch that attempts to call `send_stk_push`;
- a pending response for accepted Daraja requests (HTTP `202`);
- provider-unavailable/rejected error paths.

Do not describe the integration as production-ready based only on this source inspection. Live/sandbox credentials, callback reachability, idempotency and transaction persistence still require verification.

### Callback — `POST /api/mpesa/callback`

The route reads a JSON payload, calls `process_callback(payload)` when the payload is a dictionary, and returns an acknowledgement with `ResultCode: 0` and `ResultDesc: "Accepted"` in the shown code. Verify signature/secret validation, duplicate callback handling, persistence and failure handling before production.

### Status — `GET /api/mpesa/status/<checkout_id>`

Looks up a checkout result in the in-memory `RESULTS` mapping. A checkout ID absent from that mapping returns a not-found error. This means status lookup may not survive a server restart unless another persistence mechanism exists.

## 8. Error handling and verification checklist

Test and record actual outcomes for:
- malformed JSON, missing fields, invalid types;
- invalid month/category/amount/transaction type;
- nonexistent user, budget or transaction;
- duplicate budget category/month and duplicate M-Pesa code;
- database failure;
- Daraja timeout/rejection;
- invalid, repeated, delayed and out-of-order callbacks;
- checkout status after process restart;
- access control and user ownership on all user-specific routes.

## 9. Frontend integration status

Source inspection of the React project found:
- `src/App.jsx` imports `initialTransactions` and `initialBudgets` from `./data/mockData`;
- `src/App.jsx` reads/writes browser `localStorage`;
- the search for `fetch`, Axios and local backend URLs did not find an API call in the searched `src` tree.

Therefore, the current frontend appears to use mock/local browser data. **Frontend-to-backend integration is not yet verified and should be documented as pending**, not as complete.

## 10. Sign-off

Backend reviewers (Members 1–2): __________________  
Frontend reviewers (Members 3–4): __________________  
Integration/documentation coordinator (Member 5): __________________  
Version/date: __________________
