# SmartPesa Testing Guide

**Purpose:** A practical checklist for the team. This is a plan, not a claim that tests have passed.

## Test environment
- Use a local development database and non-sensitive test users.
- Start PostgreSQL, apply the intended migrations, then start Flask.
- Confirm `GET /api/health` returns HTTP 200 and indicates database connectivity.
- Start React separately; note that current source inspection indicates mock/localStorage data, so frontend/backend integration tests should remain pending until implemented.

## Backend smoke tests

### Health
```bash
curl -i http://127.0.0.1:5000/api/health
```
Expected: HTTP 200 when the service and database are healthy.

### Budget creation
Replace `1` with an existing test user ID:
```bash
curl -i -X POST http://127.0.0.1:5000/api/budgets \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"category":"Food","limit_cents":1500000,"month":"2026-10"}'
```
Expected from source: HTTP 201 on success. Duplicate category/month or conflicting/missing-user conditions may return HTTP 409 in the shown code path.

### List budgets
```bash
curl -i 'http://127.0.0.1:5000/api/budgets?user_id=1&month=2026-10'
```

### Create transaction
Check `TRANSACTION_TYPES` in `server/models.py` and use one of its exact accepted values:
```bash
curl -i -X POST http://127.0.0.1:5000/api/transactions \
  -H 'Content-Type: application/json' \
  -d '{"user_id":1,"description":"Test transaction","amount_cents":25000,"transaction_type":"<VALID_TYPE>"}'
```
Replace `<VALID_TYPE>` before running; do not send the placeholder literally.

### List transactions
```bash
curl -i 'http://127.0.0.1:5000/api/transactions?user_id=1&month=2026-10'
```

## M-Pesa tests
- Set simulation mode only in a local environment using the exact configuration variable expected by the source.
- Test missing user, invalid phone, invalid amount, invalid optional budget and valid simulated STK Push.
- Save the returned checkout ID and query `/api/mpesa/status/<checkout_id>`.
- Test callback payloads: valid, malformed, duplicate and unsuccessful payment result.
- Verify whether successful callback outcomes create/update a persistent transaction.
- Restart the backend and check whether checkout status remains available. Source inspection indicates the `RESULTS` mapping is in memory, so persistence across restart is not assured.
- Never use real customer numbers or live payment credentials for routine development tests.

## Negative tests
- Missing/malformed JSON
- Invalid `user_id`
- Empty or oversized description
- Invalid `amount_cents`
- Invalid month format
- Invalid transaction type
- Nonexistent budget/transaction
- Duplicate budget category/month
- Duplicate M-Pesa code
- Database unavailable
- Daraja unavailable or rejected
- Duplicate callback

## Frontend checks
Currently pending integration:
- Confirm UI builds and lint passes.
- Check whether pages still use mock data/localStorage.
- After API integration, verify requests in browser DevTools Network tab.
- Confirm records created in the UI appear in PostgreSQL and remain after reload/new browser session.
- Confirm API errors are shown clearly to the user.

## Results log
| Test ID | Date | Environment | Expected | Actual | Pass/Fail | Tester |
|---|---|---|---|---|---|---|
| API-001 | | Local | Health 200 | | | |
| BUD-001 | | Local | Budget created | | | |
| TXN-001 | | Local | Transaction created | | | |
| MPE-001 | | Simulation | Checkout created | | | |
| UI-001 | | Local | UI uses API data | Pending integration | Not run | |

## Release gate
Do not mark SmartPesa fully integrated or production-ready until frontend/API/database flow, authentication/authorization, payment callback security, idempotency, error handling and recovery scenarios are tested.
