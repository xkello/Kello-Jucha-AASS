import { useState } from "react";
import { useNavigate } from "react-router-dom";
import AbsenceRequestForm from "../components/AbsenceRequestForm";
import { ErrorMessage, PageHeader, Panel } from "../components/ui/Feedback";
import absenceService from "../services/absenceService";

export default function CreateAbsencePage() {
  const navigate = useNavigate();
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleCreate(payload) {
    setSubmitting(true);
    setError("");
    try {
      await absenceService.create(payload);
      navigate("/absences");
    } catch (apiError) {
      setError(apiError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <>
      <PageHeader
        title="Create absence"
        description="Request vacation or sick leave through POST /absences."
      />
      <Panel title="Absence form">
        {error ? <ErrorMessage message={error} /> : null}
        <AbsenceRequestForm onSubmit={handleCreate} submitting={submitting} />
      </Panel>
    </>
  );
}
