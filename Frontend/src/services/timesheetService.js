import apiClient, { getApiErrorMessage } from "./apiClient";

async function request(promise) {
  try {
    const { data } = await promise;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

const timesheetService = {
  list(params = {}) {
    return request(apiClient.get("/timesheets", { params }));
  },
  async getById(timesheetId) {
    const items = await this.list();
    const item = items.find((timesheet) => String(timesheet.id) === String(timesheetId));
    if (!item) {
      throw new Error("Timesheet not found.");
    }
    return item;
  },
  saveMonth(year, month, entries) {
    return request(apiClient.post(`/timesheets/${year}/${month}/days`, entries));
  },
  updateDay(timesheetId, date, payload) {
    return request(apiClient.patch(`/timesheets/${timesheetId}/days/${date}`, payload));
  },
  submit(timesheetId) {
    return request(apiClient.post(`/timesheets/${timesheetId}/submit`));
  },
  approve(timesheetId) {
    return request(apiClient.post(`/timesheets/${timesheetId}/approve`));
  },
  reject(timesheetId, comment) {
    return request(apiClient.post(`/timesheets/${timesheetId}/reject`, { comment }));
  },
  unlock(timesheetId, reason) {
    return request(apiClient.post(`/timesheets/${timesheetId}/unlock`, { reason }));
  }
};

export default timesheetService;
