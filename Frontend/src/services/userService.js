import apiClient, { getApiErrorMessage } from "./apiClient";

async function request(promise) {
  try {
    const { data } = await promise;
    return data;
  } catch (error) {
    throw new Error(getApiErrorMessage(error));
  }
}

const userService = {
  list() {
    return request(apiClient.get("/users"));
  },
  create(payload) {
    return request(apiClient.post("/users", payload));
  },
  update(userId, payload) {
    return request(apiClient.patch(`/users/${userId}`, payload));
  },
  deactivate(userId) {
    return request(apiClient.delete(`/users/${userId}`));
  }
};

export default userService;
