import apiClient, { getApiErrorMessage } from "./apiClient";

async function request(promise) {
  try {
    const { data } = await promise;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

const absenceService = {
  list() {
    return request(apiClient.get("/absences"));
  },
  create(payload) {
    return request(apiClient.post("/absences", payload));
  },
  approve(absenceId, comment) {
    return request(apiClient.post(`/absences/${absenceId}/approve`, { comment }));
  },
  reject(absenceId, comment) {
    return request(apiClient.post(`/absences/${absenceId}/reject`, { comment }));
  },
  cancel(absenceId) {
    return request(apiClient.post(`/absences/${absenceId}/cancel`));
  }
};

export default absenceService;
