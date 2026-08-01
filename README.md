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
/                          - Home page (sample client dashboard)
/advisor                   - Advisor dashboard (shows all managed clients)
/advisor/client/{id}       - Client detail view (shows banks, accounts, positions)
```

# Roadmap

- Authentication
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