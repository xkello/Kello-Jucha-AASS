import { useState } from "react";
import { useNavigate } from "react-router-dom";
import TimesheetEditorForm from "../components/TimesheetEditorForm";
import { ErrorMessage, PageHeader, Panel } from "../components/ui/Feedback";
import timesheetService from "../services/timesheetService";

export default function CreateTimesheetPage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate({ month, year, entries }) {
    setSubmitting(true);
    setError("");
    try {
      const saved = await timesheetService.saveMonth(year, month, entries);
      navigate(`/timesheets/${saved.id}`);
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Create timesheet"
        description="Creates or updates the selected month through POST /timesheets/{year}/{month}/days."
      />
      <Panel title="Entry form">
        {error ? <ErrorMessage message={error} /> : null}
        <TimesheetEditorForm submitLabel="Save timesheet" onSubmit={handleCreate} submitting={submitting} />
      </Panel>
    </>
  );
}
