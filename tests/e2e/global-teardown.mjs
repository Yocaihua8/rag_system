const port = process.env.KI_E2E_PORT || "18765";
const baseURL = process.env.KI_E2E_BASE_URL || `http://127.0.0.1:${port}`;

export default async function globalTeardown() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    await fetch(`${baseURL}/__e2e__/shutdown`, {
      method: "POST",
      signal: controller.signal,
    });
  } catch {
    // The server may already be gone or be an explicitly reused non-E2E server.
  } finally {
    clearTimeout(timeout);
  }
}
