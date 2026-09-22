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
