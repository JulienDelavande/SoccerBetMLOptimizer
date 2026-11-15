import { describe, expect, it } from "vitest";
import { initials } from "./logos";

describe("initials", () => {
  it("takes the first letters of the first two words", () => {
    expect(initials("Paris Saint-Germain")).toBe("PS");
    expect(initials("Lens")).toBe("L");
  });

  it("drops club prefixes, numbers, symbols and particles", () => {
    expect(initials("1. FC Heidenheim 1846")).toBe("H");
    expect(initials("TSG 1899 Hoffenheim")).toBe("H");
    expect(initials("Brighton & Hove Albion")).toBe("BH");
    expect(initials("Estudiantes de La Plata")).toBe("EP");
    expect(initials("Bodø/Glimt")).toBe("BG");
  });

  it("never returns an empty monogram", () => {
    expect(initials("1860")).toBe("18");
    expect(initials("")).toBe("");
  });
});
