# Rapport de stage

1. Introduction
    - Contexte général des paris sportifs
    - Problématique abordée : Optimisation des gains dans les paris sportifs
    - Objectifs du stage

2. Présentation théorique et recherche préliminaire
  2.1 Formalisation mathématique des paris sportifs
    - Description du système de paris sportif (Joueur - Bookmaker)​
    - Division des différents systèmes de paris (côtes, pot...)
    - Types de paris (1X2, over/under, etc.)
  2.2 Définition du problème​
    - Cadrage du système étudié​
    - Définition du gain (Joueur – Bookmaker)​
    - Clarification de l'objectif (Joueur – Bookmaker)​
    - Fonction d'utilité​ - Rôle des fonctions d’utilité dans la gestion du risque
    - Formalisation de l'objectif (Joueur – Bookmaker)​
    - Problème de connaissance (probabilité réelle, somme d'argent investie)​
    - Avantages joueur Vs avantages bookmaker

3. Conception et mise en place de la solution
    3.1 Architecture générale du système
        - Présentation des différents composants
        - Interactions entre les composants
        - Flux de données
    3.2 Collecte des données
        - Sources de données utilisées
        - Description des données collectées
        - Méthodes de collecte (scrapping, API, etc.)
    3.3 Stockage des données
        - Choix de la base de données
        - Modèle de données
        - Intégration des données collectées
    3.4 Module de prédiction
    3.5 Module d'optimisation
    3.6 Interface utilisateur et monitoring
    3.7 API de communication entre les composants

4. Modélisation prédictive de l'issue des matchs
    4.1. Métriques de performance (accuracy, precision, recall, F1-score) et critères de sélection
    4.2. Exploration et choix des features
    4.3. Exploration et choix du modèle de prédiction
    4.4. Entrainement et réentrainement du modèle
    4.5. Evaluation du modèle

5. Optimisation des parts de bankroll
    5.1 Formulation du problème d'optimisation
    5.2 Formulation des différentes fonction d'utilité
    5.3 Algorithmes d'optimisation utilisés
    5.4 Présentation des différentes stratégies
    5.5 Monte Carlo simulation - Approche stochastique
    5.6 Résultats et discussion

6. Développement du système complet et mise en production
    6.1 Architecture en micro services, frameworks et communication
    6.2 Dockerisation et docker compose
    6.3 Déploiement sur Kubernetes
    6.4 Déploiement sur Azure (User group, Azure DevOps, Azure container registry, Azure Kubernetes Service)

7. Critiques, perspectives et améliorations futures
  - Critiques et Améliorations possibles du modèle de prédiction (donnée supplémentaires, modèles plus complexes, etc.)
  - Critiques et Améliorations possibles au niveau des fonction d'utilité
  - Critiques et Améliorations possibles au niveau des startégies
  - Modèle tout en un (avec historique des côtes)
  - Exploration du point de vue bookmaker
  - Adaptation à d'autres types de paris ou d'autres sports
  - Possibilités d'extension du système (scalabilité, API publique, etc.)

8. Conclusion

9. Annexes

