import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import timesheetService from "../services/timesheetService";
import {
  ErrorMessage,
  LoadingState,
  PageHeader,
  Panel,
  StatusPill
} from "../components/ui/Feedback";
import { formatHours, statusTone } from "../utils/formatters";

export default function TimesheetsListPage() {
  const [filters, setFilters] = useState({
    month: "",
    year: ""
  });
  const [state, setState] = useState({
    loading: true,
    error: "",
    items: []
  });

  useEffect(() => {
    let active = true;

    async function loadTimesheets() {
      setState((current) => ({ ...current, loading: true, error: "" }));
      try {
        const params = {};
        if (filters.month) {
          params.month = Number(filters.month);
        }
        if (filters.year) {
          params.year = Number(filters.year);
        }
        const items = await timesheetService.list(params);
        if (active) {
          setState({
            loading: false,
            error: "",
            items
          });
        }
      } catch (error) {
        if (active) {
          setState({
            loading: false,
            error: error.message,
            items: []
          });
        }
      }
    }

    loadTimesheets();
    return () => {
      active = false;
    };
  }, [filters.month, filters.year]);

  if (state.loading) {
    return <LoadingState label="Loading timesheets..." />;
  }

  if (state.error) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader
        title="Timesheets list"
        description="Monthly records fetched from GET /timesheets with simple filtering."
        action={
          <Link className="primary-button" to="/timesheets/new">
            Create timesheet
          </Link>
        }
      />

      <Panel title="Filters">
        <div className="form-grid two-columns">
          <label>
            <span>Month</span>
            <input
              type="number"
              min="1"
              max="12"
              value={filters.month}
              onChange={(event) => setFilters((current) => ({ ...current, month: event.target.value }))}
            />
          </label>
          <label>
            <span>Year</span>
            <input
              type="number"
              min="2024"
              max="2100"
              value={filters.year}
              onChange={(event) => setFilters((current) => ({ ...current, year: event.target.value }))}
            />
          </label>
        </div>
      </Panel>

      <Panel title="Timesheets">
        <div className="table-wrapper">
          <table className="data-table">
            <thead>
              <tr>
                <th>ID</th>
                <th>Requested by</th>
                <th>Period</th>
                <th>Status</th>
                <th>Total</th>
                <th>Entries</th>
                <th />
              </tr>
            </thead>
            <tbody>
              {state.items.map((timesheet) => {
                const total = timesheet.days.reduce((sum, day) => sum + day.hours, 0);
                return (
                  <tr key={timesheet.id}>
                    <td>{timesheet.id}</td>
                    <td>{timesheet.user_name || `User #${timesheet.user_id}`}</td>
                    <td>
                      {timesheet.month}/{timesheet.year}
                    </td>
                    <td>
                      <StatusPill tone={statusTone(timesheet.status)}>{timesheet.status}</StatusPill>
                    </td>
                    <td>{formatHours(total)}</td>
                    <td>{timesheet.days.length}</td>
                    <td>
                      <Link className="ghost-button" to={`/timesheets/${timesheet.id}`}>
                        Detail
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </Panel>
    </>
  );
}
