from django.contrib import admin
from .models import (
    Categorie,
    Produit,
    MouvementStock,
    Client,
    AdresseLivraison,
    Commande,
    LigneCommande,
    Facture,
    Paiement,
    Livreur,
    Livraison,
)


# Register your models here.

class AdresseLivraisonInline(admin.TabularInline):
    model = AdresseLivraison
    extra = 1


class LigneCommandeInline(admin.TabularInline):
    model = LigneCommande
    extra = 1


class PaiementInline(admin.TabularInline):
    model = Paiement
    extra = 0
    readonly_fields = ("date_paiement",)


# ======================================================
# CATEGORIE
# ======================================================

@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)
    ordering = ("nom",)


# ======================================================
# PRODUIT
# ======================================================

@admin.register(Produit)
class ProduitAdmin(admin.ModelAdmin):
    list_display = (
        "reference",
        "nom",
        "categorie",
        "prix",
        "disponible",
        "soumis_stock",
        "stock",
        "temps_preparation",
    )

    list_filter = (
        "categorie",
        "disponible",
        "soumis_stock",
    )

    search_fields = (
        "reference",
        "nom",
    )

    ordering = ("nom",)


# ======================================================
# MOUVEMENT DE STOCK
# ======================================================

@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = (
        "produit",
        "type_mouvement",
        "quantite",
        "date",
    )

    list_filter = (
        "type_mouvement",
        "date",
    )

    search_fields = (
        "produit__nom",
        "description",
    )

    readonly_fields = ("date",)


# ======================================================
# CLIENT
# ======================================================

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "nom",
        "prenom",
        "telephone",
        "email",
    )

    search_fields = (
        "nom",
        "prenom",
        "telephone",
    )

    inlines = [
        AdresseLivraisonInline,
    ]


# ======================================================
# ADRESSE LIVRAISON
# ======================================================

@admin.register(AdresseLivraison)
class AdresseLivraisonAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "nom",
        "adresse",
    )

    search_fields = (
        "client__nom",
        "adresse",
    )


# ======================================================
# COMMANDE
# ======================================================

@admin.register(Commande)
class CommandeAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "client",
        "date_commande",
        "total",
        "statut",
    )

    list_filter = (
        "statut",
        "date_commande",
    )

    search_fields = (
        "numero",
        "client__nom",
        "client__prenom",
    )

    date_hierarchy = "date_commande"

    inlines = [
        LigneCommandeInline,
    ]


# ======================================================
# LIGNE COMMANDE
# ======================================================

@admin.register(LigneCommande)
class LigneCommandeAdmin(admin.ModelAdmin):
    list_display = (
        "commande",
        "produit",
        "quantite",
        "prix_unitaire",
        "sous_total",
    )

    search_fields = (
        "commande__numero",
        "produit__nom",
    )


# ======================================================
# FACTURE
# ======================================================

@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = (
        "numero",
        "commande",
        "montant",
        "statut",
        "date_facture",
    )

    list_filter = (
        "statut",
        "date_facture",
    )

    search_fields = (
        "numero",
        "commande__numero",
    )

    inlines = [
        PaiementInline,
    ]


# ======================================================
# PAIEMENT
# ======================================================

@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "facture",
        "montant",
        "mode_paiement",
        "statut",
        "date_paiement",
    )

    list_filter = (
        "mode_paiement",
        "statut",
    )

    search_fields = (
        "facture__numero",
        "reference",
    )


# ======================================================
# LIVREUR
# ======================================================

@admin.register(Livreur)
class LivreurAdmin(admin.ModelAdmin):
    list_display = (
        "nom",
        "telephone",
        "plaque_moto",
        "etat",
    )

    list_filter = (
        "etat",
    )

    search_fields = (
        "nom",
        "telephone",
    )


# ======================================================
# LIVRAISON
# ======================================================

@admin.register(Livraison)
class LivraisonAdmin(admin.ModelAdmin):
    list_display = (
        "commande",
        "livreur",
        "date_livraison",
        "cout_livraison",
        "statut",
    )

    list_filter = (
        "statut",
    )

    search_fields = (
        "commande__numero",
        "livreur__nom",
    )

    date_hierarchy = "date_livraison"