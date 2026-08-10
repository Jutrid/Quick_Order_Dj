# Quick Order DJ

Application web de gestion de **commandes**, **livraisons**, **factures** et **paiements** pour un restaurant / service de livraison.

Construite avec **Django**, avec un front-end responsive (Bootstrap 5, jQuery, Select2, DataTables, SweetAlert 2 et Leaflet).

---

## Sommaire

- [Fonctionnalités](#fonctionnalités)
- [Technique](#technique)
- [Installation](#installation)
- [Utilisation](#utilisation)
- [Structure du projet](#structure-du-projet)
- [Tests](#tests)

---

## Fonctionnalités

### Commandes
- Création et modification de commandes avec **lignes de commande dynamiques** (produits, quantités, sous-totaux et total recalculés en temps réel).
- Numérotation automatique : `CMD-000001`, `CMD-000002`, ...
- Champ **« à livrer »** : si coché, les champs *adresse de livraison*, *livreur* et *frais de livraison* deviennent visibles et sont enregistrés.
- Statuts : En attente, En préparation, Prête, En livraison, Livrée, Annulée.
  - **Verrouillage** : à partir de **Prête**, seul le passage à **Annulée** est autorisé.
  - Passage à **Prête** → génération automatique de la **facture** (`FAC-{id}`) et de la **livraison** (si la commande est à livrer).

### Factures
- Générées automatiquement quand une commande passe au statut **Prête** (montant = total de la commande).
- Statuts : Non payée, Partiellement payée, Payée.
- Liste avec statistiques (total, payées, non payées, montant total).
- Bouton **Payer** : SweetAlert avec champ montant, limité au **reste à payer** (montant − somme des paiements validés). Le statut de la facture est mis à jour automatiquement.

### Paiements
- Enregistrement manuel d'un paiement (facture, montant, mode de paiement, référence, statut).
- Modes : Espèces, Mobile Money, Carte bancaire, Paiement en ligne.
- Liste avec statistiques (total, validés, en attente, montant encaissé).

### Livraisons
- Création automatique au passage de la commande à **Prête** si « à livrer » est coché (adresse et coût repris de la commande, livreur assigné si précisé).
- Changement de statut via SweetAlert : En attente, En route, Livrée, Annulée (la date de livraison est renseignée automatiquement à « Livrée »).
- **Détail de la livraison** avec carte Leaflet centrée sur l'adresse (si latitude / longitude renseignées).

### Livreurs
- CRUD complet : liste (photo, téléphone, plaque moto, nombre de livraisons, état), ajout, modification, suppression.
- États : Disponible, En livraison, Inactif.

### Produits & catalogue
- Catégories, tailles et produits (référence, prix, image, gestion de stock optionnelle, temps de préparation).

### Clients & adresses
- Gestion des clients et de leurs adresses de livraison, avec **latitude / longitude** affichées sur une carte Leaflet, filtrage par client et recherche.

### Utilisateurs & groupes
- Connexion, inscription, déconnexion.
- Gestion des utilisateurs et des groupes depuis le menu **Paramètres**.

### Interface
- Interface responsive en français (Bootstrap 5).
- Confirmations et formulaires interactifs avec **SweetAlert 2**.
- Tableaux filtrables avec **DataTables**.
- Cartes interactives **Leaflet** (OpenStreetMap / CARTO).

---

## Technique

### Stack

| Élément         | Technologie                                             |
|-----------------|---------------------------------------------------------|
| Langage         | Python 3                                                |
| Framework       | Django 6.0                                              |
| Base de données | SQLite (par défaut) — compatible PostgreSQL (`psycopg`) |
| Front-end       | Bootstrap 5, jQuery, Select2, DataTables, SweetAlert 2, Leaflet |
| Images          | Pillow                                                  |
| API             | Django REST Framework (installé, extensible)            |

### Points d'intégration notables

- **Factures automatiques** : dans `order_app/views.py`, la vue `commande_statut` crée la `Facture` au passage à `PRETE` (montant = `commande.total`), puis redirige avec un paramètre `?facture_created=...` affiché en notification SweetAlert.
- **Livraisons automatiques** : la même vue crée une `Livraison` quand `commande.a_livree` est vrai (adresse, coût et livreur repris de la commande).
- **Reste à payer** : propriétés `montant_paye` / `montant_restant` sur le modèle `Facture` (somme des paiements `VALIDE`). Le paiement est validé côté client **et** côté serveur (`facture_paiement`).
- **Statuts verrouillés** : contrôle serveur dans `commande_statut` + restriction du `<select>` en JavaScript.

### Modèles principaux (`order_app/models.py`)

- `Categorie`, `TailleProduit`, `Produit`
- `Client`, `AdresseLivraison`
- `Commande` (FK `Client`, FK `AdresseLivraison`, FK `Livreur`, `a_livree`), `LigneCommande`
- `Facture` (OneToOne `Commande`), `Paiement` (FK `Facture`)
- `Livreur`, `Livraison` (OneToOne `Commande`, FK `Livreur`)

---

## Installation

### Prérequis

- Python 3.10+
- pip

### Étapes

```bash
# 1. Cloner le dépôt
git clone <url-du-depot> quick_order_dj
cd quick_order_dj

# 2. Créer et activer un environnement virtuel
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux / macOS

# 3. Installer les dépendances
pip install -r requirements.txt

# 4. Appliquer les migrations (base de données)
python manage.py migrate

# 5. Créer un superutilisateur
python manage.py createsuperuser

# 6. Lancer le serveur de développement
python manage.py runserver
```

L'application est alors accessible sur [http://127.0.0.1:8000/](http://127.0.0.1:8000/) et l'administration Django sur [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

> **Note** : les fichiers statiques sont servis depuis le dossier `static/` en développement (`DEBUG = True`). Pour un déploiement en production, lancez `python manage.py collectstatic` et modifiez `SECRET_KEY`, `DEBUG` et `ALLOWED_HOSTS` dans `quick_order_dj/settings.py`.

---

## Utilisation

1. **Se connecter** sur la page d'accueil (ou s'inscrire via `/register/`).
2. **Paramétrer le catalogue** : ajouter des catégories, des tailles puis des produits (menu **Products**).
3. **Ajouter des clients** et leurs adresses de livraison.
4. **Créer une commande** : choisir le client, ajouter les produits (lignes dynamiques), cocher **« à livrer »** si nécessaire (adresse, livreur, frais).
5. **Faire progresser la commande** : passer au statut **Prête** → une **facture** est générée automatiquement (et une **livraison** si la commande est à livrer).
6. **Encaisser les paiements** : dans la liste des factures, cliquer sur **Payer** et saisir un montant ≤ au reste à payer.
7. **Suivre les livraisons** : changer le statut (En attente → En route → Livrée) et consulter le détail avec la carte.

---

## Structure du projet

```
quick_order_dj/
├── manage.py                 # Point d'entrée Django
├── requirements.txt          # Dépendances Python
├── quick_order_dj/           # Configuration du projet (settings, urls, wsgi, asgi)
├── order_app/                # Application principale
│   ├── models.py             # Modèles (Commande, Facture, Paiement, Livraison, ...)
│   ├── views.py              # Vues (listes, formulaires, statuts, paiement, détail)
│   ├── forms.py              # Formulaires Django
│   ├── urls.py               # Routes de l'application
│   ├── admin.py              # Interface d'administration
│   ├── tests.py              # Tests unitaires
│   └── migrations/           # Migrations de base de données
├── user_app/                 # Authentification, utilisateurs, groupes
├── templates/                # Templates HTML (listes, formulaires, détail)
│   ├── base.html             # Gabarit principal (sidebar, navbar)
│   ├── order_list.html
│   ├── factures_list.html
│   ├── paiements_list.html
│   ├── livraisons_list.html
│   ├── livraison_detail.html
│   ├── livreurs_list.html
│   ├── clients_list.html
│   ├── products_list.html
│   └── forms/                # Templates de formulaires
└── static/                   # CSS, JS, images (karla, Leaflet, Select2, ...)
```

---

## Tests

```bash
python manage.py check
python manage.py test order_app
```

Les tests couvrent notamment :
- la génération automatique des factures et des livraisons ;
- le verrouillage des statuts de commande ;
- l'encaissement des paiements (total, partiel, dépassement refusé) ;
- les listes et formulaires fonctionnels (livreurs, livraisons, adresses) ;
- le détail de livraison avec carte.
