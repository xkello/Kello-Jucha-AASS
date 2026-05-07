export function formatDate(value) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleDateString("sk-SK");
}

export function formatDateInput(value) {
  const date = new Date(value);
  const year = date.getFullYear();
  const month = `${date.getMonth() + 1}`.padStart(2, "0");
  const day = `${date.getDate()}`.padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function formatDateRange(from, to) {
  return `${formatDate(from)} - ${formatDate(to)}`;
}

export function formatHours(value) {
  return `${Number(value || 0).toFixed(1)} h`;
}

export function statusTone(status) {
  switch (status) {
    case "APPROVED":
      return "success";
    case "SUBMITTED":
    case "REQUESTED":
      return "warning";
    case "REJECTED":
    case "CANCELLED":
      return "danger";
    default:
      return "default";
  }
}
