import apiClient, { getApiErrorMessage } from "./apiClient";

const authService = {
  async login(credentials) {
    try {
      const { data } = await apiClient.post("/auth/login", credentials);
      return data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  },

  async getMe() {
    try {
      const { data } = await apiClient.get("/auth/me");
      return data;
    } catch (error) {
      throw new Error(getApiErrorMessage(error));
    }
  }
};

export default authService;
