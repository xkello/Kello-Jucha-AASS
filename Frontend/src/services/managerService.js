import apiClient, { getApiErrorMessage } from "./apiClient";

async function request(promise) {
  try {
    const { data } = await promise;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

const managerService = {
  getPendingTimesheets() {
    return request(apiClient.get("/manager/pending-timesheets"));
  },
  getPendingAbsences() {
    return request(apiClient.get("/manager/pending-absences"));
  },
  getTeamOverview() {
    return request(apiClient.get("/manager/team-overview"));
  }
};

export default managerService;
