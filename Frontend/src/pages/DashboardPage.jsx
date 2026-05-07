import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import managerService from "../services/managerService";
import absenceService from "../services/absenceService";
import timesheetService from "../services/timesheetService";
import {
  EmptyState,
  ErrorMessage,
  PageHeader,
  Panel,
  StatCard,
  StatusPill
} from "../components/ui/Feedback";
import { formatDateRange, formatHours, statusTone } from "../utils/formatters";

export default function DashboardPage() {
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    overview: null,
    timesheets: [],
    absences: []
  });

  useEffect(() => {
    let active = true;

    async function loadDashboard() {
      setState((current) => ({ ...current, loading: true, error: "" }));
      try {
        const requests = [
          timesheetService.list(),
          absenceService.list()
        ];

        if (currentUser.role === "MANAGER" || currentUser.role === "ADMIN") {
          requests.unshift(managerService.getTeamOverview());
        } else {
          requests.unshift(Promise.resolve(null));
        }

        const [overview, timesheets, absences] = await Promise.all(requests);

        if (active) {
          setState({
            loading: false,
            error: "",
            overview,
            timesheets: timesheets.slice(0, 5),
            absences: absences.slice(0, 5)
          });
        }
      } catch (error) {
        if (active) {
          setState((current) => ({
            ...current,
            loading: false,
            error: error.message
          }));
        }
      }
    }

    loadDashboard();
    return () => {
      active = false;
    };
  }, [currentUser.role]);

  if (state.error) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader
        title="Dashboard"
        description="Quick overview of timesheets, absences and manager approval workload."
        action={
          <Link className="primary-button" to="/timesheets/new">
            New timesheet
          </Link>
        }
      />

      <div className="stats-grid">
        <StatCard label="Current role" value={currentUser.role} tone="accent" />
        <StatCard label="Recent timesheets" value={state.timesheets.length} />
        <StatCard label="Recent absences" value={state.absences.length} />
        <StatCard
          label="Pending approvals"
          value={
            state.overview
              ? state.overview.pending_timesheets + state.overview.pending_absences
              : 0
          }
          tone="warning"
        />
      </div>

      {state.overview ? (
        <Panel title="Manager overview">
          <div className="stats-grid">
            {Object.entries(state.overview).map(([key, value]) => (
              <StatCard key={key} label={key.replaceAll("_", " ")} value={String(value)} />
            ))}
          </div>
        </Panel>
      ) : null}

      <Panel title="Latest timesheets">
        {state.timesheets.length ? (
          <div className="stack-md">
            {state.timesheets.map((timesheet) => (
              <Link key={timesheet.id} className="list-row" to={`/timesheets/${timesheet.id}`}>
                <div>
                  <strong>
                    {timesheet.user_name || `User #${timesheet.user_id}`} | {timesheet.month}/{timesheet.year}
                  </strong>
                  <p className="muted-text">
                    {timesheet.days.length} entries, {formatHours(timesheet.days.reduce((sum, day) => sum + day.hours, 0))}
                  </p>
                </div>
                <StatusPill tone={statusTone(timesheet.status)}>{timesheet.status}</StatusPill>
              </Link>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No timesheets yet"
            description="Create the first monthly timesheet entry."
            actionLabel="Create timesheet"
            actionTo="/timesheets/new"
          />
        )}
      </Panel>

      <Panel title="Latest absences">
        {state.absences.length ? (
          <div className="stack-md">
            {state.absences.map((absence) => (
              <div key={absence.id} className="list-row">
                <div>
                  <strong>{absence.type}</strong>
                  <p className="muted-text">{formatDateRange(absence.date_from, absence.date_to)}</p>
                </div>
                <StatusPill tone={statusTone(absence.status)}>{absence.status}</StatusPill>
              </div>
            ))}
          </div>
        ) : (
          <EmptyState
            title="No absences recorded"
            description="Absence requests will appear here after creation."
            actionLabel="Create absence"
            actionTo="/absences/new"
          />
        )}
      </Panel>
    </>
  );
}
