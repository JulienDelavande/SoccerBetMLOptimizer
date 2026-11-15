import { describe, expect, it } from "vitest";
import { BEVEL_DEPTH, BULGE, DEFAULT_POSE, ballMesh, ballSvg, norm, panels, pose, radius, type Vec3 } from "./geometry";

const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dist = (a: Vec3, b: Vec3) => Math.hypot(...sub(a, b));

describe("truncated icosahedron panels", () => {
  const ps = panels();

  it("has 12 pentagons and 20 hexagons", () => {
    expect(ps.filter((p) => p.kind === "pent" && p.corners.length === 5)).toHaveLength(12);
    expect(ps.filter((p) => p.kind === "hex" && p.corners.length === 6)).toHaveLength(20);
  });

  it("has 60 distinct corners, each shared by exactly three panels", () => {
    const key = (v: Vec3) => v.map((x) => x.toFixed(5)).join(",");
    const seen = new Map<string, number>();
    ps.forEach((p) => p.corners.forEach((c) => seen.set(key(c), (seen.get(key(c)) ?? 0) + 1)));
    expect(seen.size).toBe(60);
    expect([...seen.values()].every((n) => n === 3)).toBe(true);
  });

  it("has regular panels: all edges about the same length", () => {
    const edges = ps.flatMap((p) => p.corners.map((c, i) => dist(c, p.corners[(i + 1) % p.corners.length])));
    const lo = Math.min(...edges), hi = Math.max(...edges);
    expect(hi / lo).toBeLessThan(1.15);   // corners are on the sphere, so not exactly equal, but close
  });

  it("winds every panel counter-clockwise seen from outside", () => {
    for (const p of ps) {
      const n = cross(sub(p.corners[1], p.corners[0]), sub(p.corners[2], p.corners[0]));
      expect(dot(n, p.centre)).toBeGreaterThan(0);
    }
  });

  it("puts a pentagon on the spin axis and flags the ten equator hexagons as accent", () => {
    expect(ps.some((p) => p.kind === "pent" && p.centre[1] > 0.9999)).toBe(true);
    const accents = ps.filter((p) => p.accent);
    expect(accents).toHaveLength(10);
    expect(accents.every((p) => p.kind === "hex")).toBe(true);
  });
});

describe("panel profile", () => {
  it("bulges at the centre and dips into the seam", () => {
    expect(radius(0)).toBeCloseTo(1 + BULGE);
    expect(radius(1)).toBeCloseTo(1 - BEVEL_DEPTH);
    for (let s = 0; s < 1; s += 0.05) expect(radius(s + 0.05)).toBeLessThanOrEqual(radius(s) + 1e-9);
  });
});

describe("ballMesh", () => {
  const m = ballMesh(5);

  it("returns matching buffers with in-range indices", () => {
    const n = m.positions.length / 3;
    expect(m.colors.length).toBe(m.positions.length);
    expect(m.indices.length % 3).toBe(0);
    expect(Math.max(...m.indices)).toBeLessThan(n);
  });

  it("keeps every vertex near the unit sphere", () => {
    for (let i = 0; i < m.positions.length; i += 3) {
      const r = Math.hypot(m.positions[i], m.positions[i + 1], m.positions[i + 2]);
      expect(r).toBeGreaterThan(1 - BEVEL_DEPTH - 1e-6);
      expect(r).toBeLessThan(1 + BULGE + 1e-6);
    }
  });

  it("keeps the tomato accent to a small share of the surface", () => {
    let tomato = 0;
    for (let i = 0; i < m.colors.length; i += 3) if (m.colors[i] > 0.9 && m.colors[i + 1] < 0.4) tomato++;
    const share = tomato / (m.colors.length / 3);
    expect(share).toBeGreaterThan(0.02);
    expect(share).toBeLessThan(0.12);
  });
});

describe("pose and poster", () => {
  it("rotations keep vectors unit length", () => {
    const v = pose(norm([0.3, 0.5, -0.8]), DEFAULT_POSE);
    expect(Math.hypot(...v)).toBeCloseTo(1);
  });

  it("draws the visible panels as an SVG with a seam background", () => {
    const svg = ballSvg();
    const polys = svg.match(/<polygon/g)?.length ?? 0;
    expect(svg.startsWith("<svg")).toBe(true);
    expect(polys).toBeGreaterThan(14);           // about half the 32 panels, plus accent stripes
    expect(svg).toContain("#355e3b");
    expect(svg).not.toMatch(/NaN/);
  });
});
