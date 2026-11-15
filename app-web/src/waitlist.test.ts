import { afterEach, beforeAll, describe, expect, it } from "vitest";
import { setLang, t } from "./i18n";
beforeAll(() => setLang("fr"));
import { BUDGETS, MESSAGE_MAX, PLANS, validateWaitlist, waitlistCard, waitlistDone, waitlistForm, waitlistPayload } from "./waitlist";
import type { WaitlistValues } from "./waitlist";

const ok: WaitlistValues = { email: " Alice@Example.com ", plan: "yearly", budget: "10_20", message: "  Hâte  ", consent: true, adult: true, website: "" };
const text = (html: string) => html.replace(/<[^>]+>/g, " ").replace(/\s+/g, " ");

afterEach(() => setLang("fr"));

describe("validateWaitlist", () => {
  it("accepts a complete answer", () => {
    expect(validateWaitlist(ok)).toEqual({});
    expect(validateWaitlist({ ...ok, message: "" })).toEqual({});
  });

  it("flags every invalid field", () => {
    const e = validateWaitlist({ email: "nope", plan: "", budget: "50plus", message: "x".repeat(MESSAGE_MAX + 1), consent: false, adult: false, website: "" });
    expect(Object.keys(e).sort()).toEqual(["adult", "budget", "consent", "email", "message", "plan"]);
  });

  it.each(["", "a@b", "a b@c.fr", "@x.fr", `${"x".repeat(320)}@a.fr`])("rejects the email %j", (email) => {
    expect(validateWaitlist({ ...ok, email }).email).toBeTruthy();
  });

  it("counts the trimmed message against the limit", () => {
    expect(validateWaitlist({ ...ok, message: ` ${"x".repeat(MESSAGE_MAX)}  ` })).toEqual({});
  });
});

describe("waitlistPayload", () => {
  it("normalises the answer into the API body", () => {
    expect(waitlistPayload(ok, "en")).toEqual({
      email: "alice@example.com", plan: "yearly", budget: "10_20", message: "Hâte", lang: "en",
      consent: true, adult: true, website: "",
    });
  });

  it("sends a blank message as null and passes the honeypot through", () => {
    const p = waitlistPayload({ ...ok, message: "   ", website: "spam" }, "fr");
    expect(p.message).toBeNull();
    expect(p.website).toBe("spam");
    expect(p.lang).toBe("fr");
  });

  it("only uses the values the API accepts", () => {
    expect(PLANS.map(([k]) => k)).toEqual(["monthly", "yearly", "unsure"]);
    expect(BUDGETS.map(([k]) => k)).toEqual(["lt10", "10_20", "20_30", "30plus"]);
  });
});

describe("waitlistForm", () => {
  it("labels every control and groups the radios", () => {
    const html = waitlistForm(null);
    expect(html).toMatch(/<label class="k" for="wl-email">/);
    expect(html).toMatch(/<label class="k" for="wl-message">/);
    expect(html.match(/<fieldset/g)).toHaveLength(2);
    expect(html).toMatch(/<legend class="k">Formule souhaitée<\/legend>/);
    expect(html).toMatch(/<legend class="k">Budget mensuel<\/legend>/);
    expect(html.match(/type="radio" name="plan"/g)).toHaveLength(3);
    expect(html.match(/type="radio" name="budget"/g)).toHaveLength(4);
    expect(html).toMatch(/maxlength="1000"/);
    expect(html).toMatch(/type="submit" class="btn-cta wl-submit">Rejoindre la liste d'attente/);
    expect(html).toMatch(/role="status" aria-live="polite"/);
  });

  it("has an off-screen honeypot out of the tab order", () => {
    expect(waitlistForm(null)).toMatch(/<div class="wl-hp" aria-hidden="true"><label>[^<]*<input type="text" name="website" tabindex="-1" autocomplete="off"/);
  });

  it("requires consent (linked to the privacy page) and the 18+ confirmation", () => {
    const html = waitlistForm(null);
    expect(html).toMatch(/name="consent" required/);
    expect(html).toMatch(/href="\/confidentialite.html#liste-attente"/);
    expect(html).toMatch(/name="adult" required aria-describedby/);
    expect(waitlistForm(null, null, true)).toMatch(/name="adult" required checked/);
  });

  it("locks the email to the signed-in account's address", () => {
    const html = waitlistForm({ email: "me@gmail.com" });
    expect(html).toMatch(/value="me@gmail.com" readonly/);
    expect(html).toMatch(/Utiliser une autre adresse/);
    expect(waitlistForm(null)).not.toMatch(/readonly/);
  });

  it("prefills an update and escapes the stored email", () => {
    const html = waitlistForm(null, { email: '"><script>x</script>@a.fr', plan: "monthly", budget: "30plus" });
    expect(html).not.toMatch(/<script>/);
    expect(html).toMatch(/value="monthly" checked/);
    expect(html).toMatch(/value="30plus" checked/);
  });
});

describe("success state", () => {
  it("confirms, shows the address and offers an update", () => {
    const tx = text(waitlistDone({ email: "a@b.fr", plan: "unsure", budget: "lt10" }));
    expect(tx).toMatch(/C'est noté, tu seras prévenu\./);
    expect(tx).toMatch(/Inscrit avec a@b\.fr ?\./);
    expect(tx).toMatch(/Modifier mes réponses/);
    expect(waitlistDone({ email: "<b>x</b>@a.fr", plan: "", budget: "" })).not.toMatch(/<b>x<\/b>/);
  });
});

describe("copy", () => {
  // Code de la consommation L121-4 15° : no promise of winnings or better chances.
  const BANNED = /gagn|\bwin|ROI|rendement|return|profit|bénéfice|chance|garanti|guarantee/i;
  it.each(["fr", "en"] as const)("stays neutral and is fully translated (%s)", (lang) => {
    setLang(lang);
    const all = text(waitlistCard() + waitlistForm(null) + waitlistDone({ email: "a@b.fr", plan: "", budget: "" }));
    expect(all).not.toMatch(BANNED);
    if (lang === "en") {
      expect(all).toMatch(/A paid plan is in the works/);
      expect(all).toMatch(/Join the waitlist/);
      expect(all).not.toMatch(/Formule|Budget mensuel|Rejoindre|J'accepte/);
    } else {
      expect(all).toMatch(/Une formule payante se prépare/);
      expect(all).toMatch(/Gratuit, sans engagement, désinscription en un clic\./);
    }
  });

  it("translates every error message", () => {
    setLang("en");
    const e = validateWaitlist({ email: "", plan: "", budget: "", message: "x".repeat(1001), consent: false, adult: false, website: "" });
    for (const k of Object.values(e)) expect(t(k!)).not.toBe(k);
  });
});
