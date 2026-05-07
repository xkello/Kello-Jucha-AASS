import { useMemo, useState } from "react";
import { formatDateInput } from "../utils/formatters";

const dayTypes = ["WORK", "SICK"];

function createRow(date = "", hours = 8, day_type = "WORK") {
  return {
    id: crypto.randomUUID(),
    date,
    hours,
    day_type
  };
}

export default function TimesheetEditorForm({
  initialMonth,
  initialYear,
  initialEntries = [],
  submitLabel,
  onSubmit,
  submitting
}) {
  const [month, setMonth] = useState(initialMonth || new Date().getMonth() + 1);
  const [year, setYear] = useState(initialYear || new Date().getFullYear());
  const [entries, setEntries] = useState(
    initialEntries.length
      ? initialEntries.map((entry) => ({ ...entry, id: crypto.randomUUID() }))
      : [createRow(formatDateInput(new Date()))]
  );

  const totalHours = useMemo(
    () => entries.reduce((sum, entry) => sum + Number(entry.hours || 0), 0),
    [entries]
  );

  function updateEntry(id, field, value) {
    setEntries((current) =>
      current.map((entry) => (entry.id === id ? { ...entry, [field]: value } : entry))
    );
  }

  function addRow() {
    setEntries((current) => [...current, createRow()]);
  }

  function removeRow(id) {
    setEntries((current) => current.filter((entry) => entry.id !== id));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const payload = entries
      .filter((entry) => entry.date)
      .map(({ date, hours, day_type }) => ({
        date,
        hours: Number(hours),
        day_type
      }));

    await onSubmit({
      month: Number(month),
      year: Number(year),
      entries: payload
    });
  }

  return (
    <form className="stack-lg" onSubmit={handleSubmit}>
      <div className="form-grid two-columns">
        <label>
          <span>Month</span>
          <input
            type="number"
            min="1"
            max="12"
            value={month}
            onChange={(event) => setMonth(event.target.value)}
            required
          />
        </label>
        <label>
          <span>Year</span>
          <input
            type="number"
            min="2024"
            max="2100"
            value={year}
            onChange={(event) => setYear(event.target.value)}
            required
          />
        </label>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Hours</th>
              <th>Day type</th>
              <th />
            </tr>
          </thead>
          <tbody>
            {entries.map((entry) => (
              <tr key={entry.id}>
                <td>
                  <input
                    type="date"
                    value={entry.date}
                    onChange={(event) => updateEntry(entry.id, "date", event.target.value)}
                    required
                  />
                </td>
                <td>
                  <input
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    value={entry.hours}
                    onChange={(event) => updateEntry(entry.id, "hours", event.target.value)}
                    required
                  />
                </td>
                <td>
                  <select
                    value={entry.day_type}
                    onChange={(event) => updateEntry(entry.id, "day_type", event.target.value)}
                  >
                    {dayTypes.map((type) => (
                      <option key={type} value={type}>
                        {type}
                      </option>
                    ))}
                  </select>
                </td>
                <td>
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={() => removeRow(entry.id)}
                    disabled={entries.length === 1}
                  >
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="inline-actions">
        <button type="button" className="secondary-button" onClick={addRow}>
          Add day
        </button>
        <span className="muted-text">Current total: {totalHours.toFixed(1)} h</span>
      </div>

      <p className="muted-text">
        Vacation should be requested through the absence module. A direct sick day in the timesheet is allowed for one day only.
      </p>

      <button className="primary-button" type="submit" disabled={submitting}>
        {submitting ? "Saving..." : submitLabel}
      </button>
    </form>
  );
}
