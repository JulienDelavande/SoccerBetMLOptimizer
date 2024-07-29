# Définition du problème et notation

## Matchs
Soit $t$ $\in$ $\mathbb{R}^+$ le temps. Pour chaque temps $t$, on définit un ensemble de matchs $\mathbb{M}(t)$ tel que $\mathbb{M}(t)$ = $\{m_1, m_2, ..., m_M\}$ avec M $\in$ $\mathbb{N}$. Cette ensemble représente l'ensemble des matchs planifiés ou en train d'être joués mais non terminés pour n'importe quelle discipline sportive.

## Issues
Pour chaque match $m_k$ $\in$ $\mathbb{M}(t)$, on définit un ensemble d'issues possibles $\mathbb{\Omega}(m_k)$ = $\{\omega_1, \omega_2, ..., \omega_N\}$ avec N $\in$ $\mathbb{N}$. \
Par exemple, pour un match de football, on peut définir un ensemble d'issues possibles $\Omega(m_k)$=$\{\text{Victoire de l'équipe à domicile, Victoire de l'équipe à l'extérieur, Match nul}\}$ donc $N=3$.

## Bookmakers
Soit $\mathbb{B}$, l'ensemble des bookmakers. Pour chaque bookmaker $B$ $\in$ $\mathbb{B}$, on définit un ensemble de cotes $\mathbb{O}(B, m_k, t)$ = $\{o_1, o_2, ..., o_N\}$ avec N $\in$ $\mathbb{N}$. Ces cotes sont les cotes proposées par le bookmaker $B$ pour chaque issue possible d'un match donné $m_k$ à un temps $t$. Par exemple, pour un match de football, les cotes proposées par un bookmaker sont $\{1.5, 2.5, 3.5\}$.

Chaque bookmaker est libre de chosir les matchs et les issues pour ces matchs pour lesquels il propose des côtes. Le bookmaker définit lui même les côtes qu'il propose pour chaque issue possible d'un match donné. Il doit cependant proposer des issues tels que pour chaque match $m_k$, $\bigcup_{i=1}^{N} \omega_i^k = \Omega(m_k)$.

On note $B_{bookmaker}(B, t)$ la bankroll du bookmaker $B$ à un temps $t$.

## Parieurs
Soit $\mathbb{J}$, l'ensemble des parieurs (joueur). Pour chaque parieur $J$ $\in$ $\mathbb{J}$, on définit un vecteur de fraction de sa bankroll $F(J, B, t) = ( f_1, f_2, ..., f_N)$ avec N $\in$ $\mathbb{N}$. Ce vecteur représente les fractions de la bankroll du joueur $J$ qu'il place sur chaque issue possible d'un match donné proposé par un bookmaker $B$ à un temps $t$. \
Par exemple, pour un match de football, le joueur $J$ peut placer 20$ sur une victoire de l'équipe à domicile avec une côte de 1.5 proposée par le bookmaker $B$ ($f_1 = 0.2$, $\omega_1 = \text{Victoire de l'équipe à domicile}$).


Chaque parieur est libre de choisir les matchs et les issues pour ces matchs pour lesquels il propose des paris. Le parieur définit lui même les paris qu'il propose pour chaque issue possible d'un match donné.

On note $B_{joueur}(J, t)$ la bankroll du parieur $J$ à un temps $t$, avant d'avoir parié pour les matchs à un temps $t$ et après avoir récupéré les gains des matchs à un temps $t-1$.


## Résultats
A l'issue d'un match, la parieur $J$ gagne ou perd de l'argent en fonction de l'issue du match et des paris qu'il a placé. 

De même, chaque bookmaker gagne ou perd de l'argent en fonction de l'issue du match et des côtes qu'il a proposé.

**Hypothèse**:\
Pour simplifier le problème, on considérera que $t$ est discret. Ainsi pour chaque $t$, on a un ensemble de matchs $\mathbb{M}(t)$, un ensemble de bookmakers $\mathbb{B}$ et un ensemble de parieurs $\mathbb{J}$ qui font leur paris et définissent leur côte à un temps $t$ donné et récupère leur gain à un temps $t+1$. De même à $t+1$, on a un ensemble de matchs $\mathbb{M}(t+1)$, un ensemble de bookmakers $\mathbb{B}$ et un ensemble de parieurs $\mathbb{J}$ qui font leur paris et définissent leur côte à un temps $t+1$ donné et récupère leur gain à un temps $t+2$. Les matchs à $t$ seront joués à $t+1$ et les résultats seront connus à $t+1$.

- $M$ corresond au nombre de matchs à un temps $t$.
- $N$ correspond au nombre d'issues possibles pour un match donné.

<br>

- Soit $\mathbb{M}(t) = \{m_1, m_2, ..., m_M\}$ l'ensemble des matchs à un temps $t$.
- Soit $\Omega(m_k)$ = $\{\omega_1^k, \omega_2^k, ..., \omega_N^k\}$ les issues possibles du match $m_k$.
- Soit $\mathbb{O}(B, m_k) = \{o_1^k, o_2^k, ..., o_N^k\}$ les côtes proposées par le bookmaker $b$ pour chaque issue possible du match $m_k$. \
(On posera $o_i^k = 1$ si le bookmaker ne propose pas l'issue associée)
- Soit $\mathbb{F}(J, B, m_k) = \{f_1^k, f_2^k, ..., f_N^k\}$ les fractions de la bankroll du joueur $J$ qu'il place sur chaque issue possible du match $m_k$ proposé par le bookmaker $B$.\
(De même si le joueur ne parie pas sur une des issue $i$, on posera $f_i^k = 0$)

A l'issue du match $m_k$, pour chaque issue $\omega_i^k$ du match $m_k$, le joueur rajoute ou non de l'argent à sa bankroll en fonction de l'issue du match et des paris qu'il a placé. 

On note $\Omega_i(m_k) = {\omega_i^k, \neg \omega_i^k}$ l'ensemble des issues possibles du match $m_k$ avec $\neg \omega_i^k$ l'issue contraire de $\omega_i^k$. \
Ainsi on peut définir la variable aléatoire $X_i^k :\Omega_i(m_k) \to \{0, 1\}$, la variable aléatoire qui prend la valeur 1 si l'issue $\omega_i^k$ se réalise et 0 sinon.

**Hypothèse**:
- On considère pour simplifier qu'il n'y a pour l'instant qu'un bookmaker (du point de vue du bookmaker cela ne pose aucun problème et du point de vue du joueur, cela revient à prendre les "meilleures" côtes proposées parmi tous les bookmakers en definssant un bookmaker fictif, "meilleur" restant à définir). \
- De plus on ne considéreara pour l'instant qu'un sport avec pour chaque match toujours $N$ issues possibles, dont les côtes sont toujours proposées par le bookmaker.

---

### Joueur

On peut définir la bankroll du joueur $B_{joueur}(t)$ à un temps $t$ comme suit:

$$B_{joueur}(t+1) = B_{joueur}(t) \times [\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times X_i^k - 1)(t)] + B_{joueur}(t)$$

---

### Bookmaker

De même pour le bookmaker $B_{bookmaker}(t)$ à un temps $t$:

$$B_{bookmaker}(t+1) = B_{joueur}(t) \times [\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (1 - o_i^k \times X_i^k)(t)] + B_{bookmaker}(t)$$

$B_{joueur}(t)$ et $B_{bookmaker}(t+1)$ sont des variables aléatoires. 

---

On note 

$$G_{joueur}(t+1) = B_{joueur}(t+1) - B_{joueur}(t) = B_{joueur}(t) \times [\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times X_i^k - 1)(t)]$$
$$G_{bookmaker}(t+1) = B_{bookmaker}(t+1) - B_{bookmaker}(t) = B_{joueur}(t) \times [\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (1 - o_i^k \times X_i^k)(t)]$$

On remarque que la somme des gains du joueur et du bookmaker est nulle. \
$G_{joueur}(t) = - G_{bookmaker}(t)$ \
Le joueur joue donc contre le bookmaker. 

Dans le cas d'un bookmaker contre plusieurs joueurs,  ce n'est pas le cas. Mais chaque gain de joueur positif pénalise le bookmaker et chaque gain de joueur négatif récompense le bookmaker.

Pour ne pas prendre en compte l'apport initial de la bankroll du joueur et du bookmaker, on peut définir le ROI (Return on Investment) du joueur et du bookmaker comme suit:

$ROI_{joueur}(T) = \frac{\sum_{t=0}^TG_{joueur}(t)}{B_{joueur}(t=0)} = \frac{B_{joueur}(T)}{B_{joueur}(0)}$

$ROI_{bookmaker}(T) = \frac{\sum_{t=0}^TG_{bookmaker}(t)}{B_{bookmaker}(t=0)} = \frac{B_{bookmaker}(T)}{B_{bookmaker}(0)}$


## Probabilités des issues

### Probabilités vraies

Chaque issue $\omega_i^k$ d'un match $m_k$ a une probabilité de se réaliser $r_i^k$ qui est inconnue.

**Hypothèse**:\
On suppose qu'il existe $Y$ un vecteur de variables aléatoires qui repésente la description de l'état du monde à un temps $t$ donné. $Y$ est un vecteur de variables aléatoires qui représente l'ensemble des informations disponibles à un temps $t$ donné. $Y$ peut contenir des informations sur les matchs, les joueurs, les résultats des matchs précédents, etc.

On définit $\mathbb{P}_Y^{real.i,k}$ la loi de probabilité définit sur $\Omega_i(m^k)$ en fonction de l'état du monde $Y$ à un temps $t$ donné, la loi sachant $Y$ pour $t$ donné.

On note $r_i^k = \mathbb{P}_Y^{real.i,k}(X_i^k = 1)$ la probabilité vraie que l'issue $\omega_i^k$ se réalise pour le match $m_k$ en fonction de l'état du monde $Y$ à un temps $t$ donné.


### Probabilités bookmaker

Soit $D_b$, un vecteur de variables aléatoires qui représente les informations disponibles pour le bookmaker à un temps $t$ donné. On définit $\mathbb{P}_{D_{b}}^{bookies.i,k}$ la loi de probabilité définit sur $\Omega_i(m^k)$ en fonction de l'information $D_{b}$ à un temps $t$ donné, la loi sachant $D_{b}$ pour $t$ donné.

On note $b_i^k = \mathbb{P}_{D_{b}}^{bookies.i,k}(X_i^k = 1)$ la probabilité estimée par le bookmaker que l'issue $\omega_i^k$ se réalise pour le match $m_k$ en fonction de l'information $D_{b}$ à un temps $t$ donné.

### Probabilités joueur

Soit $D_j$, un vecteur de variables aléatoires qui représente les informations disponibles pour le joueur à un temps $t$ donné. On définit $\mathbb{P}_{D_{j}}^{joueur.i,k}$ la loi de probabilité définit sur $\Omega_i(m^k)$ en fonction de l'information $D_{j}$ à un temps $t$ donné, la loi sachant $D_{j}$ pour $t$ donné.

On note $t_i^k = \mathbb{P}_{D_{j}}^{joueur.i,k}(X_i^k = 1)$ la probabilité estimée par le joueur que l'issue $\omega_i^k$ se réalise pour le match $m_k$ en fonction de l'information $D_{j}$ à un temps $t$ donné.

## Objectif

L'objectif du joueur et du bookmaker est de maximiser leur bankroll sur le long terme, tout en évitant les risques de ruine / variation trop importante de leur bankroll sur le court terme. Le bookmaker doit aussi attirer les parieurs en proposant des côtes attractives. On se ramèrera à un problème de maximisation du gain à un temps $t$.

La probabilité vraie $r_i^k$ est inconnue pour le joueur et le bookmaker. De même, le vecteur d'information $Y$ est inconnu pour le joueur et le bookmaker, le vecteur $D$ sert de proxy pour $Y$.

Pour un set de matchs donné, un set d'issues données sur ces match et un temps $t$ donné:
- Le joueur peut jouer sur les fractions $f_i^k$ pour chaque match $m_k$ et chaque issue possible $\omega_i^k$ de ce match de sa bankroll $B_{joueur}(t)$ qu'il peut investir. \
Sachant qu'il peut avoir $f_i^k \in [0, 1]$ \
$f_i^k = 0$ signifant qu'il ne pari pas sur l'issue $\omega_i^k$ du match $m_k$ et $f_i^k = 1$ signifiant qu'il parie toute sa bankroll sur l'issue $\omega_i^k$ du match $m_k$.
- Le bookmaker peut jouer sur les côtes $o_i^k$ qu'il propose pour chaque match $m_k$ et chaque issue possible $\omega_i^k$ de ce match.


## Fonction d'utilité

Le joueur et le bookmaker peuvent définir une fonction d'utilité $U$ qu'ils cherchent à optimiser pour optimiser leur gains à un temps t en limitant le risque.
La fonction d'utilité choisie est un choix personnel du joueur et du bookmake, elle en général un trade-off entre l'espérance de gain et le risque (souvent représenté par la variance).


Ainsi maximiser le ROI revient à maximiser la bankroll du joueur et du bookmaker sur le long terme.

Une forme courante de la fonction d'utilité est la suivante:

$U_{joueur}(t) = \mathbb{E}[G_{joueur}(T)] - \lambda \times \text{Var}[G_{joueur}(T)]$

$U_{bookmaker}(t) = \mathbb{E}[G_{bookmaker}(T)] - \lambda \times \text{Var}[G_{bookmaker}(T)]$

avec $\lambda$ un paramètre de régularisation qui permet de contrôler le trade-off entre l'espérance de gain et le risque.

Le joueur ou le bookmaker ne pouvant pas revenir dans le passé ou dans le futur, on peut condu gain du joueur et du bookmaker à un temps $t$ en fonction des paris et des côtes qu'ils ont placé à un temps $t$.

### Objectif joueur

Pour chaque temps $t$ le joueur cherche $\mathbb{F}^*(t)$ tel que:

$\mathbb{F}^*(t) = \text{argmax}_{\mathbb{F}(t)} U_{joueur}(t)$

*Contrainte :* $f_i^k \in [0, 1]$ et $\sum_{i=1}^{N} f_i^k \leq 1$


### Objectif bookmaker

Pour chaque temps $t$ le bookmaker cherche $\mathbb{O}^*(t)$ tel que:

$\mathbb{O}^*(t) = \text{argmax}_{\mathbb{O}(t)} U_{bookmaker}(t)$

*Contrainte :* côtes proposées par le bookmaker attirent les parieurs.

Pour traduire cette contrainte de façon formelle, les bookmakers se fixe une marge $\epsilon^k$ sur chacun des matchs $m_k$. La marge est définie comme suit:

$ \sum_{i=1}^{N} \frac{1}{o_i^k} = 1 + \epsilon^k$

Ainsi, dans la fonction d'utilité à maximiser, le bookmaker prendra en compte la somme investie par les parieurs sur chaque match et chaque issue possible de ce match. Autrement dit le bookmaker cherche à maximiser l'argent investie par les parieurs (en fonction des côtes proposées) tout en maximisant son gain et réduisant son risque sous la contrainte décrit précédement.

$\mathbb{O}^*(t) = \text{argmax}_{\mathbb{O}(t)} U_{bookmaker}(t)$

*Contrainte :* $\sum_{i=1}^{N} \frac{1}{o_i^k} = 1 + \epsilon^k$


---
### Espérance de gain


On peut calculer l'espérance de gain du joueur et du bookmaker comme suit:

$$
\mathbb{E}[G_{joueur}(t)] = \sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times \mathbb{E}[X_i^k] - 1)(t)
$$

$$
\mathbb{E}[G_{joueur}(t)] = \sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times r_i^k - 1)(t)
$$

---

De même pour le bookmaker.

$$
\mathbb{E}[G_{bookmaker}(t)] = \sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (1 - o_i^k \times \mathbb{E}[X_i^k])(t)
$$

$$
\mathbb{E}[G_{bookmaker}(t)] = \sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (1 - o_i^k \times r_i^k)(t)
$$
---
### Variance de gain

On peut calculer la variance de gain du joueur et du bookmaker comme suit

**Hypothèse**:\
On suppose que les matchs qui ont lieu à t sont indépendants entre eux:

$$
\text{Var}[G_{joueur}(t)] = \sum_{k=1}^{M}  \text{Var}[\sum_{i=1}^{N} f_i^k \times (o_i^k \times X_i^k - 1)(t)]
$$

$$
\text{Var}[G_{joueur}(t)] = \sum_{k=1}^{M} [\sum_{i=1}^{N} \text{Var}[f_i^k \times (o_i^k \times X_i^k - 1)(t)] + \sum_{j \neq i}^{N} \text{Cov}[f_i^k \times (o_i^k \times X_i^k - 1)(t), f_j^k \times (o_j^k \times X_j^k - 1)(t)]]
$$

$$
\text{Var}[G_{joueur}(t)] = \sum_{k=1}^{M}  [\sum_{i=1}^{N} (f_i^k)^2 (o_i^k)^2  \text{Var}[X_i^k](t) + 2 \sum_{j \leq i}^{N} f_i^k f_j^k  o_i^k  o_j^k \text{Cov}[X_i^k, X_j^k](t)]
$$


Les varaibles sont binaires $X_i^k \in \{0, 1\}$ et $X_j^k \in \{0, 1\}$, on a alors

$$
\text{Var}[X_i^k] = (1 - r_i^k)r_i^k + r_i^k(1 - r_i^k)
$$

$$
\text{Var}[X_i^k] = r_i^k(1 - r_i^k)
$$

**Condition**:\
Si on a que pour un match $k$, car si une issue se réalise les autres non. On a alors  $P(X_i^k = 1, X_j^k = 1) = 0$ et $\text{Cov}[X_i^k, X_j^k] = -r_i^k r_j^k$

$$
\text{Cov}(X,Y) = \sum_{i=1}^{N} \sum_{j=1}^{N} x_i y_jP(X=x_i,  Y=y_j) - E[X]E[Y]
$$

$$
\text{Var}[G_{joueur}(t)] = \sum_{k=1}^{M}  [\sum_{i=1}^{N} (f_i^k)^2 (o_i^k)^2  r_i^k(1 - r_i^k) - 2 \sum_{j \leq i}^{N} f_i^k f_j^k  o_i^k  o_j^k r_i^k r_j^k]
$$



De même pour le bookmaker.

$$
\text{Var}[G_{bookmaker}(t)] = \sum_{k=1}^{M}  \text{Var}[\sum_{i=1}^{N} f_i^k \times (1 - o_i^k \times X_i^k)(t)]
$$

$$
\text{Var}[G_{bookmaker}(t)] = \text{Var}[G_{joueur}(t)]
$$




## Point de vue Joueur
### Critère de Kelly

Le critère de Kelly peut être considéré comme une certaine forme de la fonction d'utilité. Il est défini comme suit, pour $t$ fixé:

$
U^{kelly}_{joueur} = \mathbb{E}[\log(G_{joueur})] 
$

On suppose que les mêmes matchs sont joués un grand nombre de fois T.


$
G_{joueur}(T) = B_{joueur}(0) \times \prod_{t=0}^{T-1} [1+\sum_{k=1}^{M} \sum_{i=1}^{N}f_i^k \times (o_i^k \times X_i^k - 1)](t)
$

Pour un match et pour une seule issue, on a:

$
G_{joueur}(T) = B_{joueur}(0) \times \prod_{t=0}^{T-1} [1+f \times (o \times X - 1)](t)
$


On suppose que sur les T essaies, on gagne $pT$ fois et on perd $(1-p)T$ fois. On a alors:

$
G_{joueur}(T) = B_{joueur}(0) \times [1+f \times (o  - 1)]^{pT} \times [1-f]^{(1-p)T}  
$

$
log(G_{joueur}(T)) = log(B_{joueur}(0)) + pT \times log(1+f \times (o  - 1)) + (1-p)T \times log(1-f)
$

On prend la moyenne de $log(G_{joueur}(T))$ 

$
1/T \times \sum_{t=0}^{T-1} log(G_{joueur}(T)) = log(B_{joueur}(0)) + p \times log(1+f \times (o  - 1)) + (1-p) \times log(1-f)
$

Quand T tend vers l'infini, on a: $p \to r$ et $(1-r) \to 1-r$ la probabilité de gagner et de perdre.

$
\lim_{T \to \infty} 1/T \times \sum_{t=0}^{T-1} log(G_{joueur}(T)) = log(B_{joueur}(0)) + r \times log(1+f \times (o  - 1)) + (1-r) \times log(1-f)
$

On a un estimateur de l'esperance de $log(G_{joueur}(T))$ qui est:

$
\mathbb{E}[log(G_{joueur}(T))] = log(B_{joueur}(0)) + r \times log(1+f \times (o  - 1)) + (1-r) \times log(1-f)
$

On peut alors trouver $f$ qui maximise $\mathbb{E}[log(G_{joueur}(T))]$

$
\dfrac{\partial \mathbb{E}[log(G_{joueur}(T))]}{\partial f} |_{f=f^*} = 0
$

$
<=>\dfrac{\partial \mathbb{E}[log(G_{joueur}(T))]}{\partial f}|_{f=f^*} = \dfrac{r \times (o-1)}{1+f^* \times (o-1)} - \dfrac{1-r}{1-f^*} = 0
$

$
<=> f^* = r - \dfrac{1-r}{o-1}
$


On a alors la fraction de la bankroll que le joueur doit miser pour maximiser son gain à long terme.



### Sharpe Ratio

Le Sharpe Ratio est un autre critère de performance. Il est défini comme suit:

$
U^{sharpe}_{joueur} = \dfrac{\mathbb{E}[G_{joueur}]}{\sqrt{\text{Var}[G_{joueur}]}}
$

On peut alors chercher les fractions $f_i^k$ qui maximisent le Sharpe Ratio.

Dans le cas d'un seul match et d'une seule issue, on a:

$
U^{sharpe}_{joueur} = \dfrac{\mathbb{E}[G_{joueur}]}{\sqrt{\text{Var}[G_{joueur}]}}
$

$
= \dfrac{f \times (o \times r - 1)}{\sqrt{f^2 \times (o^2 \times r - 1)^2}}
$

On peut alors chercher $f$ qui maximise le Sharpe Ratio.

$
\dfrac{\partial U^{sharpe}_{joueur}}{\partial f} |_{f=f^*} = 0
$


$
<=> \dfrac{\partial U^{sharpe}_{joueur}}{\partial f} |_{f=f^*} = \dfrac{o \times r - 1}{\sqrt{f^2 \times (o^2 \times r - 1)^2}} - \dfrac{f \times (o^2 \times r - 1) \times 2 \times f}{2 \times \sqrt{f^2 \times (o^2 \times r - 1)^2}} = 0
$


$
<=> f^* = \dfrac{o \times r - 1}{o^2 \times r - 1}
$



## Problème d'optimisation

### Esperance de gain pour l'utilité

$$
U_{joueur}(t) = \mathbb{E}[G_{joueur}(t)]
$$

$$
U_{joueur}(t) = \sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times r_i^k - 1)(t)
$$

On peut alors chercher $f_i^k$ qui maximise l'espérance de gain pour l'utilité.

$$
\argmax_{f_i^k} U_{joueur}(t)
$$

Sous les conditions

$$
f_i^k \in [0, 1]
$$


$$
\sum_{i=1}^{N} f_i^k \leq 1
$$

---

### Kelly pour l'utilité

$$
U_{joueur}(t) = \mathbb{E}[log(G_{joueur}(t))]
$$

$$
U_{joueur}(t) = \mathbb{E}[log(\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times X_i^k - 1))(t)]
$$

Si on considère que  $ 1 - G_{joueur}(t) $ est proche de 0, on peut approximer 

$$
log(G_{joueur}(t)) = log(1 - (-G_{joueur}(t)+1))
$$

$$
log(G_{joueur}(t)) = -(-G_{joueur}(t)+1) - \dfrac{(-G_{joueur}(t)+1)^2}{2} - \dfrac{(-G_{joueur}(t)+1)^3}{3} - o((-G_{joueur}(t)+1)^4)
$$

$$
log(G_{joueur}(t)) \approx G_{joueur}(t)-1 - \dfrac{(-G_{joueur}(t)+1)^2}{2}
$$

$$
log(G_{joueur}(t)) \approx G_{joueur}(t)-1 - \dfrac{G_{joueur}(t)^2}{2} + G_{joueur}(t) - \dfrac{1}{2}
$$

$$
log(G_{joueur}(t)) \approx 2 \times G_{joueur}(t) - \dfrac{G_{joueur}(t)^2}{2} - \dfrac{3}{2}
$$

$$
\text{E}[log(G_{joueur}(t))] \approx 2 \times \text{E}[G_{joueur}(t)] - \dfrac{\text{E}[G_{joueur}(t)^2]}{2} - \dfrac{3}{2}
$$

$$
\text{E}[log(G_{joueur}(t))] \approx 2 \times \text{E}[G_{joueur}(t)] - \dfrac{\text{Var}[G_{joueur}(t)] + \text{E}[G_{joueur}(t)]^2}{2} - \dfrac{3}{2}
$$

On peut alors chercher $f_i^k$ qui maximise l'espérance de gain pour l'utilité.

$$
\argmax_{f_i^k} U_{joueur}(t)
$$

Sous les conditions

$$
f_i^k \in [0, 1]
$$

$$
\sum_{i=1}^{N} f_i^k \leq 1
$$

---

### Sharpe Ratio pour l'utilité

$$
U_{joueur}(t) = \dfrac{\mathbb{E}[G_{joueur}(t)]}{\sqrt{\text{Var}[G_{joueur}(t)]}}
$$

$$
U_{joueur}(t) = \dfrac{\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times r_i^k - 1)(t)}{\sqrt{\sum_{k=1}^{M}  \text{Var}[\sum_{i=1}^{N} f_i^k \times (o_i^k \times X_i^k - 1)(t)]}}
$$

Si pour chaque match $k$, on a que si une issue se réalise les autres non.

$$
U_{joueur}(t) = \dfrac{\sum_{k=1}^{M} \sum_{i=1}^{N} f_i^k \times (o_i^k \times r_i^k - 1)(t)}{\sqrt{\sum_{k=1}^{M}  [\sum_{i=1}^{N} (f_i^k)^2 (o_i^k)^2  r_i^k(1 - r_i^k) - 2 \sum_{j \leq i}^{N} f_i^k f_j^k  o_i^k  o_j^k r_i^k r_j^k]}}
$$

On peut alors chercher $f_i^k$ qui maximise le Sharpe Ratio pour l'utilité.

$$
\argmax_{f_i^k} U_{joueur}(t)
$$

Sous les conditions

$$
f_i^k \in [0, 1]
$$

$$
\sum_{i=1}^{N} f_i^k \leq 1
$$


