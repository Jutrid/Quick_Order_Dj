# Description détaillée de la modélisation de l'application de livraison

## Introduction

Cette modélisation représente une application de gestion d'un restaurant
spécialisé dans la vente et la livraison de **tacos, pizzas, crèmes
glacées et boissons**. Elle couvre la gestion du catalogue, des clients,
des commandes, des paiements, des factures et des livraisons.

------------------------------------------------------------------------

# 1. Catégorie

La classe **Categorie** permet de regrouper les produits selon leur
nature.

Exemples : - Pizza - Tacos - Crème glacée - Boisson

Chaque catégorie peut contenir plusieurs produits tandis qu'un produit
appartient à une seule catégorie.

------------------------------------------------------------------------

# 2. Produit

La classe **Produit** représente les articles vendus.

Elle contient notamment : - une référence unique (générée
automatiquement) ; - le nom du produit ; - une description ; - son prix
; - une image ; - son temps de préparation ; - son état de disponibilité
; - une gestion de stock optionnelle.

Chaque produit est associé à une catégorie.

------------------------------------------------------------------------

# 3. Client

Cette classe représente les clients.

Informations enregistrées : - nom ; - prénom ; - téléphone ; - adresse
e-mail.

Un client peut passer plusieurs commandes et posséder plusieurs adresses
de livraison.

------------------------------------------------------------------------

# 4. AdresseLivraison

Cette entité permet à un client d'enregistrer plusieurs adresses.

Exemples : - Maison - Travail - Université

Chaque adresse peut également contenir des coordonnées GPS (latitude et
longitude).

------------------------------------------------------------------------

# 5. Commande

La commande est l'élément central de l'application.

Elle contient : - un numéro unique ; - le client ; - l'adresse de
livraison ; - la date ; - les frais de livraison ; - le montant total
; - un commentaire (ex. : « sans oignons », « sauce piquante ») ; - une
heure souhaitée de livraison ; - un statut.

Les statuts possibles sont : - En attente - En préparation - Prête - En
livraison - Livrée - Annulée

Une commande possède plusieurs lignes de commande.

------------------------------------------------------------------------

# 6. LigneCommande

Chaque ligne correspond à un produit commandé.

Elle contient : - le produit ; - la quantité ; - le prix unitaire ; - le
sous-total ; - une note de préparation.

Le sous-total est calculé automatiquement.

------------------------------------------------------------------------

# 7. Facture

Une facture est générée pour chaque commande.

Elle contient : - un numéro ; - une date ; - le montant ; - un statut de
paiement.

Relation : - une commande possède une seule facture.

------------------------------------------------------------------------

# 8. Paiement

Une facture peut recevoir un ou plusieurs paiements.

Les modes de paiement sont : - Espèces - Mobile Money - Carte bancaire -
Paiement en ligne

Chaque paiement possède un montant, une référence et un statut.

------------------------------------------------------------------------

# 9. Livreur

Cette classe représente les personnes chargées de livrer les commandes.

Informations : - nom ; - téléphone ; - photo ; - plaque de la moto ; -
état (Disponible, En livraison, Inactif).

------------------------------------------------------------------------

# 10. Livraison

Une livraison est associée à une commande.

Elle contient : - le livreur ; - l'adresse ; - la date de livraison ; -
l'heure de départ ; - l'heure d'arrivée ; - le coût de livraison ; - le
statut.

Les statuts possibles sont : - En attente - En route - Livrée - Annulée

------------------------------------------------------------------------

# Relations entre les classes

-   Une **Catégorie** possède plusieurs **Produits**.
-   Un **Client** possède plusieurs **Adresses de livraison**.
-   Un **Client** peut effectuer plusieurs **Commandes**.
-   Une **Commande** contient plusieurs **Lignes de commande**.
-   Chaque **Ligne de commande** référence un seul **Produit**.
-   Une **Commande** génère une seule **Facture**.
-   Une **Facture** peut recevoir plusieurs **Paiements**.
-   Une **Commande** possède une seule **Livraison**.
-   Un **Livreur** peut réaliser plusieurs **Livraisons**.

------------------------------------------------------------------------

# Conclusion

Cette modélisation est adaptée à une application de restauration rapide
avec livraison. Elle sépare clairement les responsabilités entre les
produits, les clients, les commandes, la facturation, les paiements et
la livraison. Elle est évolutive et peut accueillir par la suite des
fonctionnalités telles que la gestion des ingrédients, des promotions,
du suivi GPS en temps réel ou encore des programmes de fidélité.
