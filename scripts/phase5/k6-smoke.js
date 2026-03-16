import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "20s",
  thresholds: {
    http_req_failed: ["rate<0.05"],
    http_req_duration: ["p(95)<1000"],
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export default function () {
  const books = http.get(`${BASE_URL}/books/`, { redirects: 0 });
  check(books, {
    "books endpoint is 200": (r) => r.status === 200,
  });

  const health = http.get(`${BASE_URL}/health/`, { redirects: 0 });
  check(health, {
    "health endpoint is 200": (r) => r.status === 200,
  });

  const metrics = http.get(`${BASE_URL}/metrics/`, { redirects: 0 });
  check(metrics, {
    "metrics endpoint is 200": (r) => r.status === 200,
  });

  sleep(0.2);
}
