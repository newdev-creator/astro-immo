import { defineMiddleware } from "astro:middleware";
import { parseJWT } from "@lib/jwt";

const PROTECTED_ROUTES = ["/dashboard"];
const PATRON_ONLY = ["/dashboard/admin"];

export const onRequest = defineMiddleware((context, next) => {
  const { pathname } = context.url;
  const isProtected = PROTECTED_ROUTES.some((r) => pathname.startsWith(r));

  if (!isProtected) return next();

  const token = context.cookies.get("access_token")?.value;
  if (!token) return context.redirect("/login");

  const payload = parseJWT(token);
  if (!payload || (payload.exp as number) < Date.now() / 1000) {
    return context.redirect("/login");
  }

  const isPatronOnly = PATRON_ONLY.some((r) => pathname.startsWith(r));
  if (isPatronOnly && payload.role !== "patron") {
    return context.redirect("/dashboard");
  }

  context.locals.user = {
    id: payload.sub,
    nom: payload.nom,
    role: payload.role,
  };

  return next();
});
