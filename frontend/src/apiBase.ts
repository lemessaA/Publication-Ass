/**
 * Resolved API root for fetch calls. VITE_API_BASE_URL must end up as …/api/v1
 * (same prefix as FastAPI's router). A common misconfiguration is setting only
 * the Render hostname, which yields GET /history → 404 instead of /api/v1/history.
 */
export function resolvedApiBaseUrl(): string {
  const fallback = "http://localhost:8000/api/v1";
  const raw = (import.meta.env.VITE_API_BASE_URL ?? "").trim();
  if (!raw) {
    return fallback;
  }
  let u = raw.replace(/\/+$/, "");
  if (/\/api\/v1$/i.test(u)) {
    return u;
  }
  if (/\/api$/i.test(u)) {
    return `${u}/v1`;
  }
  return `${u}/api/v1`;
}
