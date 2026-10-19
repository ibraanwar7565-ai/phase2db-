# SmartPesa — Full Project Report

**Project:** SmartPesa  
**Phase:** Phase 2  
**Prepared by:** Member 5 — Integration, Documentation and Coordination  
**Report status:** Draft based on the project context and source screenshots supplied during review  
**Date:** 19 October 2026

## 1. Executive summary
SmartPesa is a personal-finance application project intended to help users manage budgets and transactions and initiate M-Pesa payments. The observed implementation includes a React/Vite frontend and a Flask backend with SQLAlchemy/PostgreSQL-related configuration and route modules. The backend source includes budget and transaction CRUD operations, authentication routes, a dashboard endpoint, user-profile routes and M-Pesa STK Push/callback/status routes.

A key implementation distinction is that the current React source appears to use mock initial data and browser `localStorage`. The search shown during review did not find `fetch`, Axios or local API URL calls in the frontend source. Consequently, frontend-to-backend integration is **not verified and should be treated as pending**. The backend route code is source-inspected, but not every route or payment scenario has been execution-tested in this report.

## 2. Problem statement
Users need a convenient way to record and review personal spending, set monthly category budgets, monitor usage and initiate mobile-money payments. A useful application should maintain consistent records, validate input, provide meaningful feedback and avoid treating simulated payments as real payment confirmations.

## 3. Project objectives
- Provide user registration/login workflows.
- Create, list, update and delete budgets.
- Create, list and retrieve transactions, and delete transactions.
- Provide a dashboard summary for a selected user/month.
- Support an M-Pesa STK Push workflow, including a simulation mode for development.
- Store financial records in a database through the backend.
- Deliver clear documentation, API expectations and a repeatable test plan.

These are project objectives and observed route capabilities; they should not be interpreted as proof that all workflows are integrated or production-ready.

## 4. Technology stack observed
| Layer | Technology / evidence |
|---|---|
| Frontend | React, React Router DOM, Vite |
| Backend | Python, Flask, route Blueprints |
| Data access | SQLAlchemy-related models/extensions |
| Database | PostgreSQL referenced in project setup and health check |
| Migrations | Flask-Migrate-style commands and `server/migrations/` directory referenced |
| Payment | Safaricom Daraja STK Push code path plus simulation branch |
| Frontend state | React state, `localStorage`, initial mock data |
| Version control | Git/GitHub workflow is part of team process |

## 5. Architecture and data flow
**Intended flow:** React UI → Flask JSON API → SQLAlchemy/database; M-Pesa STK Push requests flow from Flask to the Daraja provider, and provider callback results return to the Flask callback route.

**Observed current frontend flow:** React pages use shared application state, seed initial state from `src/data/mockData.js`, and persist selected state in browser `localStorage`. The searched source did not show API requests. Therefore the intended backend/database flow should be documented as an integration target until confirmed in the browser and database.

## 6. Backend capabilities observed in source
### Health
`GET /api/health` executes `SELECT 1` and returns a JSON response indicating API/database health.

### Authentication
The source has `POST /api/auth/register` and `POST /api/auth/login`. Exact request fields, password-handling details and authorization behaviour require full source/test review.

### Budgets
Routes observed:
- `POST /api/budgets`
- `GET /api/budgets`
- `GET /api/budgets/<budget_id>`
- `PUT /api/budgets/<budget_id>`
- `DELETE /api/budgets/<budget_id>`

Creation fields include `user_id`, `category`, `limit_cents`, and `month`. Month is validated in `YYYY-MM` format; category is 1–50 characters. The code handles conflicts such as duplicate category/month. Amount values use integer fields.

### Transactions
Routes observed:
- `POST /api/transactions`
- `GET /api/transactions`
- `GET /api/transactions/<transaction_id>`
- `DELETE /api/transactions/<transaction_id>`

The creation logic validates `user_id`, description, `amount_cents`, transaction type, optional M-Pesa code, optional date/time, and optional budget ownership. Successful creation returns HTTP 201 in the shown code path. The exact accepted transaction types must be read from `server/models.py`.

### Dashboard and user profile
`GET /api/dashboard` accepts a user ID and uses a month value in `YYYY-MM` format. The profile module has `GET /api/users/profile` and `PUT /api/users/profile`, with `user_id` read from query parameters. Exact response schemas and access controls need tests.

### M-Pesa
Routes observed:
- `POST /api/mpesa/stkpush`
- `POST /api/mpesa/callback`
- `GET /api/mpesa/status/<checkout_id>`

The STK Push code has a simulation path and a Daraja path. It validates a user, Kenyan phone number, amount and optional budget. Amount is expressed in integer cents and the route requires at least 100 cents and multiples of 100 (whole-shilling increments). The callback route passes JSON to `process_callback` and acknowledges receipt. Checkout status is looked up in an in-memory `RESULTS` mapping in the inspected code; status durability across restarts is therefore not assured. Callback security, idempotency, persistence and live/sandbox verification remain open items.

## 7. Frontend status
The observed `src/App.jsx` imports `initialTransactions` and `initialBudgets` from `./data/mockData` and contains helper functions for reading and writing `localStorage`. The project contains Home, Transactions, Budget, Analysis and Settings pages. A search through `src` did not find API calls via `fetch`, Axios or local backend URLs. The frontend currently appears to be a prototype using mock/local browser data. This finding should be confirmed with the frontend owners, and integration should be marked pending until proven by browser network traffic and database persistence.

## 8. Testing and quality assurance
The documentation pack contains a practical testing guide with health, budget, transaction, negative-validation, M-Pesa simulation and frontend integration checks. Tests are not marked as passed unless actually executed. Recommended test evidence includes:
- request and response, including HTTP status;
- test user and database environment (no passwords or sensitive data);
- actual versus expected result;
- date, tester and any defect ticket;
- browser Network tab evidence for frontend API requests;
- database confirmation for persisted records.

## 9. Security, privacy and reliability considerations
- Do not commit `.env`, database passwords, Daraja credentials or tokens.
- Use debug mode only locally.
- Verify authentication and resource ownership for user-specific routes.
- Restrict CORS to known origins.
- Secure the M-Pesa callback endpoint and validate callback payloads.
- Make callback processing idempotent so duplicate callbacks do not duplicate transactions.
- Persist payment/check-out state if status must survive server restarts.
- Distinguish simulation outcomes from actual provider-confirmed payments.
- Use HTTPS and managed secrets for deployment.

## 10. Roles and coordination
Based on the team's stated allocation:
- Members 1 and 2: backend implementation.
- Members 3 and 4: frontend implementation.
- Member 5: oversee coordination, API contract, documentation, integration tracking and practical testing checklist.

Member 5 should not silently change backend/frontend implementation owned by teammates. Instead, agree the contract, record discrepancies, coordinate review and capture test evidence.

## 11. Current status summary
| Area | Current documentation status |
|---|---|
| Backend route inventory | Source-inspected |
| Budget field names and validation | Source-inspected |
| Transaction field names and validation | Source-inspected |
| M-Pesa route inventory and simulation branch | Source-inspected |
| PostgreSQL health check | Source-inspected |
| Frontend mock data/localStorage | Source-inspected |
| Frontend-to-backend integration | Pending verification |
| Full API test suite | Pending execution |
| Daraja sandbox/live payment | Pending execution and configuration review |
| Production readiness | Not established |

## 12. Recommendations and next steps
1. Review the API contract with backend and frontend owners.
2. Confirm exact transaction types and authentication/access-control behaviour from source.
3. Agree the frontend API client/base URL and replace mock-data flows when the team is ready.
4. Execute the testing guide and record evidence.
5. Strengthen callback security, idempotency and payment status persistence.
6. Review environment configuration and ensure secrets are excluded from version control.
7. Update this report only when tests or source inspection support a status change.

## 13. Conclusion
SmartPesa has a meaningful backend route structure and a React frontend prototype. The available source screenshots support documenting the main budget, transaction, health and M-Pesa route families. The key outstanding documentation caveat is that frontend/backend integration and full end-to-end behaviour have not been verified. Maintaining that distinction makes the report honest, useful to the team and ready to update as the project progresses.
