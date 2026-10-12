# SmartPesa Backend (Phase 2)

Flask + PostgreSQL REST API for SmartPesa, a budget tracker for M-Pesa spending.

> Status: Flask app, SQLAlchemy models, migrations, and dashboard/settings API
> routes are available. Frontend pages remain a separate integration task.

## Tech stack

- Flask 3, Flask-SQLAlchemy, Flask-Migrate (Alembic)
- PostgreSQL 14+ (`psycopg2-binary`)
- pytest

## Project structure

```
.
├── requirements.txt
├── .env.example          # copy to .env (never commit .env)
├── pytest.ini
└── server/
    ├── app.py            # create_app() factory + /api/health
    ├── config.py         # Config (Postgres) and TestConfig (SQLite in memory)
    ├── extensions.py     # db + migrate objects, constraint naming rules
    ├── models.py         # User, Budget, Transaction
    ├── migrations/       # Alembic migration history
    └── testing/         # pytest tests for models and API routes
└── src/
    └── services/
        └── api.js        # Frontend API client and Vite API base URL
```

## Setup

```bash
# 1. Python environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 2. Database (PostgreSQL must be running)
createdb smartpesa_dev             # or: psql -U postgres -c "CREATE DATABASE smartpesa_dev;"
cp .env.example .env               # then edit DATABASE_URL if your user/password differ
export DATABASE_URL=postgresql://postgres:postgres@localhost:5432/smartpesa_dev

# 3. Build the tables
cd server
flask db upgrade

# 4. Run
python app.py                      # http://localhost:5000/api/health
```

Run the tests from the repo root with `pytest`. They use an in-memory SQLite
database, so PostgreSQL does not need to be running.

## Data model

All money is stored as **integer cents** (KES 1,250.50 → `125050`) to avoid
floating-point rounding errors.

| Table | Key columns | Rules |
|---|---|---|
| `users` | `name`, `email`, `phone`, `password_hash` | email and phone unique; password stored hashed only |
| `budgets` | `user_id` → users, `category`, `limit_cents`, `month` (`YYYY-MM`) | `limit_cents >= 0`; one budget per user + category + month |
| `transactions` | `user_id` → users, `budget_id` → budgets, `description`, `amount_cents`, `transaction_type`, `mpesa_code`, `occurred_at` | `amount_cents > 0`; type is one of `paybill`, `till`, `send_money`, `airtime`, `withdrawal`, `other`; `mpesa_code` unique |

Relationships:

- One **User** has many **Budgets** and many **Transactions**.
- One **Budget** has many **Transactions**.
- Deleting a user deletes their budgets and transactions (`ON DELETE CASCADE`).
- Deleting a budget keeps its transactions but clears their `budget_id`
  (`ON DELETE SET NULL`).

User settings include a display currency (KES, USD, EUR, or GBP) and saved
transaction categories. Categories already used by budgets are also included
in the settings response.

## Frontend API configuration

The API client reads `VITE_API_URL`; its local default is
`http://localhost:5000/api`. Configure that variable in the frontend's local
Vite environment file when the API runs at a different address. The backend
allows the origin configured by `FRONTEND_ORIGIN` (default
`http://localhost:5173`); set it to the frontend's actual origin when needed.

Member 3 dashboard/settings endpoints:

| Method | Endpoint | Purpose |
|---|---|---|
| `GET` | `/api/users/<user_id>/dashboard` | User summary, budgets, and recent transactions |
| `GET` | `/api/users/<user_id>/settings` | User currency and categories |
| `PATCH` | `/api/users/<user_id>/settings` | Update the currency |
| `POST` | `/api/users/<user_id>/settings/categories` | Add a category using `{"name": "Health"}` |
| `DELETE` | `/api/users/<user_id>/settings/categories/<category_id>` | Remove a saved category |

Run `flask db upgrade` from `server/` after updating to apply the user currency
and category tables migration.

## Changing the models

After editing `server/models.py`:

```bash
cd server
flask db migrate -m "describe the change"
flask db upgrade
```

Commit the new file in `server/migrations/versions/` along with your model change.
