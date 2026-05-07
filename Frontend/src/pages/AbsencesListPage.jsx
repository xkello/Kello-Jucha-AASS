import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import absenceService from "../services/absenceService";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatusPill
} from "../components/ui/Feedback";
import { formatDateRange, statusTone } from "../utils/formatters";

export default function AbsencesListPage() {
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    items: []
  });
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    loadAbsences();
  }, []);

  async function loadAbsences() {
    setState((current) => ({ ...current, loading: true, error: "" }));
    try {
      const items = await absenceService.list();
      setState({
        loading: false,
        error: "",
        items
      });
    } catch (error) {
      setState({
        loading: false,
        error: error.message,
        items: []
      });
    }
  }

  async function handleAction(absenceId, action) {
    setActionLoading(true);
    try {
      if (action === "approve") {
        await absenceService.approve(absenceId, "Approved in frontend");
      }
      if (action === "reject") {
        const comment = window.prompt("Rejection comment", "Missing details");
        await absenceService.reject(absenceId, comment || "");
      }
      if (action === "cancel") {
        await absenceService.cancel(absenceId);
      }
      await loadAbsences();
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    } finally {
      setActionLoading(false);
    }
  }

  if (state.loading) {
    return <LoadingState label="Loading absences..." />;
  }

  if (state.error && !state.items.length) {
    return <ErrorMessage message={state.error} />;
  }

  const canApprove = ["MANAGER", "ADMIN"].includes(currentUser.role);

  return (
    <>
      <PageHeader
        title="Absences list"
        description="Absence requests, approvals and cancellations from GET /absences."
        action={
          <Link className="primary-button" to="/absences/new">
            Create absence
          </Link>
        }
      />

      {state.error ? <ErrorMessage message={state.error} /> : null}

      <Panel title="Absence requests">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Type</th>
                <th>Date range</th>
                <th>Status</th>
                <th>Comment</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {state.items.map((absence) => (
                <tr key={absence.id}>
                  <td>{absence.id}</td>
                  <td>{absence.type}</td>
                  <td>{formatDateRange(absence.date_from, absence.date_to)}</td>
                  <td>
                    <StatusPill tone={statusTone(absence.status)}>{absence.status}</StatusPill>
                  </td>
                  <td>{absence.comment || "-"}</td>
                  <td>
                    <div className="inline-actions">
                      {canApprove && absence.status === "REQUESTED" ? (
                        <>
                          <button className="ghost-button" onClick={() => handleAction(absence.id, "approve")} disabled={actionLoading}>
                            Approve
                          </button>
                          <button className="ghost-button" onClick={() => handleAction(absence.id, "reject")} disabled={actionLoading}>
                            Reject
                          </button>
                        </>
                      ) : null}
                      {["REQUESTED", "APPROVED"].includes(absence.status) ? (
                        <button className="ghost-button" onClick={() => handleAction(absence.id, "cancel")} disabled={actionLoading}>
                          Cancel
                        </button>
                      ) : null}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
