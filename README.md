# Timesheet & Absence Portal Backend

Production-like MVP backend for an internal company portal covering attendance recording, monthly timesheets, absences, approvals, teams, users, and audit logging.

## Stack

- Python 3.11+
- FastAPI
- SQLAlchemy 2.x
- Alembic
- PostgreSQL
- Docker Compose
- Pytest

## Project Tree

```text
.
├── app/
│   ├── api/
│   │   ├── absences.py
│   │   ├── audit.py
│   │   ├── auth.py
│   │   ├── manager.py
│   │   ├── teams.py
│   │   ├── timesheets.py
│   │   └── users.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── deps.py
│   │   └── security.py
│   ├── services/
│   │   ├── absences.py
│   │   ├── access.py
│   │   ├── audit.py
│   │   ├── auth.py
│   │   ├── teams.py
│   │   ├── timesheets.py
│   │   └── users.py
│   ├── main.py
│   ├── models.py
│   ├── schemas.py
│   └── seed.py
├── alembic/
│   ├── env.py
│   └── versions/
│       └── 0001_initial.py
├── tests/
│   ├── conftest.py
│   └── test_business_rules.py
├── .env
├── .env.example
├── Dockerfile
├── alembic.ini
├── application.py
├── docker-compose.yml
├── pytest.ini
└── requirements.txt
```

## Quick Start

### Docker Compose

This is the primary supported path.

```bash
docker compose up --build
```

Then open:

- API docs: http://localhost:8000/docs
- Health endpoint: http://localhost:8000/health

### Local Python Run

```bash
python -m pip install -r requirements.txt
alembic upgrade head
python -m app.seed
uvicorn app.main:app --reload
```

## Demo Credentials

All seeded users use this password:

```text
demo123
```

Users:

- admin@demo.local
- manager.alpha@demo.local
- manager.beta@demo.local
- alice@demo.local
- bob@demo.local
- eva@demo.local

## Main Endpoints

### Auth

- POST /auth/login
- POST /auth/invite
- POST /auth/set-password
- GET /auth/me

### Users and Teams

- GET /users
- POST /users
- PATCH /users/{id}
- DELETE /users/{id}
- GET /teams
- POST /teams
- PATCH /teams/{id}
- POST /teams/{id}/members
- DELETE /teams/{id}/members/{user_id}

### Timesheets

- GET /timesheets
- POST /timesheets/{year}/{month}/days
- PATCH /timesheets/{timesheet_id}/days/{date}
- POST /timesheets/{timesheet_id}/submit
- POST /timesheets/{timesheet_id}/approve
- POST /timesheets/{timesheet_id}/reject
- POST /timesheets/{timesheet_id}/unlock

### Absences

- GET /absences
- POST /absences
- POST /absences/{id}/approve
- POST /absences/{id}/reject
- POST /absences/{id}/cancel

### Audit / Manager Views

- GET /audit-logs
- GET /manager/pending-timesheets
- GET /manager/pending-absences
- GET /manager/team-overview

## Example API Usage

### 1. Login

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@demo.local","password":"demo123"}'
```

### 2. Create a Team

```bash
curl -X POST http://localhost:8000/teams \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Platform","manager_user_id":2}'
```

### 3. Enter Timesheet Days

```bash
curl -X POST http://localhost:8000/timesheets/2026/4/days \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[
    {"date":"2026-04-01","hours":8,"day_type":"WORK"},
    {"date":"2026-04-02","hours":8,"day_type":"WORK"}
  ]'
```

### 4. Request Vacation

```bash
curl -X POST http://localhost:8000/absences \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type":"VACATION","date_from":"2026-06-01","date_to":"2026-06-05","comment":"Family trip"}'
```

## Business Rules Implemented

- Monthly timesheet hard limit of 160 hours
- Timesheet lifecycle with lock/unlock behavior
- Vacation limit of 14 working days per year
- Sick leave requests without yearly cap
- Absence overlap prevention
- Approved absence blocks hour entry on covered days
- Manager approvals restricted to own team members
- Admin unlock with mandatory reason and audit logging
- Audit logging for hours changes, decisions, and admin actions

## Tests Included

The test suite covers:

- 160-hour hard limit
- 14-day vacation limit
- absence overlap prevention
- absence blocking hour entry
- timesheet transitions
- manager approval scope
- admin unlock audit trail

Run with:

```bash
pytest -q
```

## Implemented vs Stubbed

### Implemented

- JWT login and current-user endpoint
- invitation-based password setup flow
- role-based access for Employee, Manager, Admin
- team and user management
- timesheet and absence workflows
- audit logging and manager dashboards
- Docker Compose, Alembic migration, seed data, and tests

### Stubbed / Simplified

- logout is stateless and frontend-driven
- notifications are left as future TODO hooks
- no email delivery for invites in the MVP; the invite token is returned in the response for local demo use
- public holidays are intentionally ignored for vacation counting

## Notes

If Docker Desktop is not running, start it first and then re-run:

```bash
docker compose up --build
```
