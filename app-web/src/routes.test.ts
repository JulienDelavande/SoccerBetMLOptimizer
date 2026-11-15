import { afterAll, describe, expect, it } from "vitest";
import { setLang } from "./i18n";
import { routeTitle } from "./routes";

describe("routeTitle", () => {
  afterAll(() => setLang("fr"));
  it("names every route, day links as Today", () => {
    setLang("fr");
    expect(routeTitle("/")).toBe("Aujourd'hui · OptiBet");
    expect(routeTitle("/jour/2026-11-12")).toBe("Aujourd'hui · OptiBet");
    expect(routeTitle("/historique")).toBe("Historique · OptiBet");
    expect(routeTitle("/methode")).toBe("Méthode · OptiBet");
    expect(routeTitle("/match/abc")).toBe("Match · OptiBet");
    expect(routeTitle("/nope")).toBe("Aujourd'hui · OptiBet");
  });

  it("follows the language", () => {
    setLang("en");
    expect(routeTitle("/historique")).toBe("History · OptiBet");
    expect(routeTitle("/compte")).toBe("Account · OptiBet");
  });
});
