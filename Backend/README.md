# Timesheet Portal Backend

FastAPI backend for the school project timesheet system. It covers users, teams, timesheets, absences, manager approvals, and audit logging.

## Stack

- Python 3.11
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Docker Compose
- Pytest

## Main Modules

- `auth`
- `users`
- `teams`
- `timesheets`
- `absences`
- `manager`
- `audit`

## Requirements

Recommended local setup:

- Docker Desktop

Optional local-only setup:

- Python 3.11+
- PostgreSQL

## Quick Start

### Recommended: run with Docker

Open a terminal in `Backend` and run:

```powershell
docker compose up --build
```

This starts:

- PostgreSQL database
- FastAPI backend
- Alembic migrations
- demo seed data

Then open:

- API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

To stop containers:

```powershell
docker compose down
```

### RabbitMQ variant

Run the RabbitMQ-enhanced variant with workers:

```powershell
docker compose -f docker-compose.yml -f docker-compose.rabbitmq.yml up --build
```

This starts:

- database
- backend
- RabbitMQ
- worker containers for audit, notification, timesheet, absence, and approval flows

### Camunda variant

Run the Camunda/Zeebe workflow variant:

```powershell
docker compose -f docker-compose.yml -f docker-compose.camunda.yml up --build -d
```

After the stack is up, restart backend and worker once so they reconnect after Zeebe is fully ready:

```powershell
docker compose -f docker-compose.yml -f docker-compose.camunda.yml restart backend camunda-worker
```

This starts:

- database
- backend
- Camunda Zeebe
- Operate UI
- Elasticsearch
- dedicated Camunda worker container

Useful Camunda URLs:

- Operate UI: `http://localhost:8080`
- Zeebe gateway: `localhost:26500`

Operate login:

- username: `demo`
- password: `demo`

Camunda mode is enabled only in this compose variant through environment variables.

### Run tests locally

If you have a local Python virtual environment in `Backend/.venv`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_business_rules.py -q
```

## Local Python Run Without Docker

Use this only if you want to run PostgreSQL yourself.

1. Update `Backend/.env`

Change:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/timesheet_portal
```

to something like:

```env
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/timesheet_portal
```

2. Install dependencies and run:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m app.seed
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

## Demo Credentials

Seeded password for all demo users:

```text
demo123
```

Seeded users:

- `admin@demo.local`
- `manager.alpha@demo.local`
- `manager.beta@demo.local`
- `alice@demo.local`
- `bob@demo.local`
- `eva@demo.local`

## Environment

Example `Backend/.env.example`:

```env
APP_ENV=development
SECRET_KEY=change-me-in-production
DATABASE_URL=postgresql+psycopg://postgres:postgres@db:5432/timesheet_portal
SEED_DEMO_DATA=true
DEMO_PASSWORD=demo123
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
CAMUNDA_ENABLED=false
ZEEBE_ADDRESS=zeebe:26500
CAMUNDA_PROCESS_ID=Process_TimesheetApproval
```

## Main Endpoints

### Auth

- `POST /auth/login`
- `GET /auth/me`
- `POST /auth/invite`
- `POST /auth/set-password`

### Users

- `GET /users`
- `POST /users`
- `PATCH /users/{user_id}`
- `DELETE /users/{user_id}`

### Teams

- `GET /teams`
- `POST /teams`
- `PATCH /teams/{team_id}`
- `POST /teams/{team_id}/members`
- `DELETE /teams/{team_id}/members/{user_id}`

### Timesheets

- `GET /timesheets`
- `POST /timesheets/{year}/{month}/days`
- `PATCH /timesheets/{timesheet_id}/days/{entry_date}`
- `POST /timesheets/{timesheet_id}/submit`
- `POST /timesheets/{timesheet_id}/approve`
- `POST /timesheets/{timesheet_id}/reject`
- `POST /timesheets/{timesheet_id}/unlock`

### Absences

- `GET /absences`
- `POST /absences`
- `POST /absences/{absence_id}/approve`
- `POST /absences/{absence_id}/reject`
- `POST /absences/{absence_id}/cancel`

### Manager

- `GET /manager/pending-timesheets`
- `GET /manager/pending-absences`
- `GET /manager/team-overview`

## Current Business Rules

- Monthly timesheet total cannot exceed `160` hours
- Vacation is requested through absences, not entered directly in timesheets
- Manual sick entry in timesheet is allowed for one day only
- Approved absence blocks conflicting work-hour entry
- Rejected timesheet can be edited by its owner and stays `REJECTED` until resubmitted
- Managers and admins cannot approve or reject their own timesheets
- Managers can only approve members of their own team
- Only owner or admin can edit timesheets
- Admin can unlock timesheets with a reason

## Notes

- Backend CORS is configured for local frontend development ports such as `5173`, `5174`, and `5175`
- Docker builds ignore local caches through `Backend/.dockerignore`
- If Docker says `docker` is not recognized, install Docker Desktop first
- The Camunda BPMN process is stored in `Backend/camunda/processes/timesheet-approval.bpmn`
- Classic, RabbitMQ, and Camunda variants are intentionally separated through compose overrides
- For the Camunda demo, verify workflow instances in Operate after submitting and approving/rejecting a timesheet
