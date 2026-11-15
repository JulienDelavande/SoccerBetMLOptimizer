// Pure geometry for the hero football: a truncated icosahedron (12 pentagons + 20 hexagons) whose
// panels are inflated onto the sphere with rounded seams. No three.js here, so it is unit-tested and
// shared by the WebGL ball and its static SVG poster.

export type Vec3 = [number, number, number];
export type Kind = "pent" | "hex";
export interface Panel { kind: Kind; centre: Vec3; corners: Vec3[]; accent: boolean }

const PHI = (1 + Math.sqrt(5)) / 2;

const sub = (a: Vec3, b: Vec3): Vec3 => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const dot = (a: Vec3, b: Vec3) => a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
const cross = (a: Vec3, b: Vec3): Vec3 => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const len = (a: Vec3) => Math.hypot(a[0], a[1], a[2]);
export const norm = (a: Vec3): Vec3 => { const l = len(a) || 1; return [a[0] / l, a[1] / l, a[2] / l]; };
const lerp = (a: Vec3, b: Vec3, t: number): Vec3 => [a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t];
const centroid = (ps: Vec3[]) => norm(ps.reduce<Vec3>((s, p) => [s[0] + p[0], s[1] + p[1], s[2] + p[2]], [0, 0, 0]));

export const rotX = (v: Vec3, a: number): Vec3 => [v[0], v[1] * Math.cos(a) - v[2] * Math.sin(a), v[1] * Math.sin(a) + v[2] * Math.cos(a)];
export const rotY = (v: Vec3, a: number): Vec3 => [v[0] * Math.cos(a) + v[2] * Math.sin(a), v[1], -v[0] * Math.sin(a) + v[2] * Math.cos(a)];
export const rotZ = (v: Vec3, a: number): Vec3 => [v[0] * Math.cos(a) - v[1] * Math.sin(a), v[0] * Math.sin(a) + v[1] * Math.cos(a), v[2]];

/** How the ball is shown: spin about its own (pentagon) axis, then the axis tilted toward the camera
 *  and leaned sideways. Same order as the three.js scene graph (outer Euler "ZXY", inner rotation.y). */
export interface Pose { spin: number; tiltX: number; tiltZ: number }
export const DEFAULT_POSE: Pose = { spin: 0.35, tiltX: 0.42, tiltZ: -0.16 };
export const pose = (v: Vec3, p: Pose): Vec3 => rotZ(rotX(rotY(v, p.spin), p.tiltX), p.tiltZ);

/** The 32 panels, oriented so a pentagon sits on +Y (the spin axis). The ten hexagons around the
 *  equator are flagged `accent` (they get the tomato stripe). */
export function panels(): Panel[] {
  const raw: Vec3[] = [];
  for (const a of [-1, 1]) for (const b of [-PHI, PHI]) raw.push([0, a, b], [a, b, 0], [b, 0, a]);
  // Bring vertex (0, 1, phi) onto +Y: rotate about X so its z becomes 0.
  const up = -Math.atan(PHI);
  const V = raw.map((v) => norm(rotX(v, up)));
  const edge = 2 / Math.hypot(1, PHI);                     // icosahedron edge length on the unit sphere
  const adj = V.map((a, i) => V.map((b, j) => (i !== j && Math.abs(len(sub(a, b)) - edge) < 1e-6 ? j : -1)).filter((j) => j >= 0));
  // Truncation point on edge a->b, one third of the way, pushed back onto the sphere.
  const cut = (a: number, b: number) => norm(lerp(V[a], V[b], 1 / 3));
  const out: Panel[] = [];

  V.forEach((v, i) => {
    // Order the five neighbours counter-clockwise around v (seen from outside).
    const ref = norm(sub(V[adj[i][0]], v)), side = cross(v, ref);
    const ring = [...adj[i]].sort((p, q) => angle(p) - angle(q));
    function angle(j: number) { const d = sub(V[j], v); return Math.atan2(dot(d, side), dot(d, ref)); }
    out.push({ kind: "pent", centre: v, corners: ring.map((j) => cut(i, j)), accent: false });
  });

  for (let i = 0; i < 12; i++) for (const j of adj[i]) for (const k of adj[i]) {
    if (!(i < j && j < k) || !adj[j].includes(k)) continue;
    let [a, b, c] = [i, j, k];
    if (dot(cross(sub(V[b], V[a]), sub(V[c], V[a])), V[a]) < 0) [b, c] = [c, b];   // counter-clockwise outward
    const corners = [cut(a, b), cut(b, a), cut(b, c), cut(c, b), cut(c, a), cut(a, c)];
    const centre = centroid([V[a], V[b], V[c]]);
    out.push({ kind: "hex", centre, corners, accent: Math.abs(centre[1]) < 0.5 });
  }
  return out;
}

/** Radius of a panel point at normalised distance `s` from its centre (0 = centre, 1 = seam):
 *  a slight pillow, then a quarter-round bevel down into the seam. */
export const BULGE = 0.012, BEVEL_START = 0.87, BEVEL_DEPTH = 0.03, SEAM_RADIUS = 0.976, INSET = 0.985;
export function radius(s: number) {
  let r = 1 + BULGE * (1 - s * s);
  if (s > BEVEL_START) { const u = (s - BEVEL_START) / (1 - BEVEL_START); r -= BEVEL_DEPTH * (1 - Math.sqrt(Math.max(0, 1 - u * u))); }
  return r;
}

// Ring positions (s) from centre to seam; denser where the bevel curves and around the accent stripe.
const RINGS = [0.2, 0.42, 0.6, 0.72, 0.78, 0.785, 0.835, 0.84, 0.87, 0.905, 0.935, 0.96, 0.978, 0.992, 1];
const ACCENT = [0.785, 0.835] as const;                     // tomato stripe, painted inside the bevel

export const COLORS = {
  hexCentre: 0xF6F0E2, hexEdge: 0xEDE4CF, pent: 0x355E3B, pentEdge: 0x2E5434, accent: 0xEF4429, seam: 0x33352B,
} as const;

export interface BallMesh { positions: Float32Array; colors: Float32Array; indices: Uint32Array; panels: Panel[] }

/** Triangle mesh of all panels. Each panel has its own vertices (so the seams stay crisp); colours are
 *  sRGB 0..1 (convert to linear before handing them to a renderer that expects linear). */
export function ballMesh(segments = 7): BallMesh {
  const ps = panels();
  const pos: number[] = [], col: number[] = [], idx: number[] = [];
  for (const p of ps) {
    const n = p.corners.length * segments;
    const boundary: Vec3[] = [];
    p.corners.forEach((c, i) => { const d = p.corners[(i + 1) % p.corners.length]; for (let t = 0; t < segments; t++) boundary.push(lerp(c, d, t / segments)); });
    const base = pos.length / 3;
    const put = (s: number, b: Vec3 | null) => {
      const dir = b ? norm(lerp(p.centre, b, s * INSET)) : p.centre;
      const r = radius(s);
      pos.push(dir[0] * r, dir[1] * r, dir[2] * r);
      col.push(...rgb(colorAt(p, s)));
    };
    put(0, null);
    for (const s of RINGS) for (const b of boundary) put(s, b);
    for (let i = 0; i < n; i++) idx.push(base, base + 1 + i, base + 1 + ((i + 1) % n));
    for (let r = 0; r < RINGS.length - 1; r++) {
      const a0 = base + 1 + r * n, b0 = a0 + n;
      for (let i = 0; i < n; i++) {
        const i1 = (i + 1) % n;
        idx.push(a0 + i, b0 + i, b0 + i1, a0 + i, b0 + i1, a0 + i1);
      }
    }
  }
  return { positions: new Float32Array(pos), colors: new Float32Array(col), indices: new Uint32Array(idx), panels: ps };
}

function colorAt(p: Panel, s: number): number {
  if (p.kind === "pent") return s > 0.9 ? COLORS.pentEdge : COLORS.pent;
  if (p.accent && s >= ACCENT[0] && s <= ACCENT[1]) return COLORS.accent;
  return mix(COLORS.hexCentre, COLORS.hexEdge, Math.min(1, s / 0.85));
}

export const rgb = (hex: number): Vec3 => [((hex >> 16) & 255) / 255, ((hex >> 8) & 255) / 255, (hex & 255) / 255];
function mix(a: number, b: number, t: number) {
  const [ar, ag, ab] = rgb(a), [br, bg, bb] = rgb(b);
  const c = (x: number, y: number) => Math.round((x + (y - x) * t) * 255);
  return (c(ar, br) << 16) | (c(ag, bg) << 8) | c(ab, bb);
}
const hex = (n: number) => `#${n.toString(16).padStart(6, "0")}`;

/** Static poster of the ball (orthographic, same pose as the 3D ball's first frame): the instant
 *  first paint, and the fallback when WebGL is unavailable. viewBox is -1..1. */
export function ballSvg(p: Pose = DEFAULT_POSE, idPrefix = "bs"): string {
  const outline = (panel: Panel, f: number) => {
    const out: Vec3[] = [], k = panel.corners.length;
    for (let i = 0; i < k; i++) for (let t = 0; t < 6; t++)
      out.push(pose(norm(lerp(panel.centre, lerp(panel.corners[i], panel.corners[(i + 1) % k], t / 6), f)), p));
    return out;
  };
  // Points behind the limb are pulled onto it, so a panel crossing the edge is cut by the silhouette.
  const pt = (v: Vec3) => { const q = v[2] < 0 ? norm([v[0], v[1], 0]) : v; return `${q[0].toFixed(4)},${(-q[1]).toFixed(4)}`; };
  const poly = (o: Vec3[]) => o.map(pt).join(" ");
  const body = panels().map((panel) => ({ panel, z: pose(panel.centre, p)[2] }))
    .filter((s) => s.z > -0.45).sort((a, b) => a.z - b.z)
    .map(({ panel, z }) => {
      const fill = panel.kind === "pent" ? hex(COLORS.pent) : hex(COLORS.hexEdge);
      const stripe = panel.accent && z > 0.2 ? `<polygon points="${poly(outline(panel, INSET * 0.82))}" fill="none" stroke="${hex(COLORS.accent)}" stroke-opacity=".9" stroke-width=".016" stroke-linejoin="round"/>` : "";
      return `<polygon points="${poly(outline(panel, Math.min(1, INSET * 1.008)))}" fill="${fill}"/>${stripe}`;
    }).join("");
  const g = idPrefix;
  return `<svg class="ball-svg" viewBox="-1.02 -1.02 2.04 2.04" aria-hidden="true">
    <defs>
      <radialGradient id="${g}-hi" cx="-.38" cy="-.46" r="1.25" gradientUnits="userSpaceOnUse"><stop offset="0" stop-color="#fff" stop-opacity=".42"/><stop offset=".45" stop-color="#fff" stop-opacity=".06"/><stop offset="1" stop-color="#fff" stop-opacity="0"/></radialGradient>
      <radialGradient id="${g}-lo" cx="-.25" cy="-.35" r="1.45" gradientUnits="userSpaceOnUse"><stop offset=".5" stop-color="#3A3020" stop-opacity="0"/><stop offset=".88" stop-color="#3A3020" stop-opacity=".2"/><stop offset="1" stop-color="#3A3020" stop-opacity=".38"/></radialGradient>
      <clipPath id="${g}-c"><circle r="1"/></clipPath>
    </defs>
    <g clip-path="url(#${g}-c)"><circle r="1" fill="${hex(COLORS.seam)}"/>${body}<circle r="1" fill="url(#${g}-lo)"/><circle r="1" fill="url(#${g}-hi)"/></g>
  </svg>`;
}
