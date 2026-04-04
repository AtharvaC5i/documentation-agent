import axios from "axios";

const client = axios.create({
  baseURL: "/api-proxy",
  timeout: 300_000, // 5 min — context build + generation can be slow
  headers: { "Content-Type": "application/json" },
});

client.interceptors.response.use(
  (res) => res,
  (err) => {
    const detail = err.response?.data?.detail ?? err.message ?? "Unknown error";
    return Promise.reject(new Error(detail));
  },
);

export default client;
