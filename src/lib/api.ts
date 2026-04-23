const API_BASE = "http://localhost:8000";

export function apiFetch(
  path: string,
  request: Request,
  options: RequestInit = {},
) {
  const allCookies = request.headers.get("cookie") ?? "";
  const accessToken =
    allCookies
      .split(";")
      .find((c) => c.trim().startsWith("access_token="))
      ?.trim() ?? "";

  return fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      cookie: accessToken,
      ...(options.headers ?? {}),
    },
  });
}
