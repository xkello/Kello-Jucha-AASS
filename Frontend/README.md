# Timesheet Portal Frontend

React frontend for the school project timesheet system. It connects to the FastAPI backend in the `Backend` folder.

## Stack

- React
- Vite
- JavaScript
- Axios
- React Router

## Features Implemented

- Login page connected to backend
- Top navigation layout
- Dashboard
- Timesheets list
- Timesheet detail
- Create timesheet
- Edit own draft or rejected timesheet
- Absences list
- Create absence
- Teams overview
- Team detail
- Manager approvals page
- Users page

## Requirements

- Node.js LTS
- npm
- running backend on `http://localhost:8000`

## Installation

Open a terminal in `Frontend` and run:

```powershell
npm install
```

## Environment

Create `.env` from `.env.example`:

```powershell
copy .env.example .env
```

Default value:

```env
VITE_API_URL=http://localhost:8000
```

## Start Development Server

```powershell
npm.cmd run dev -- --host 0.0.0.0
```

Then open the local URL shown by Vite.

Usually:

- `http://localhost:5173`
- or `http://localhost:5174` if `5173` is already in use

## Recommended Project Run Flow

### Terminal 1: backend

```powershell
cd c:\Users\tjuch\Documents\GitHub\AASS\Kello-Jucha-AASS\Backend
docker compose up --build
```

### Terminal 2: frontend

```powershell
cd c:\Users\tjuch\Documents\GitHub\AASS\Kello-Jucha-AASS\Frontend
npm.cmd run dev -- --host 0.0.0.0
```

## Demo Login

Use one of the seeded users from the backend:

- `manager.alpha@demo.local`
- `admin@demo.local`
- `alice@demo.local`

Password for all demo users:

```text
demo123
```

## Frontend Rules Matching Backend

- Vacation is not entered directly in timesheet editor
- Manual sick entry is intended for one day only
- Only owner or admin can open the edit form for a draft or rejected timesheet
- Managers can open detail pages for team members' timesheets but cannot edit them
- Own timesheet cannot be self-approved or self-rejected

## Folder Structure

```text
Frontend/
  src/
    components/
    context/
    layouts/
    pages/
    services/
    utils/
    App.jsx
    main.jsx
    styles.css
  index.html
  package.json
  vite.config.js
```

## Main Frontend Files

- `src/layouts/AppLayout.jsx` - top navigation and app shell
- `src/context/AppContext.jsx` - auth state and current user bootstrap
- `src/services/apiClient.js` - axios client and error handling
- `src/services/*.js` - API service layer
- `src/pages/*` - route screens

## Troubleshooting

### `npm` is not recognized

Install Node.js and reopen VS Code or PowerShell.

### PowerShell blocks `npm.ps1`

Use:

```powershell
npm.cmd run dev -- --host 0.0.0.0
```

or temporarily allow scripts in the current terminal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### `Network Error` on login

Check:

- backend is running
- frontend `.env` points to correct backend URL
- backend CORS is enabled for the current Vite port

### Vite starts on `5174` instead of `5173`

That is fine. Just open the URL Vite prints in the terminal.
