import axios from "axios";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error.response?.status;
    const url: string = error.config?.url || "";
    const isAuthRoute =
      url.includes("/login") ||
      url.includes("/forgot-password") ||
      url.includes("/reset-password");

    if (status === 401 && !isAuthRoute && localStorage.getItem("token")) {
      localStorage.removeItem("token");
      window.location.reload();
    }

    return Promise.reject(error);
  }
);

export default api;