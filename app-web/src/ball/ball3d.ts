// WebGL football (three.js), loaded lazily by ./hero.ts. Renders only while something moves
// (idle spin, drag inertia, hover tilt) and only while `setActive(true)` (on screen, tab visible).
import {
  BufferAttribute, BufferGeometry, Color, DirectionalLight, Group, HemisphereLight, Mesh, MeshPhysicalMaterial,
  MeshStandardMaterial, NeutralToneMapping, PerspectiveCamera, PMREMGenerator, SRGBColorSpace, Scene,
  SphereGeometry, WebGLRenderer,
} from "three";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { COLORS, DEFAULT_POSE, SEAM_RADIUS, ballMesh } from "./geometry";

export interface BallOptions { reducedMotion: boolean; dark: boolean; hoverTilt: boolean; onFirstFrame?: () => void }
export interface Ball { setActive(on: boolean): void; setDark(dark: boolean): void; dispose(): void }

const IDLE = (2 * Math.PI) / 20;       // one revolution per 20 s
const INERTIA_TAU = 0.9;               // s: flick speed decays back to idle with this time constant
const TILT_MAX = 0.16;                 // rad, hover tilt toward the pointer
const TILT_TAU = 0.18;
const MAX_SPIN = 14;                   // rad/s
const DISTANCE = 9;
const FILL = 0.94;                     // ball diameter / canvas size

/** Mount the ball into `canvas`. `surface` receives drag and hover pointer events. */
export function createBall(canvas: HTMLCanvasElement, surface: HTMLElement, opts: BallOptions): Ball {
  const renderer = new WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: "low-power" });
  renderer.setPixelRatio(Math.min(devicePixelRatio || 1, 2));
  renderer.outputColorSpace = SRGBColorSpace;
  renderer.toneMapping = NeutralToneMapping;
  renderer.setClearColor(0x000000, 0);

  const scene = new Scene();
  const pmrem = new PMREMGenerator(renderer);
  const room = new RoomEnvironment();
  const env = pmrem.fromScene(room, 0.04).texture;
  scene.environment = env;
  room.dispose?.();
  pmrem.dispose();

  // Perspective with a long lens: reads like a product shot and matches the orthographic SVG poster.
  const half = Math.tan(Math.asin(1.012 / DISTANCE)) / FILL;
  const camera = new PerspectiveCamera((2 * Math.atan(half) * 180) / Math.PI, 1, DISTANCE - 2, DISTANCE + 2);
  camera.position.set(0, 0, DISTANCE);

  const data = ballMesh(7);
  const geo = new BufferGeometry();
  const lin = new Float32Array(data.colors.length);
  const c = new Color();
  for (let i = 0; i < lin.length; i += 3) {
    c.setRGB(data.colors[i], data.colors[i + 1], data.colors[i + 2], SRGBColorSpace);
    lin[i] = c.r; lin[i + 1] = c.g; lin[i + 2] = c.b;
  }
  geo.setAttribute("position", new BufferAttribute(data.positions, 3));
  geo.setAttribute("color", new BufferAttribute(lin, 3));
  geo.setIndex(new BufferAttribute(data.indices, 1));
  geo.computeVertexNormals();
  // Satin leather: soft roughness with a thin, blurry clearcoat for the sheen on the panel crowns.
  const skin = new MeshPhysicalMaterial({
    vertexColors: true, roughness: 0.56, metalness: 0, clearcoat: 0.22, clearcoatRoughness: 0.45, envMapIntensity: 0.38,
  });
  const seamGeo = new SphereGeometry(SEAM_RADIUS, 96, 64);
  const seamMat = new MeshStandardMaterial({ color: COLORS.seam, roughness: 0.9, envMapIntensity: 0.3 });

  const spinner = new Group();             // spin about the pentagon axis
  spinner.add(new Mesh(geo, skin), new Mesh(seamGeo, seamMat));
  const axis = new Group();                // the tilted axis
  axis.rotation.order = "ZXY";
  axis.rotation.set(DEFAULT_POSE.tiltX, 0, DEFAULT_POSE.tiltZ);
  axis.add(spinner);
  const hover = new Group();               // hover tilt toward the pointer
  hover.add(axis);
  scene.add(hover);
  spinner.rotation.y = DEFAULT_POSE.spin;

  // Studio: warm key from the upper left, cool rim from behind on the right, soft fill from below.
  const key = new DirectionalLight(0xfff3e0, 3.2); key.position.set(-5, 5, 2.4);
  const rim = new DirectionalLight(0xf6f0e2, 1.6); rim.position.set(4.5, 2.5, -4);
  const rim2 = new DirectionalLight(0xf6f0e2, 0.5); rim2.position.set(-4, -1, -3);
  const fill = new HemisphereLight(0xfff8ec, 0x6b6550, 0.18);
  scene.add(key, rim, rim2, fill);

  function setDark(dark: boolean) {
    // On deep hunter the ball needs a brighter rim to separate from the page, and a darker bounce.
    rim.intensity = dark ? 2.6 : 1.6;
    rim2.intensity = dark ? 1.1 : 0.6;
    fill.groundColor.set(dark ? 0x1e3423 : 0x6b6550);
    fill.intensity = dark ? 0.16 : 0.18;
    renderer.toneMappingExposure = dark ? 1.0 : 1.02;
    request();
  }

  // ---- size ----
  let width = 0;
  const resize = () => {
    const r = canvas.getBoundingClientRect();
    const w = Math.max(1, Math.round(r.width)), h = Math.max(1, Math.round(r.height));
    if (w === width && canvas.height === Math.round(h * renderer.getPixelRatio())) return;
    width = w;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    request(true);
  };
  const ro = new ResizeObserver(resize);
  ro.observe(canvas);

  // ---- motion state ----
  const idle = opts.reducedMotion ? 0 : IDLE;
  let omega = idle, dragging = false, active = false, raf = 0, last = 0, rendered = false;
  let tiltX = 0, tiltY = 0, tx = 0, ty = 0;

  function frame(now: number) {
    raf = 0;
    const dt = Math.min(0.05, last ? (now - last) / 1000 : 0);
    last = now;
    if (!dragging) {
      omega = idle + (omega - idle) * Math.exp(-dt / INERTIA_TAU);
      if (Math.abs(omega - idle) < 1e-3) omega = idle;
      spinner.rotation.y += omega * dt;
    }
    const k = 1 - Math.exp(-dt / TILT_TAU);
    tiltX += (tx - tiltX) * k; tiltY += (ty - tiltY) * k;
    if (Math.abs(tx - tiltX) < 1e-4) tiltX = tx;
    if (Math.abs(ty - tiltY) < 1e-4) tiltY = ty;
    hover.rotation.set(tiltX, tiltY, 0);
    renderer.render(scene, camera);
    if (!rendered) { rendered = true; opts.onFirstFrame?.(); }
    const moving = dragging || omega !== 0 || tiltX !== tx || tiltY !== ty;
    if (active && moving) raf = requestAnimationFrame(frame);
    else last = 0;
  }
  /** Schedule a frame. `force` renders even when inactive (first paint, resize). */
  function request(force = false) {
    if (raf || (!active && !force)) return;
    raf = requestAnimationFrame(frame);
  }

  // ---- drag to spin: horizontal-dominant only; vertical swipes keep scrolling the page ----
  let startX = 0, startY = 0, lastX = 0, lastT = 0, pointer = -1, decided = false, velocity = 0;
  const onDown = (e: PointerEvent) => {
    if (e.button !== 0 || pointer !== -1) return;
    pointer = e.pointerId; decided = e.pointerType === "mouse"; startX = lastX = e.clientX; startY = e.clientY; lastT = e.timeStamp; velocity = 0;
    if (decided) begin(e);
  };
  const begin = (e: PointerEvent) => {
    dragging = true;
    surface.setPointerCapture?.(e.pointerId);
    surface.classList.add("grabbing");
    request();
  };
  const onMove = (e: PointerEvent) => {
    if (opts.hoverTilt && e.pointerType === "mouse" && !dragging) aim(e);
    if (e.pointerId !== pointer) return;
    if (!decided) {
      const dx = e.clientX - startX, dy = e.clientY - startY;
      if (Math.hypot(dx, dy) < 6) return;
      decided = true;
      if (Math.abs(dx) <= Math.abs(dy)) { pointer = -1; return; }   // vertical: leave it to the page
      begin(e);
    }
    if (!dragging) return;
    const dx = e.clientX - lastX, dt = Math.max(1, e.timeStamp - lastT) / 1000;
    const dTheta = (dx / Math.max(80, width * FILL)) * Math.PI;    // one ball width = half a turn
    spinner.rotation.y += dTheta;
    velocity = velocity * 0.6 + (dTheta / dt) * 0.4;
    lastX = e.clientX; lastT = e.timeStamp;
    request();
  };
  const onUp = (e: PointerEvent) => {
    if (e.pointerId !== pointer) return;
    pointer = -1;
    if (!dragging) return;
    dragging = false;
    surface.classList.remove("grabbing");
    // A pause before releasing means "stop here", not "flick".
    const fresh = e.timeStamp - lastT < 80;
    omega = fresh ? Math.max(-MAX_SPIN, Math.min(MAX_SPIN, velocity)) : idle;
    request();
  };
  const aim = (e: PointerEvent) => {
    const r = surface.getBoundingClientRect();
    const nx = ((e.clientX - r.left) / r.width) * 2 - 1, ny = ((e.clientY - r.top) / r.height) * 2 - 1;
    ty = Math.max(-1, Math.min(1, nx)) * TILT_MAX;
    tx = Math.max(-1, Math.min(1, ny)) * TILT_MAX * 0.8;
    request();
  };
  const onLeave = () => { tx = 0; ty = 0; request(); };
  surface.addEventListener("pointerdown", onDown);
  surface.addEventListener("pointermove", onMove);
  surface.addEventListener("pointerup", onUp);
  surface.addEventListener("pointercancel", onUp);
  surface.addEventListener("pointerleave", onLeave);

  setDark(opts.dark);
  resize();
  request(true);

  return {
    setActive(on) {
      active = on;
      if (on) request(); else if (raf) { cancelAnimationFrame(raf); raf = 0; last = 0; }
    },
    setDark,
    dispose() {
      active = false;
      if (raf) cancelAnimationFrame(raf);
      ro.disconnect();
      surface.removeEventListener("pointerdown", onDown);
      surface.removeEventListener("pointermove", onMove);
      surface.removeEventListener("pointerup", onUp);
      surface.removeEventListener("pointercancel", onUp);
      surface.removeEventListener("pointerleave", onLeave);
      geo.dispose(); seamGeo.dispose(); skin.dispose(); seamMat.dispose(); env.dispose();
      renderer.dispose();
      renderer.forceContextLoss();
    },
  };
}
