// Session state: loaded once at startup, shared across pages.
import { getConfig, getMe, loginGoogle, logout as apiLogout } from "./api";
import type { PublicConfig, UserProfile } from "./api";

let config: PublicConfig | null = null;
let user: UserProfile | null = null;
let gsiLoaded: Promise<void> | null = null;

export async function initSession(): Promise<void> {
  try {
    config = await getConfig();
  } catch { config = { auth_enabled: false, google_client_id: "", telegram_bot: "" }; }
  if (config.auth_enabled) {
    try { user = await getMe(); } catch { user = null; }
  }
}

export const currentUser = () => user;
export const authConfig = () => config;
export const setUser = (u: UserProfile | null) => { user = u; };

export async function logout(): Promise<void> {
  await apiLogout();
  user = null;
}

function loadGsi(): Promise<void> {
  if (!gsiLoaded) {
    gsiLoaded = new Promise((resolve, reject) => {
      const s = document.createElement("script");
      s.src = "https://accounts.google.com/gsi/client";
      s.async = true; s.defer = true;
      s.onload = () => resolve();
      s.onerror = () => reject(new Error("GSI load failed"));
      document.head.appendChild(s);
    });
  }
  return gsiLoaded;
}

/** Render the "Sign in with Google" button into `el`; on success, sets the user and calls onLogin. */
export async function renderGoogleButton(el: HTMLElement, onLogin: (u: UserProfile) => void): Promise<void> {
  if (!config?.auth_enabled || !config.google_client_id) {
    el.innerHTML = `<p class="note">La connexion sera bientôt disponible.</p>`;
    return;
  }
  await loadGsi();
  const g = (window as unknown as { google: any }).google;
  g.accounts.id.initialize({
    client_id: config.google_client_id,
    callback: async (resp: { credential: string }) => {
      try {
        const u = await loginGoogle(resp.credential);
        user = u;
        onLogin(u);
      } catch { el.insertAdjacentHTML("beforeend", `<p class="note down">Échec de la connexion.</p>`); }
    },
  });
  g.accounts.id.renderButton(el, { theme: "filled_black", size: "large", shape: "pill", text: "continue_with" });
}
