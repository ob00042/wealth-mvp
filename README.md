# Wealth MVP

A minimal wealth management platform inspired by products like Altoo, Addepar, Masttro, and Landytech.

The goal of this MVP is to aggregate a client's wealth across multiple banks and display it in a single dashboard.

Current features:

- Store advisors
- Store clients (linked to advisors)
- Store financial institutions (banks)
- Store bank accounts
- Store investment positions
- Advisor dashboard to view all managed clients
- Client detail views with banks, accounts, and positions
- REST API with FastAPI
- PostgreSQL database
- Next.js dashboard

---

# Tech Stack

## Backend

| Package | Purpose |
|---------|---------|
| Python 3.13 | Backend language |
| FastAPI | REST API framework |
| SQLAlchemy | ORM for interacting with PostgreSQL |
| Alembic | Database migrations |
| Pydantic | Request/response validation |
| Uvicorn | ASGI web server |
| psycopg2 | PostgreSQL driver |

## Frontend

| Package | Purpose |
|---------|---------|
| Next.js | React framework |
| React | UI library |
| TypeScript | Type-safe JavaScript |
| Tailwind CSS | Styling |

## Database

| Technology | Purpose |
|------------|---------|
| PostgreSQL | Primary relational database |

---

# Project Structure

```
wealth-mvp/

├── backend/
│   ├── alembic/
│   ├── app/
│   │   ├── api/
│   │   ├── db/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── main.py
│   │
│   ├── requirements.txt
│   ├── seed_data.py
│   └── .env
│
├── frontend/
│   ├── src/
│   │   └── app/
│   ├── package.json
│   └── next.config.ts
│
└── README.md
```

---

# Backend Setup

Create and activate a virtual environment.

```bash
cd backend

python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Configure your `.env` file.

Example:

```text
DATABASE_URL=postgresql://username:password@localhost:5432/wealth_mvp
```

Run database migrations.

```bash
alembic upgrade head
```

Seed the database with sample data (optional).

```bash
python3 seed_data.py
```

This will create sample advisors, clients, banks, accounts, and positions for testing.

Start the API.

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```
http://localhost:8000
```

Swagger documentation:

```
http://localhost:8000/docs
```

---

# Frontend Setup

Install dependencies.

```bash
cd frontend

npm install
```

Run the development server.

```bash
npm run dev
```

The application will be available at:

```
http://localhost:3000
```

---

# Development Workflow

### Start PostgreSQL

Ensure PostgreSQL is running.

### Start the backend

```bash
cd backend

source .venv/bin/activate

uvicorn app.main:app --reload
```

### Start the frontend

Open a second terminal.

```bash
cd frontend

npm run dev
```

---

# Database

Current data model:

```
Advisor
    │
    ├── Client
            │
            ├── Institution (Bank)
                    │
                    ├── Account
                            │
                            ├── Position
```

Relationships:

- An advisor manages many clients
- A client belongs to one advisor
- A client owns many institutions
- An institution owns many accounts
- An account owns many positions

---

# Current API

```
GET     /advisors
POST    /advisors
GET     /advisors/{id}/dashboard

GET     /clients
POST    /clients

GET     /accounts
POST    /accounts

GET     /positions
POST    /positions

GET     /clients/{id}/dashboard
```

Interactive API documentation is available via Swagger.

---

# Frontend Routes

```
/                          - Redirects to login
/login                     - Advisor or client login
/client                    - Read-only dashboard for the signed-in client
/advisor                   - Advisor dashboard (shows all managed clients)
/advisor/client/{id}       - Client detail view (shows banks, accounts, positions)
```

# Roadmap

- Bank integrations
- Portfolio allocation
- Performance analytics
- Multi-currency support
- Transaction history
- Document vault
- Reporting

---

# License

Private project.

# Client login and access control

Apply the migration before starting the updated backend:

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

Existing clients retain their data and have no login until their advisor enables it.
Sign in as an advisor, open a client, and use **Client login access** to set an
email and password (at least 8 characters, at most 72 UTF-8 bytes). Share those
credentials with that client through your usual secure channel. The same form
can reset credentials. Client emails are unique and case insensitive at login.

On `/login`, select **Client**. Clients see only their own banks, accounts,
positions, and total assets at `/client`, with no editing controls. API access
is enforced independently of the UI: list endpoints are scoped to the signed-in
user, other clients' dashboards return 404, and writes require the owning advisor.
Existing advisor sessions must sign in again because tokens now include a role.

Additional endpoints:

- `POST /clients/login` — client email/password authentication
- `GET /clients/me/dashboard` — signed-in client's own dashboard
- `PUT /clients/{id}/credentials` — owning advisor sets client login credentials

Run the access-control regression tests with:

```bash
cd backend
.venv/bin/python -m unittest discover -s tests
```


Demo client logins (choose **Client** on the login screen):

| Client | Email | Password |
|--------|-------|----------|
| Jane Doe | jane.doe@example.com | JaneDemo123! |
| Mister Agapitos | mister.agapitos@example.com | AgapitosDemo123! |

These credentials are included in `seed_data.py` for local demo use. The seed
script deletes and rebuilds sample data; it is not needed to log into the
existing demo clients once their credentials have been configured.

# Transactions and historical valuations

After pulling this feature, apply the schema and add history to existing demo clients:

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python seed_history.py
```

This preserves current accounts, positions and credentials. Re-running the history
seed skips existing transaction source IDs and valuation keys. The full
`seed_data.py` reset also includes history, but still deletes and rebuilds demo data.

Jane has 202 transactions and Mister Agapitos has 207. Each has 13 portfolio
snapshots (52 account snapshots), from 30 September 2025 through 22 September 2026.
The monthly series plus the final dated snapshot is synthetic and labelled in the UI.
The final snapshot reconciles to existing cash and investment values. Each interval's
cash movement reconciles to its transactions. Trades also change synthetic holding
quantities; market prices fluctuate between snapshots. Existing balances are not
updated by importing history.

Both roles see **Activity & history** below portfolio detail. Filter by account,
currency and date, inspect the chart or valuation table, and filter transactions
by type with server-side pagination. There is no editing or trading UI.

Accounting conventions:

- `Account.balance` is **cash**, excluding investment positions.
- Transaction `amount` is signed cash: buys, withdrawals and fees are negative;
  sells, deposits and income are positive. Trade quantity is positive for buys
  and negative for sells. Fees should be separate rows.
- Trade date and optional settlement date are separate fields. Demo transactions
  settle on the same day. No pending/settled balance engine is implemented.
- Account valuations are end-of-day cash and aggregate investment values for an
  account/date/currency; total value is their sum. Money uses database decimals.
- Values are grouped by original currency, never summed across currencies.
- Change in value includes cash flows and is **not** a performance return.
- Missing account snapshots are flagged as partial coverage, not filled with zero
  or carried forward. Coverage conservatively includes current accounts and those
  with recorded history in the currency; account opening/closing dates are not yet modelled.
- Source and external transaction IDs prevent duplicate imports. Imported timestamps
  preserve provenance. The seed skips existing valuations rather than overwriting them.

Read endpoints (Bearer token required):

- `GET /clients/{id}/transactions` or `/clients/me/transactions`
- `GET /clients/{id}/valuations` or `/clients/me/valuations`

Both accept optional `account_id`, `currency`, `start_date`, and `end_date` (inclusive).
Transactions also accept `type`, `limit` (1–100) and `offset`. They return newest
first, with stable ID ordering for same-day entries. Valuations return oldest first
with account coverage and source labels. Access is limited to the client themselves
or their owning advisor; account filters cannot bypass this check.

This implements persisted historical data and its read APIs. Actual bank connectors,
CSV import UI, daily price feeds, individual position snapshots and return calculations
are future work. The demo fixture is a fixed history, not a background updating feed.

# Fictional market-data provider

The authenticated mock API serves fictional product profiles and dated constituents.
It makes no Bloomberg calls and does not reproduce a Bloomberg API contract. The
`MarketDataProvider` interface separates the application from its fixture adapter,
so a licensed provider can be integrated later.

To add products to an existing demo database without resetting its clients:

```bash
cd backend
.venv/bin/alembic upgrade head
.venv/bin/python seed_products.py
```

The seed adds a **Fictional Product Demo Portfolio** account to each demo client,
with 15,000 cash in the client's currency and these investment positions:

| Client | Product | Value |
|--------|---------|-------|
| Jane Doe | Atlas Global Equity ETF | USD 20,000 |
| Jane Doe | Nova Innovation ETF | USD 10,000 |
| Jane Doe | Cedar Technologies | USD 3,000 |
| Mister Agapitos | Atlas Global Equity ETF — EUR class | EUR 30,000 |
| Mister Agapitos | Horizon Balanced Fund | EUR 20,000 |
| Mister Agapitos | Cedar Technologies — EUR listing | EUR 5,000 |

Existing positions and credentials are preserved. Re-running the seed skips
existing demo positions and history. Each new account adds 63 transactions and
13 valuation snapshots, extending the original history totals above to 265/270
transactions and 65 account snapshots per client. The full `seed_data.py` reset
also includes these products.

Both advisor and client dashboards show **Product holdings** for linked positions.
Choose a product and an optional cutoff date to inspect its latest snapshot on or
before that date. Fixtures include 30 June and 22 September 2026 snapshots,
shared underlying security IDs across products, and a fund with 10% undisclosed
holdings. The UI reports coverage, snapshot age, and a demo stale-data threshold
of 45 days. Security currency is metadata, not a calculated FX exposure.

Bearer-authenticated endpoints:

- `GET /market-data/products`
- `GET /market-data/products/{product_id}/holdings?as_of=2026-09-22`

The cutoff defaults to today's UTC date. Unknown products and dates before the
first snapshot return 404; future cutoff dates return 422; an unavailable provider
returns 503. Product metadata contains no client information. Client portfolios
continue to use the existing ownership checks.

Fixtures live in `backend/app/providers/fixtures/products.json`. Constituents use
fractional NAV weights; undisclosed weight stays explicit rather than being
redistributed. Underlying constituents are not added to account balances, avoiding
double counting. Combined portfolio exposure analysis is described below. Recommendations remain
out of scope.


# Combined portfolio exposure

Both roles now see **Portfolio exposure** above Product holdings. No migration or
new seed is required if the fictional product positions have already been loaded.
The read-only endpoint is `GET /clients/me/exposure?currency=USD` for clients or
`GET /clients/{id}/exposure?currency=EUR` for the owning advisor. Optional `as_of`
is a composition cutoff, not a portfolio valuation date; future dates are rejected.

- Uses current cash and position market values in the selected currency. No FX
  conversion, historical position reconstruction, or trading is performed.
- A fund's position value times each disclosed constituent weight is its indirect
  exposure. Provider-linked stocks with a single 100% constituent are direct
  exposure. Canonical security IDs combine these across accounts and products.
  Names/tickers are never used to guess identity; different securities issued by
  the same company are not automatically combined.
- Asset-class, sector, and country allocations use total assets as denominator,
  retaining cash and unresolved investments. Investment coverage excludes cash.
  Values use Decimal calculations; the UI rounds display values only.
- Missing mappings/products/snapshots, provider outages and undisclosed fund
  holdings retain their original value as unresolved. Conflicting classifications
  are marked unknown. Stale compositions remain included but are flagged.
- Pairwise fund overlap lists shared disclosed securities and the sum of both
  funds' exposures to those securities. Pair totals are not additive across pairs.
- Source details show account, position, composition date, weight and stale status.
  Search and a multiple-position filter help inspect concentration.
- This is one-level fund look-through for long positions and non-negative cash.
  Nested fund recursion, issuer-level consolidation, derivatives/leverage modelling,
  FX risk, real Bloomberg integration and recommendations are not implemented.

With the September 22, 2026 composition, Jane's Cedar exposure is USD 12,500
(3,000 direct + 5,000 Atlas + 4,500 Nova). Mister Agapitos's is EUR 14,500
(5,000 direct + 7,500 Atlas + 2,000 Horizon). Horizon's undisclosed 10% remains
EUR 2,000 unresolved. Legacy positions without provider mappings remain unresolved
rather than being silently classified or matched to fictional instruments.

Regression coverage includes exact aggregation, reconciliation, fund overlap,
partial holdings, currency separation, dated/stale/missing sources, provider
outages, repeated products, conflicting metadata and ownership restrictions.

# Reporting currency conversion

Both client and advisor client views include a **Consolidated portfolio** panel.
Choose EUR, USD, GBP, CHF or JPY to translate all current cash and investment
positions, retaining original values in a currency breakdown and expandable detail.
The original-currency detail, fund exposure and history panels remain separate.

`GET /clients/{id}/reporting-valuation?currency=EUR` (or `/clients/me/…`)
uses the existing ownership checks. Optional `as_of` selects the latest FX snapshot
on or before that date; future dates and unsupported reporting currencies return 422.
No migration or seed change is needed.

Rates are explicitly fictional, not Bloomberg or live quotes. The dataset in
`backend/app/providers/fixtures/fx.json` contains June 30 and September 22, 2026 snapshots,
quoted as currency units per EUR. Cross rate = target quote / source quote;
converted value = original value × cross rate. Same-currency translation is 1.
All calculations use Decimal and totals are calculated before display rounding.
Dates more than 45 days after the selected snapshot show a stale warning.

A missing rate preserves original values but leaves converted values unavailable;
the full total is null and the UI labels the known portion as a converted subtotal.
Zero-value entries do not make totals incomplete. Signed values are preserved.
This translates current portfolio values, not historical holdings or returns.
Currency grouping reflects valuation currencies, not underlying economic FX risk.
Tests cover cross rates, reconciliation, identity conversion, dated/stale/missing
rates, empty and signed portfolios, validation and ownership isolation.


## FX provider API

FX rates now use a replaceable `FxProvider` interface and `FictionalFxProvider`
fixture adapter, matching the market-data provider architecture. The adapter
validates positive decimal quotes and a unit base-currency rate at startup.

`GET /market-data/fx/rates?as_of=2026-09-22` requires an advisor or client Bearer
token and returns base currency, decimal quotes, effective date, requested cutoff,
source, synthetic flag, supported currencies, age and stale status. Quotes mean
units of each currency per one unit of the response's base currency.

The reporting-valuation endpoint receives the same provider via dependency
injection. It does not call its own HTTP endpoint. A future licensed adapter can
replace the fixture provider without changing portfolio calculations. No external
network calls, subscriptions or credentials are needed for the demo.

The rates endpoint returns 404 when no snapshot precedes the cutoff, 422 for a
future or malformed date, and 503 for provider unavailability. Portfolio valuation
continues to preserve unconvertible amounts when a snapshot or quote is missing;
a provider outage returns 503, which the existing UI displays with Retry.

# Performance analytics (phase 1)

Both roles have a **Performance** section with account/date filters, a return chart,
monthly/quarterly/yearly period tables, and a summary since the first recorded
valuation (or the selected range). No migration or seed change is required.
`GET /clients/{id}/performance?currency=EUR&frequency=monthly` and the `/me` variant
require ownership access. Optional `account_id`, `start_date`, and `end_date` use
the same access and validation rules as history. Currency is required.

The calculation uses Decimal and non-annualised Modified Dietz:

- Gain = closing value − opening value − signed external flows.
- Return = gain / (opening value + sum(flow × days remaining / period days)).
- Cash flows occur at end of day; the opening date is excluded, closing date
  included with zero weight. Deposits/withdrawals are external. Trades are internal;
  dividends/interest and recorded fees remain in net investment gain/loss.
- For a selected account, transfers cross that account's boundary and are external
  flows. Portfolio-wide transfer records lack explicit internal/external linkage,
  so affected portfolio periods are unavailable rather than matched by guessed
  amounts or counted as contributions. Explicit transfer linking is future work.
- Every observed interval must reconcile cash separately for every expected account.
  Missing account valuations, unknown/delayed settlement, negative balances, and
  ambiguous transfers block results. Nonpositive weighted capital blocks the
  percentage return. Data issues are returned and shown alongside affected periods.
- Expected coverage includes current accounts/position currencies and accounts with
  recorded history/activity in the selected currency. Account opening/closing dates
  are not modelled. Reconciliation cannot establish completeness of a bank import
  (for example, omitted offsetting movements can still reconcile).
- Only snapshots inside the requested range are used. Actual start/end dates are
  displayed; no valuations are interpolated. Calendar groups with missing boundary
  dates are labelled partial. The overall return is calculated directly over the
  full observed span, not summed from monthly returns. This is an approximation,
  not daily time-weighted return or IRR. Sources label synthetic demo history.

This phase uses original currencies only. Historical FX consolidation, benchmarks,
annualisation, and PDF reporting remain future work. Tests cover known cash-flow
examples, boundary timing, income/fees/trades, reconciliation, incomplete coverage,
transfers, settlement ambiguity, calendar grouping, currency isolation and access.
