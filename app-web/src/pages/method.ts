import { pct } from "../format";
import { t } from "../i18n";
import { JIS_PHONE, bankrollNote, pageHead, recordFacts } from "./shared";
import type { SiteData } from "../types";

export function renderMethod(app: HTMLElement, data: SiteData) {
  const clv = data.kpis?.clv;
  const f = recordFacts({ live_since: data.live_since, generated_at: data.generated_at ?? new Date().toISOString(), kpis: data.kpis ?? null });
  app.innerHTML = `
    ${pageHead(t("Méthode"), t("Comment chaque pari est choisi, misé et mesuré."))}
    <section class="method">
      <article data-reveal><span class="n" aria-hidden="true">01</span><h2>${t("Pinnacle donne le juste prix")}</h2>
        <p>${t("Pinnacle est le bookmaker le plus précis du monde : marges faibles, il accepte les gros parieurs et corrige ses cotes avec leur argent. On retire sa marge (méthode de Shin) pour obtenir la vraie probabilité de chaque issue.")}</p></article>
      <article data-reveal><span class="n" aria-hidden="true">02</span><h2>${t("On cherche les bookmakers en retard")}</h2>
        <p>${t("Chaque jour, on compare à ce juste prix les cotes de plus de vingt bookmakers grand public (Pinnacle sert de référence, les bourses d'échange sont exclues). Quand une cote dépasse le juste prix d'au moins 2 % (cote ≤ 3,50, prix récent, avant le coup d'envoi), c'est un pari de valeur. Un bookmaker seul est rarement en retard : l'avantage vient du nombre de bookmakers surveillés. Un seul pari par match, au premier signal.")}</p></article>
      <article data-reveal><span class="n" aria-hidden="true">03</span><h2>${t("On mise avec Kelly")}</h2>
        <p>${t("La mise suit le critère de Kelly, divisé par deux : plus l'avantage est grand, plus on mise, sans jamais dépasser 5 % de la bankroll par pari ni 30 % par jour. En moyenne, moins de 2 % par pari.")}</p></article>
      <article data-reveal><span class="n" aria-hidden="true">04</span><h2>${t("On mesure avec le CLV")}</h2>
        <p>${t("Les résultats des matchs sont bruités. La mesure suivie est la closing line value : la cote publiée comparée à la cote de clôture de Pinnacle. Sur les paris publiés depuis le {d}, elle est de {clv} en moyenne. C'est un écart mesuré avec le marché, pas une garantie de résultat.", { d: f.since, clv: clv == null ? "–" : pct(clv) })}</p></article>
    </section>
    <section class="risk-card" data-reveal><h2>${t("Les risques, honnêtement")}</h2>
      <ul class="risks">
        <li><b>${t("Ça fluctue beaucoup.")}</b> ${t("L'écart mesuré est de quelques % par pari : même s'il se maintient, une saison peut finir en perte (à peu près 4 chances sur 10).")}</li>
        <li><b>${t("Les résultats passés ne garantissent pas les résultats futurs.")}</b> ${t("L'historique publié est court ({p}) : il ne permet pas de conclure, et l'écart peut disparaître.", { p: f.period })}</li>
        <li><b>${t("Les bookmakers limitent les comptes.")}</b> ${t("Un compte qui prend ces cotes est souvent plafonné : les résultats réels s'écartent alors de l'historique publié.")}</li>
        <li><b>${t("Pas de modèle magique.")}</b> ${t("Un modèle maison a été testé sur 14 saisons et 22 championnats : il ne bat jamais Pinnacle. Toute la valeur vient de la comparaison des cotes.")}</li>
        <li><b>${t("Bankroll fictive.")}</b> ${bankrollNote(data.start_bankroll ?? 10000)}</li>
        <li><b>${t("Information, pas conseil.")}</b> ${t("Ce site publie une méthode et son historique ; ce n'est pas un conseil de pari adapté à votre situation. Ne misez que ce que vous pouvez vous permettre de perdre. Interdit aux moins de 18 ans.")}</li>
      </ul>
      <p class="fine">${t("Joueurs Info Service :")} <a href="tel:+33974751313">${JIS_PHONE}</a> ${t("(appel non surtaxé).")}</p>
    </section>`;
}
