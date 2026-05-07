import { useEffect, useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useAppContext } from "../context/AppContext";
import TimesheetEditorForm from "../components/TimesheetEditorForm";
import { ErrorMessage, LoadingState, PageHeader, Panel } from "../components/ui/Feedback";
import timesheetService from "../services/timesheetService";

export default function EditTimesheetPage() {
  const { timesheetId } = useParams();
  const navigate = useNavigate();
  const { currentUser } = useAppContext();
  const [state, setState] = useState({
    loading: true,
    error: "",
    timesheet: null
  });
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let active = true;

    async function loadTimesheet() {
      try {
        const timesheet = await timesheetService.getById(timesheetId);
        const canEditTimesheet =
          ["DRAFT", "REJECTED"].includes(timesheet.status) &&
          (currentUser.id === timesheet.user_id || currentUser.role === "ADMIN");

        if (!canEditTimesheet) {
          throw new Error("You can only edit your own draft or rejected timesheets.");
        }

        if (active) {
          setState({
            loading: false,
            error: "",
            timesheet
          });
        }
      } catch (error) {
        if (active) {
          setState({
            loading: false,
            error: error.message,
            timesheet: null
          });
        }
      }
    }

    loadTimesheet();
    return () => {
      active = false;
    };
  }, [currentUser.id, currentUser.role, timesheetId]);

  async function handleSave({ month, year, entries }) {
    setSubmitting(true);
    try {
      const updated = await timesheetService.saveMonth(year, month, entries);
      navigate(`/timesheets/${updated.id}`);
    } catch (error) {
      setState((current) => ({ ...current, error: error.message }));
    } finally {
      setSubmitting(false);
    }
  }

  if (state.loading) {
    return <LoadingState label="Loading timesheet..." />;
  }

  if (state.error && !state.timesheet) {
    return <ErrorMessage message={state.error} />;
  }

  return (
    <>
      <PageHeader title={`Edit timesheet #${timesheetId}`} description="Update the day entries for the selected month." />
      <Panel title="Edit form">
        {state.error ? <ErrorMessage message={state.error} /> : null}
        <TimesheetEditorForm
          initialMonth={state.timesheet.month}
          initialYear={state.timesheet.year}
          initialEntries={state.timesheet.days}
          submitLabel="Update timesheet"
          onSubmit={handleSave}
          submitting={submitting}
        />
      </Panel>
    </>
  );
}
