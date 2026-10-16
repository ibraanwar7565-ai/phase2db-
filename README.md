# SmartPesa Backend (Phase 2)

SmartPesa is a Flask REST API for tracking personal budgets and M-Pesa
spending. The backend provides account registration and login, profile
management, monthly budgets, expense transactions, a dashboard summary, and
M-Pesa STK Push integration with a local simulation mode.

## Backend capabilities

- **Accounts:** register users, verify passwords at login, and read or update
  profile details. Passwords are stored as hashes and are never included in
  user responses.
- **Budgets:** create, list, read, update, and delete monthly category budgets.
  Each budget includes spending and remaining-balance totals.
- **Transactions:** create and list expenses, filter by budget or month, read
  individual transactions, and delete transactions. A transaction may be
  linked to a budget or left unbudgeted.
- **Dashboard:** summarize a user's budgets and spending for a selected month,
  including per-budget utilization and the five most recent transactions.
- **M-Pesa:** request an STK Push in simulation or Daraja sandbox mode, receive
  payment callbacks, and query checkout status.
- **Operational support:** database health check, PostgreSQL migrations,
  constrained data models, JSON API errors, development CORS configuration,
  and pytest tests using in-memory SQLite.

The API currently uses `user_id` values supplied in requests to select a
user's data. Registration and login do not issue access tokens, and the other
routes do not require an authenticated session. Add authentication and
authorization before exposing the API to untrusted clients.

## Technology

- Python 3
- Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic)
- PostgreSQL (`psycopg2-binary`)
- Requests for Safaricom Daraja API calls
- pytest

## Project layout

```text
.
├── .env.example
├── pytest.ini
├── requirements.txt
└── server/
    ├── app.py             # Application factory, routes registration, health check
    ├── auth.py            # Registration and login
    ├── budgets.py         # Budget endpoints
    ├── config.py          # Environment-based configuration
    ├── dashboard.py       # Monthly dashboard endpoint
    ├── errors.py          # JSON API error helper
    ├── extensions.py      # SQLAlchemy and migration extensions
    ├── models.py          # User, Budget, Transaction models
    ├── mpesa.py           # STK Push, callback, and payment status
    ├── seed.py            # Repeatable demo data seeder
    ├── transactions.py    # Transaction endpoints
    ├── users.py           # Profile endpoints
    ├── utils.py           # Shared input helpers
    ├── migrations/        # Alembic migration history
    └── testing/           # pytest tests
```

## Setup and run

### Requirements

Install Python 3 and PostgreSQL 14 or later. Create and activate a virtual
environment, then install the project dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a PostgreSQL database and configure the environment:

```bash
createdb smartpesa_dev
cp .env.example .env
```

Edit `.env` with a PostgreSQL connection URL and a secret key, for example:

```dotenv
DATABASE_URL=postgresql+psycopg2://postgres:your-password@localhost:5432/smartpesa_dev
SECRET_KEY=replace-with-a-long-random-value
MPESA_MODE=simulate
```

System environment variables take precedence over values in `.env`. The
configuration loader looks for `.env` in the repository root or `server/`.
Never commit a real `.env` file or production credentials.

Apply migrations, optionally seed demo data, and start the development server:

```bash
cd server
flask db upgrade
python seed.py                 # asks for confirmation before replacing demo users
# python seed.py --yes         # skip the confirmation prompt
python app.py                  # http://localhost:5000
```

The API health endpoint is `GET http://localhost:5000/api/health`. It checks
both that the API is responding and that the configured database is reachable.
The built-in server runs in Flask debug mode and is for local development, not
production deployment.

## Configuration

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLAlchemy database connection URL; required |
| `SECRET_KEY` | Flask secret; required |
| `MPESA_MODE` | `simulate` (default) or `daraja` |
| `MPESA_BASE_URL` | Daraja API base URL; defaults to Safaricom sandbox |
| `MPESA_CONSUMER_KEY` | Daraja OAuth consumer key; required for Daraja mode |
| `MPESA_CONSUMER_SECRET` | Daraja OAuth consumer secret; required for Daraja mode |
| `MPESA_SHORTCODE` | Paybill/business shortcode used for STK Push |
| `MPESA_PASSKEY` | Daraja STK Push passkey |
| `MPESA_CALLBACK_URL` | Publicly reachable URL for `/api/mpesa/callback` |

Simulation mode is intended for local development and does not call Safaricom.
Daraja mode sends real requests to the configured Daraja host (the default is
the sandbox), so it requires valid credentials and a callback URL reachable by
Safaricom. Checkout requests and results are held in process memory; pending
payment state is not shared between application workers and is lost on restart.

## API

All endpoints are under `/api`. JSON request examples omit optional fields
unless they are useful to the example. Monetary values are integer cents (for
example, KES 1,250.50 is `125050`).

### Health

| Method and path | Behavior |
|---|---|
| `GET /api/health` | Returns `{"status":"ok","database":"connected"}` when the database can be reached. |

### Authentication

| Method and path | Request | Success |
|---|---|---|
| `POST /api/auth/register` | `{"name":"Amina Hassan","email":"amina@example.com","phone":"0712345678","password":"at-least-8-chars"}` | `201`; returns a message and the new user |
| `POST /api/auth/login` | `{"email":"amina@example.com","password":"at-least-8-chars"}` | `200`; returns a message and the matching user |

Registration requires a non-empty name, email, phone, and password of at least
eight characters. Email is normalized to lowercase. Duplicate email or phone
returns `409`. Login returns `401` for invalid credentials.

### User profile

| Method and path | Request | Behavior |
|---|---|---|
| `GET /api/users/profile?user_id=1` | — | Returns the user's public profile |
| `PUT /api/users/profile?user_id=1` | Any of `name`, `email`, and `phone` | Updates the supplied profile fields |

Profile updates validate email and Kenyan phone-number formats. Phone numbers
are normalized to the `2547...` or `2541...` form. Conflicting email or phone
values return `409`.

### Budgets

| Method and path | Request / query | Behavior |
|---|---|---|
| `POST /api/budgets` | `{"user_id":1,"category":"Food","limit_cents":1500000,"month":"2026-10"}` | Creates a budget; returns `201` |
| `GET /api/budgets?user_id=1&month=2026-10` | `user_id` required; `month` optional | Lists budgets, ordered by month and category |
| `GET /api/budgets/12` | — | Returns one budget, including spent and remaining cents |
| `PUT /api/budgets/12` | Any of `category`, `limit_cents`, and `month` | Updates supplied fields |
| `DELETE /api/budgets/12` | — | Deletes the budget; returns `204` |

Budget categories must contain 1–50 characters, the limit must be between
`0` and `1,000,000,000` cents, and the month must use `YYYY-MM` with a valid
month. A user may have only one budget per category per month. Creating a
duplicate or referencing a missing user returns `409`.

### Transactions

| Method and path | Request / query | Behavior |
|---|---|---|
| `POST /api/transactions` | `{"user_id":1,"budget_id":12,"description":"Groceries","amount_cents":125050,"transaction_type":"till","mpesa_code":"SJK3XY12AB","occurred_at":"2026-10-13T12:00:00Z"}` | Creates an expense; returns `201` |
| `GET /api/transactions?user_id=1&budget_id=12&month=2026-10` | `user_id` required; `budget_id` and `month` optional | Lists transactions newest first; month filters by occurrence time |
| `GET /api/transactions/42` | — | Returns one transaction |
| `DELETE /api/transactions/42` | — | Deletes a transaction; returns `204` |

Transaction descriptions must contain 1–200 characters. Amounts must be
positive integer cents up to `100,000,000` (KES 1,000,000). The optional type
defaults to `other` and must be one of `paybill`, `till`, `send_money`,
`airtime`, `withdrawal`, or `other`. An optional budget must belong to the
same user. `occurred_at`, when supplied, must be an ISO date/time; a value
without a timezone is treated as UTC. M-Pesa confirmation codes are unique.

### Dashboard

| Method and path | Query | Behavior |
|---|---|---|
| `GET /api/dashboard?user_id=1&month=2026-10` | `user_id` required; `month` defaults to the current UTC month | Returns month totals, budget utilization, and up to five recent transactions |

The response includes `total_budget_cents`, `total_spent_cents`,
`remaining_cents`, `transaction_count`, a `budgets` array, and a
`recent_transactions` array. Each budget also includes `percent_used` and
`over_budget`; `percent_used` is `null` for a zero-limit budget.

### M-Pesa

| Method and path | Request / query | Behavior |
|---|---|---|
| `POST /api/mpesa/stkpush` | `{"user_id":1,"budget_id":12,"amount_cents":125000,"phone":"0712345678","description":"Groceries"}` | Starts a simulated or Daraja STK Push |
| `POST /api/mpesa/callback` | Safaricom STK callback JSON | Accepts the callback and records a successful payment as a `paybill` transaction |
| `GET /api/mpesa/status/<checkout_request_id>` | — | Returns the stored result for a checkout request |

The STK Push amount must be at least 100 cents and a multiple of 100 (whole
Kenyan shillings); its maximum is the transaction limit. `phone` is optional
and defaults to the user's saved phone number. The optional budget must belong
to that user.

In `simulate` mode, the payment is completed immediately and a transaction is
recorded; the response has status `200`. In `daraja` mode, a successful request
returns `202` with a checkout request ID and pending status. A later successful
callback records the transaction; a failed callback records a failed result.
Safaricom callbacks are acknowledged with HTTP `200`. Unknown checkout IDs
return `404` from the status endpoint.

## Data model and validation

Money is stored as integer cents to avoid floating-point rounding errors.
Database check constraints reinforce important rules even when records are
written outside the HTTP endpoints.

| Table | Important fields and rules |
|---|---|
| `users` | Name, email, phone, password hash, and creation time; email and phone are unique |
| `budgets` | User, category, integer-cent limit, `YYYY-MM` month, and creation time; unique per user/category/month |
| `transactions` | User, optional budget, description, amount in cents, transaction type, optional M-Pesa code, occurrence and creation times; M-Pesa code is unique |

A user has many budgets and transactions. Deleting a user cascades to their
budgets and transactions. Deleting a budget preserves its transactions and
sets their `budget_id` to `NULL`.

### Errors and CORS

Most API validation and resource errors use this JSON shape:

```json
{"error":{"status":400,"code":"validation_error","message":"..."}}
```

HTTP errors are also returned as JSON, and unexpected server errors return a
generic `500` response while the exception is logged. Registration and login
currently return their validation and credential errors as a simple `error`
string rather than the nested format.

CORS is enabled for `/api/*` requests from `http://localhost:5173` and
`http://127.0.0.1:5173`, suitable for the local frontend development server.

## Demo data

From `server/`, run `python seed.py` and type `SEED` to confirm, or use
`python seed.py --yes` for a non-interactive run. The seeder creates three
demo users, six category budgets per user, and transactions for the previous
and current month. It removes and recreates only users whose email ends in
`@smartpesa.local`; other users are left untouched. Demo credentials are for
local development only:

| Email | Password |
|---|---|
| `wanjiku@smartpesa.local` | `DemoPass123!` |
| `otieno@smartpesa.local` | `DemoPass123!` |
| `amina@smartpesa.local` | `DemoPass123!` |

## Migrations

After changing `server/models.py`, create and apply a migration from `server/`:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

Commit the generated file in `server/migrations/versions/` with the model
change.

## Tests

Run the tests from the repository root:

```bash
pytest
```

Tests use an in-memory SQLite database with foreign-key enforcement enabled;
PostgreSQL does not need to be running to run the test suite.
