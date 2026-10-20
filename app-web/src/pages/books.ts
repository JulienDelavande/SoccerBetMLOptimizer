// Bookmakers the user can pick from (the soft books we compare to Pinnacle).
import { BOOKS } from "../format";

const KEYS = ["onexbet", "williamhill", "sport888", "unibet_eu", "unibet_uk", "unibet_nl", "unibet_se",
  "marathonbet", "betsson", "nordicbet", "coolbet", "leovegas", "leovegas_se", "gtbets", "betano_uk",
  "betfred_uk", "casumo", "coral", "ladbrokes_uk", "paddypower", "skybet", "betvictor", "tipico_de",
  "betway", "everygame", "mybookieag", "betonlineag", "suprabets"];

export const BOOKS_ALL = KEYS.map((key) => ({ key, label: BOOKS[key] ?? pretty(key) }));

function pretty(k: string): string {
  return k.replace(/_(eu|uk|nl|se|de|it|fr)$/, (_m, r) => ` (${r.toUpperCase()})`)
    .replace(/(^|\s)\w/g, (c) => c.toUpperCase());
}
