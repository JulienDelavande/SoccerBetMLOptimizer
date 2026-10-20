// "Bot" (public showcase, all bookmakers) vs "Moi" (personalised: my books, my stakes, my results).
// Only meaningful when signed in; anonymous visitors always see the bot.
export type View = "bot" | "me";

const KEY = "view";
let view: View = (typeof localStorage !== "undefined" ? (localStorage.getItem(KEY) as View) : null) || "me";

export const getView = (): View => view;
export const setView = (v: View) => { view = v; if (typeof localStorage !== "undefined") localStorage.setItem(KEY, v); };
