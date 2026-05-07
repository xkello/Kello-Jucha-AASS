import apiClient, { getApiErrorMessage } from "./apiClient";

async function request(promise) {
  try {
    const { data } = await promise;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

const teamService = {
  list() {
    return request(apiClient.get("/teams"));
  },
  create(payload) {
    return request(apiClient.post("/teams", payload));
  },
  update(teamId, payload) {
    return request(apiClient.patch(`/teams/${teamId}`, payload));
  },
  addMember(teamId, user_id) {
    return request(apiClient.post(`/teams/${teamId}/members`, { user_id }));
  },
  removeMember(teamId, userId) {
    return request(apiClient.delete(`/teams/${teamId}/members/${userId}`));
  }
};

export default teamService;
