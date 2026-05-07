import { useState } from "react";
import { formatDateInput } from "../utils/formatters";

const absenceTypes = ["VACATION", "SICK"];

export default function AbsenceRequestForm({ onSubmit, submitting }) {
  const today = formatDateInput(new Date());
  const [form, setForm] = useState({
    type: "VACATION",
    date_from: today,
    date_to: today,
    comment: ""
  });

  function updateField(field, value) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    await onSubmit(form);
  }

  return (
    <form className="stack-lg" onSubmit={handleSubmit}>
      <div className="form-grid two-columns">
        <label>
          <span>Type</span>
          <select value={form.type} onChange={(event) => updateField("type", event.target.value)}>
            {absenceTypes.map((type) => (
              <option key={type} value={type}>
                {type}
              </option>
            ))}
          </select>
        </label>
        <label>
          <span>From</span>
          <input
            type="date"
            value={form.date_from}
            onChange={(event) => updateField("date_from", event.target.value)}
            required
          />
        </label>
        <label>
          <span>To</span>
          <input
            type="date"
            value={form.date_to}
            onChange={(event) => updateField("date_to", event.target.value)}
            required
          />
        </label>
      </div>

      <label>
        <span>Comment</span>
        <textarea
          rows="4"
          value={form.comment}
          onChange={(event) => updateField("comment", event.target.value)}
          placeholder="Optional note for the manager"
        />
      </label>

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Submitting..." : "Request absence"}
      </button>
    </form>
  );
}
