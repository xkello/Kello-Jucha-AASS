import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatCard,
  StatusPill
} from "../components/ui/Feedback";
import timesheetService from "../services/timesheetService";
import { formatDate, formatHours, statusTone } from "../utils/formatters";

export default function TimesheetDetailPage() {
  const { timesheetId } = useParams();
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    timesheet: null
  });
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadTimesheet();
  }, [timesheetId]);

  async function loadTimesheet() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const timesheet = await timesheetService.getById(timesheetId);
      setState({
        loading: false,
        error: "",
        timesheet
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        timesheet: null
      });
    }
  }

  async function handleAction(action) {
    setActionLoading(true);
    try {
      if (action === "submit") {
        await timesheetService.submit(timesheetId);
      }
      if (action === "approve") {
        await timesheetService.approve(timesheetId);
      }
      if (action === "reject") {
        const comment = window.prompt("Rejection comment", "Please adjust the monthly entry.");
        await timesheetService.reject(timesheetId, comment || "");
      }
      if (action === "unlock") {
        const reason = window.prompt("Unlock reason", "Allowed for correction");
        if (!reason) {
          setActionLoading(false);
          return;
        }
        await timesheetService.unlock(timesheetId, reason);
      }
      await loadTimesheet();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    } finally {
      setActionLoading(false);
    }
  }

  if (state.loading) {
    return <LoadingState label="Loading timesheet detail..." />;
  }

  if (state.error && !state.timesheet) {
    return <ErrorMessage message={state.error} />;
  }

  const { timesheet } = state;
  const totalHours = timesheet.days.reduce((sum, day) => sum + day.hours, 0);
  const canManageOwnDraft =
    ["DRAFT", "REJECTED"].includes(timesheet.status) &&
    (currentUser.id === timesheet.user_id || currentUser.role === "ADMIN");
  const canApprove =
    ["MANAGER", "ADMIN"].includes(currentUser.role) &&
    timesheet.status === "SUBMITTED" &&
    currentUser.id !== timesheet.user_id;
  const canUnlock = currentUser.role === "ADMIN" && timesheet.status !== "DRAFT";

  return (
    <>
      <PageHeader
        title={`Timesheet #${timesheet.id}`}
        description={`Detailed monthly record for ${timesheet.month}/${timesheet.year}.`}
        action={
          canManageOwnDraft ? (
            <Link className="primary-button" to={`/timesheets/${timesheet.id}/edit`}>
              Edit timesheet
            </Link>
          ) : null
        }
        secondaryAction={
          <div className="inline-actions">
            {canManageOwnDraft ? (
              <button className="secondary-button" onClick={() => handleAction("submit")} disabled={actionLoading}>
                Submit
              </button>
            ) : null}
            {canApprove ? (
              <>
                <button className="secondary-button" onClick={() => handleAction("approve")} disabled={actionLoading}>
                  Approve
                </button>
                <button className="ghost-button" onClick={() => handleAction("reject")} disabled={actionLoading}>
                  Reject
                </button>
              </>
            ) : null}
            {canUnlock ? (
              <button className="ghost-button" onClick={() => handleAction("unlock")} disabled={actionLoading}>
                Unlock
              </button>
            ) : null}
          </div>
        }
      />

      {state.error ? <ErrorMessage message={state.error} /> : null}

      <div className="stats-grid">
        <StatCard label="Requested by" value={timesheet.user_name || `User #${timesheet.user_id}`} />
        <StatCard label="Status" value={timesheet.status} tone={statusTone(timesheet.status)} />
        <StatCard label="Total hours" value={formatHours(totalHours)} />
        <StatCard label="Entries" value={timesheet.days.length} />
        <StatCard label="Approver" value={timesheet.approver_user_id || "-"} />
      </div>

      <Panel title="Metadata">
        <div className="detail-grid">
          <div>
            <span className="muted-text">Requested by</span>
            <p>{timesheet.user_name || `User #${timesheet.user_id}`}</p>
          </div>
          <div>
            <span className="muted-text">Status</span>
            <div>
              <StatusPill tone={statusTone(timesheet.status)}>{timesheet.status}</StatusPill>
            </div>
          </div>
          <div>
            <span className="muted-text">Submitted at</span>
            <p>{formatDate(timesheet.submitted_at)}</p>
          </div>
          <div>
            <span className="muted-text">Approved at</span>
            <p>{formatDate(timesheet.approved_at)}</p>
          </div>
          <div>
            <span className="muted-text">Rejection comment</span>
            <p>{timesheet.rejection_comment || "-"}</p>
          </div>
        </div>
      </Panel>

      <Panel title="Day entries">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Hours</th>
                <th>Day type</th>
              </tr>
            </thead>
            <tbody>
              {timesheet.days.map((day) => (
                <tr key={day.id}>
                  <td>{formatDate(day.date)}</td>
                  <td>{formatHours(day.hours)}</td>
                  <td>{day.day_type}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
