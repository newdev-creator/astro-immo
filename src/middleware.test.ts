import { describe, expect, it } from "vitest";

import { parseJWT } from "./lib/jwt";

function buildToken(payload: Record<string, unknown>) {
  const header = Buffer.from(JSON.stringify({ alg: "HS256", typ: "JWT" })).toString(
    "base64url",
  );
  const body = Buffer.from(JSON.stringify(payload)).toString("base64url");
  return `${header}.${body}.signature`;
}

describe("parseJWT", () => {
  it("returns payload for valid token format", () => {
    const token = buildToken({ sub: 7, role: "agent", nom: "Julien" });
    const payload = parseJWT(token);

    expect(payload).toEqual({ sub: 7, role: "agent", nom: "Julien" });
  });

  it("returns null for malformed tokens", () => {
    expect(parseJWT("invalid-token")).toBeNull();
  });
});
