import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import managerService from "../services/managerService";
import {
  EmptyState,
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatCard
} from "../components/ui/Feedback";
import { formatDateRange } from "../utils/formatters";

export default function ManagerPage() {
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    overview: null,
    pendingTimesheets: [],
    pendingAbsences: []
  });

  useEffect(() => {
    if (!["MANAGER", "ADMIN"].includes(currentUser.role)) {
      setState({
        loading: false,
        error: "",
        overview: null,
        pendingTimesheets: [],
        pendingAbsences: []
      });
      return;
    }

    let active = true;

    async function loadManagerData() {
      try {
        const [overview, pendingTimesheets, pendingAbsences] = await Promise.all([
          managerService.getTeamOverview(),
          managerService.getPendingTimesheets(),
          managerService.getPendingAbsences()
        ]);
        if (active) {
          setState({
            loading: false,
            error: "",
            overview,
            pendingTimesheets,
            pendingAbsences
          });
        }
      } catch (error) {
        if (active) {
          setState({
            loading: false,
            error: error.message,
            overview: null,
            pendingTimesheets: [],
            pendingAbsences: []
          });
        }
      }
    }

    loadManagerData();
    return () => {
      active = false;
    };
  }, [currentUser.role]);

  if (!["MANAGER", "ADMIN"].includes(currentUser.role)) {
    return (
      <EmptyState
        title="Manager view unavailable"
        description="This page is intended for manager and admin roles."
        actionLabel="Go to dashboard"
        actionTo="/"
      />
    );
  }

  if (state.loading) {
    return <LoadingState label="Loading manager overview..." />;
  }

  if (state.error) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader title="Manager approvals" description="Pending approvals from the dedicated /manager endpoints." />

      <div className="stats-grid">
        {Object.entries(state.overview || {}).map(([key, value]) => (
          <StatCard key={key} label={key.replaceAll("_", " ")} value={String(value)} />
        ))}
      </div>

      <Panel title="Pending timesheets">
        <div className="stack-md">
          {state.pendingTimesheets.map((item) => (
            <Link className="list-row" key={item.id} to={`/timesheets/${item.id}`}>
              <div>
                <strong>{item.user_name}</strong>
                <p className="muted-text">
                  {item.month}/{item.year}
                </p>
              </div>
              <span className="ghost-button">Open</span>
            </Link>
          ))}
        </div>
      </Panel>

      <Panel title="Pending absences">
        <div className="stack-md">
          {state.pendingAbsences.map((item) => (
            <div className="list-row" key={item.id}>
              <div>
                <strong>{item.user_name}</strong>
                <p className="muted-text">
                  {item.type} | {formatDateRange(item.date_from, item.date_to)}
                </p>
              </div>
              <Link className="ghost-button" to="/absences">
                Review
              </Link>
            </div>
          ))}
        </div>
      </Panel>
    </>
  );
}
