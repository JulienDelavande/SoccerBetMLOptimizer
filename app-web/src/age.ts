/** Age confirmation (18+ only), remembered on this device. Shared by sign-in and the waitlist. */
export const AGE_KEY = "age_confirmed";
export const ageConfirmed = () => typeof localStorage !== "undefined" && localStorage.getItem(AGE_KEY) === "1";
export const setAgeConfirmed = (ok: boolean) => {
  if (typeof localStorage === "undefined") return;
  if (ok) localStorage.setItem(AGE_KEY, "1"); else localStorage.removeItem(AGE_KEY);
};
