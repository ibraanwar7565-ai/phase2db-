# SmartPesa Backend (Phase 2)

Flask + PostgreSQL REST API for SmartPesa, a budget tracker for M-Pesa spending.

> Status: models, migrations, seed data, CORS, error handlers, auth and
> budget/transaction routes are in place.

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
    └── testing/          # pytest tests for the models
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

# 4. Add demo data (3 users, 2 months of budgets and M-Pesa transactions)
python seed.py                     # type SEED to confirm; or: python seed.py --yes

# 5. Run
python app.py                      # http://localhost:5000/api/health
```

Run the tests from the repo root with `pytest`. They use an in-memory SQLite
database, so PostgreSQL does not need to be running.

## Data model

All money is stored as **integer cents** (KES 1,250.50 → `125050`) to avoid
floating-point rounding errors.

| Table | Key columns | Rules |
|---|---|---|
| `users` | `name`, `email`, `phone`, `password_hash` | name not blank; email contains `@`; email and phone unique; password stored hashed only |
| `budgets` | `user_id` → users, `category`, `limit_cents`, `month` (`YYYY-MM`) | `0 <= limit_cents <= 1,000,000,000` (KES 10M); category not blank; month is `YYYY-MM` with month 01–12; one budget per user + category + month |
| `transactions` | `user_id` → users, `budget_id` → budgets, `description`, `amount_cents`, `transaction_type`, `mpesa_code`, `occurred_at` | `0 < amount_cents <= 100,000,000` (KES 1M); description not blank; type is one of `paybill`, `till`, `send_money`, `airtime`, `withdrawal`, `other`; `mpesa_code` unique |

Relationships:

- One **User** has many **Budgets** and many **Transactions**.
- One **Budget** has many **Transactions**.
- Deleting a user deletes their budgets and transactions (`ON DELETE CASCADE`).
- Deleting a budget keeps its transactions but clears their `budget_id`
  (`ON DELETE SET NULL`).

## Demo data

`python seed.py` creates three demo users with budgets and transactions for the
previous and current month. One user stays under budget, one overspends, and
one is roughly on budget, so analytics has something to show.

| Email | Password |
|---|---|
| `wanjiku@smartpesa.local` | `DemoPass123!` |
| `otieno@smartpesa.local` | `DemoPass123!` |
| `amina@smartpesa.local` | `DemoPass123!` |

Running it again deletes and recreates only the `@smartpesa.local` users.

## Changing the models

After editing `server/models.py`:

```bash
cd server
flask db migrate -m "describe the change"
flask db upgrade
```

Commit the new file in `server/migrations/versions/` along with your model change.
