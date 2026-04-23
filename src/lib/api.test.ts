import { afterEach, describe, expect, it, vi } from "vitest";

import { apiFetch } from "./api";

describe("apiFetch", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("builds relative API URL from current request origin", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}", { status: 200 }));

    const request = new Request("https://example.com/dashboard", {
      headers: { cookie: "access_token=abc123; theme=dark" },
    });

    await apiFetch("/api/biens/publics", request);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("https://example.com/api/biens/publics");
    const headers = init?.headers as Headers;
    expect(headers.get("cookie")).toContain("access_token=abc123");
    expect(headers.get("content-type")).toBe("application/json");
  });

  it("keeps absolute URL untouched", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}", { status: 200 }));
    const request = new Request("https://example.com/dashboard");

    await apiFetch("https://api.example.org/ping", request);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect(fetchMock.mock.calls[0][0]).toBe("https://api.example.org/ping");
  });

  it("does not force JSON content-type on FormData uploads", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(new Response("{}", { status: 200 }));
    const request = new Request("https://example.com/dashboard");
    const body = new FormData();
    body.append("file", new Blob(["a"]), "a.txt");

    await apiFetch("/api/upload", request, { method: "POST", body });

    const headers = fetchMock.mock.calls[0][1]?.headers as Headers;
    expect(headers.get("content-type")).toBeNull();
  });
});
