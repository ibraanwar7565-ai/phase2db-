# SmartPesa Documentation Pack — Member 5

## Included documents
- `SmartPesa_Full_Project_Report.docx` and `.md` — project overview, architecture, implementation status, risks and recommendations.
- `SmartPesa_API_Contract.md` — source-inspected API route and schema reference.
- `SmartPesa_Testing_Guide.md` — practical smoke, negative and M-Pesa simulation tests.
- `../backend/README.md` — backend setup and route reference.
- `../frontend/README.md` — frontend setup and current data/integration status.

## Status definitions
- **Source-inspected:** visible source screenshots confirm a route or code pattern.
- **Tested:** a test was actually run and its result recorded.
- **Pending:** requires source inspection, team confirmation or execution-based verification.

## Key findings from current screenshots
1. Flask health route: `GET /api/health`; it executes `SELECT 1` and returns health/database status.
2. Budgets use `category`, `limit_cents`, `month`, and `user_id`; the month format is `YYYY-MM`.
3. Transactions use `amount_cents`, `description`, `user_id`, `transaction_type`, with optional fields including `budget_id`, `mpesa_code`, and `occurred_at`.
4. M-Pesa routes include `POST /api/mpesa/stkpush`, `POST /api/mpesa/callback`, and `GET /api/mpesa/status/<checkout_id>`.
5. The frontend imports initial data from `src/data/mockData.js` and persists values through `localStorage`; an API call was not found by the search shown. Treat frontend/backend integration as pending.
6. M-Pesa status uses an in-memory `RESULTS` mapping in the inspected code. Durability across server restart is not assured.

## Recommended next actions when development resumes
1. Ask backend members to confirm authentication, ownership checks, exact model constants and callback persistence.
2. Ask frontend members to confirm the mock-data/localStorage finding and integrate API calls.
3. Run the testing guide and record actual outcomes.
4. Review this documentation with one backend and one frontend teammate.
5. Replace any pending status only when supported by source or test evidence.
6. Commit documentation without `.env` or secrets.
