function getApiBase(request: Request): string {
  const envBase = ((import.meta as any).env?.API_BASE_URL as
    | string
    | undefined)?.trim();
  if (envBase) return envBase;

  return new URL(request.url).origin;
}

export function apiFetch(
  path: string,
  request: Request,
  options: RequestInit = {},
) {
  const allCookies = request.headers.get("cookie") ?? "";
  const base = getApiBase(request);
  const targetUrl = /^https?:\/\//i.test(path)
    ? path
    : new URL(path, base).toString();

  const headers = new Headers(options.headers);
  if (!headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (allCookies && !headers.has("cookie")) {
    headers.set("cookie", allCookies);
  }

  return fetch(targetUrl, {
    ...options,
    headers,
  });
}
