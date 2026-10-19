import { pct } from "../format";
import type { SiteData } from "../types";

export function renderMethod(app: HTMLElement, data: SiteData) {
  const clv = data.kpis?.clv;
  app.innerHTML = `
    <section class="sec"><div class="sec-head"><h2>Méthode</h2></div></section>
    <section class="method">
      <article><span class="n">01</span><h3>Pinnacle donne le juste prix</h3>
        <p>Pinnacle est le bookmaker le plus précis du monde : marges faibles, il accepte les gros parieurs et corrige ses cotes avec leur argent. On retire sa marge (méthode de Shin) pour obtenir la vraie probabilité de chaque issue.</p></article>
      <article><span class="n">02</span><h3>On cherche les bookmakers en retard</h3>
        <p>Chaque jour, on compare les cotes de 1xBet à ce juste prix. Quand une cote dépasse le juste prix d'au moins 2 % (cote ≤ 3,50, prix récent, avant le coup d'envoi), c'est un pari de valeur. Un seul pari par match, au premier signal.</p></article>
      <article><span class="n">03</span><h3>On mise avec Kelly</h3>
        <p>La mise suit le critère de Kelly, divisé par deux : plus l'avantage est grand, plus on mise, sans jamais dépasser 5 % de la bankroll par pari ni 30 % par jour. En moyenne, moins de 2 % par pari.</p></article>
      <article><span class="n">04</span><h3>On mesure avec le CLV</h3>
        <p>Les résultats des matchs sont bruités. Le vrai juge est la closing line value : notre cote comparée à la cote de clôture de Pinnacle. Elle est de ${clv == null ? "–" : pct(clv)} en moyenne ici : on achète moins cher que le marché.</p></article>
    </section>
    <section class="panel warn"><div class="panel-h"><h3>Les risques, honnêtement</h3></div>
      <ul class="risks">
        <li><b>Ça fluctue beaucoup.</b> L'avantage est d'environ 2 à 3 % par pari : sur une saison, on a à peu près 4 chances sur 10 d'être en perte malgré tout.</li>
        <li><b>Les gains passés ne garantissent rien.</b> L'espérance tourne autour de quelques % de la bankroll par saison, pas +40 % par an.</li>
        <li><b>Les bookmakers limitent les gagnants.</b> Un compte qui gagne finit souvent plafonné.</li>
        <li><b>Pas de modèle magique.</b> Un modèle maison a été testé sur 14 saisons et 22 championnats : il ne bat jamais Pinnacle. Toute la valeur vient de la comparaison des cotes.</li>
        <li>N'engagez que de l'argent que vous acceptez de perdre. 18+.</li>
      </ul>
      <p class="fine">Historique avant le 19/10/2026 rejoué avec les mêmes règles sur les cotes enregistrées à l'époque.</p>
    </section>`;
}
