# Timesheet Portal

School project web application for managing:

- users
- teams
- timesheets
- absences
- manager approvals

Project structure:

- [Backend](./Backend/README.md) - FastAPI, PostgreSQL, Alembic, Docker
- [Frontend](./Frontend/README.md) - React, Vite, Axios, React Router

## Quick Start

### 1. Start backend

Open a terminal in `Backend`:

```powershell
cd Backend
docker compose up --build
```

Backend will be available at:

- `http://localhost:8000/docs`
- `http://localhost:8000/health`

Available backend variants:

- classic:

```powershell
docker compose up --build
```

- RabbitMQ:

```powershell
docker compose -f docker-compose.yml -f docker-compose.rabbitmq.yml up --build
```

- Camunda:

```powershell
docker compose -f docker-compose.yml -f docker-compose.camunda.yml up --build -d
docker compose -f docker-compose.yml -f docker-compose.camunda.yml restart backend camunda-worker
```

Camunda URLs:

- API: `http://localhost:8000/docs`
- Operate: `http://localhost:8080`

Operate login:

- username: `demo`
- password: `demo`

### 2. Start frontend

Open a second terminal in `Frontend`:

```powershell
cd Frontend
npm install
npm.cmd run dev -- --host 0.0.0.0
```

Frontend will usually run at:

- `http://localhost:5173`
- or `http://localhost:5174` if port `5173` is already in use

## Demo Login

Use one of the seeded backend users:

- `admin@demo.local`
- `manager.alpha@demo.local`
- `manager.beta@demo.local`
- `alice@demo.local`
- `bob@demo.local`
- `eva@demo.local`

Password:

```text
demo123
```

## Recommended Workflow

- keep one terminal open for backend
- keep one terminal open for frontend
- backend changes usually require backend restart
- frontend changes are reloaded automatically by Vite

## Notes

- If `docker` is not recognized, install Docker Desktop
- If `npm` is not recognized, install Node.js LTS
- If PowerShell blocks `npm`, use `npm.cmd` instead of `npm`
- Detailed setup and troubleshooting are in:
  - [Backend README](./Backend/README.md)
  - [Frontend README](./Frontend/README.md)
