import { Navigate, Route, Routes } from "react-router-dom";
import { useAppContext } from "./context/AppContext";
import AppLayout from "./layouts/AppLayout";
import {
  ErrorMessage,
  LoadingState
} from "./components/ui/Feedback";
import DashboardPage from "./pages/DashboardPage";
import LoginPage from "./pages/LoginPage";
import TimesheetsListPage from "./pages/TimesheetsListPage";
import CreateTimesheetPage from "./pages/CreateTimesheetPage";
import TimesheetDetailPage from "./pages/TimesheetDetailPage";
import EditTimesheetPage from "./pages/EditTimesheetPage";
import AbsencesListPage from "./pages/AbsencesListPage";
import CreateAbsencePage from "./pages/CreateAbsencePage";
import TeamsOverviewPage from "./pages/TeamsOverviewPage";
import TeamDetailPage from "./pages/TeamDetailPage";
import ManagerPage from "./pages/ManagerPage";
import UsersPage from "./pages/UsersPage";

function ProtectedRoutes() {
  const { currentUser, initializing } = useAppContext();

  if (initializing) {
    return <LoadingState label="Loading application..." />;
  }

  if (!currentUser) {
    return <Navigate to="/login" replace />;
  }

  return (
    <AppLayout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/timesheets" element={<TimesheetsListPage />} />
        <Route path="/timesheets/new" element={<CreateTimesheetPage />} />
        <Route path="/timesheets/:timesheetId" element={<TimesheetDetailPage />} />
        <Route path="/timesheets/:timesheetId/edit" element={<EditTimesheetPage />} />
        <Route path="/absences" element={<AbsencesListPage />} />
        <Route path="/absences/new" element={<CreateAbsencePage />} />
        <Route path="/teams" element={<TeamsOverviewPage />} />
        <Route path="/teams/:teamId" element={<TeamDetailPage />} />
        <Route path="/manager" element={<ManagerPage />} />
        <Route path="/users" element={<UsersPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AppLayout>
  );
}

export default function App() {
  const { bootError } = useAppContext();

  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/*" element={<ProtectedRoutes />} />
      {bootError ? <Route path="/boot-error" element={<ErrorMessage message={bootError} />} /> : null}
    </Routes>
  );
}
