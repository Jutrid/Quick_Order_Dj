from django.db import models
from django.db.models import F, Sum
from django.db.models.functions import Greatest


# =====================================================
# CATEGORIE
# =====================================================

class Categorie(models.Model):
    nom = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["nom"]
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def __str__(self):
        return self.nom


# =====================================================
# PRODUIT
# =====================================================

class Produit(models.Model):
    categorie = models.ForeignKey(
        Categorie,
        on_delete=models.PROTECT,
        related_name="produits"
    )

    reference = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
        help_text="Générée automatiquement (PROD-xxxxxx)"
    )

    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    prix = models.DecimalField(max_digits=10, decimal_places=2)

    image = models.ImageField(
        upload_to="produits/",
        blank=True,
        null=True
    )

    disponible = models.BooleanField(default=True)

    soumis_stock = models.BooleanField(
        default=False,
        help_text="Cochez si le produit doit être géré en stock"
    )

    stock = models.PositiveIntegerField(
        default=0,
        help_text="Quantité en stock"
    )

    temps_preparation_defini = models.BooleanField(
        default=False,
        help_text="Cochez pour définir un temps de préparation"
    )

    temps_preparation = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Temps de préparation en minutes"
    )

    class Meta:
        ordering = ["nom"]

    def __str__(self):
        return self.nom

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not self.reference:
            self.reference = f"PROD-{self.pk:06d}"
            super().save(update_fields=["reference"])


# =====================================================
# MOUVEMENT DE STOCK
# =====================================================

class MouvementStock(models.Model):

    class TypeMouvement(models.TextChoices):
        ENTREE = "ENTREE", "Entrée"
        SORTIE = "SORTIE", "Sortie"

    produit = models.ForeignKey(
        Produit,
        on_delete=models.CASCADE,
        related_name="mouvements"
    )

    date = models.DateTimeField(auto_now_add=True)

    type_mouvement = models.CharField(
        max_length=10,
        choices=TypeMouvement.choices
    )

    quantite = models.PositiveIntegerField()

    description = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex : Réception fournisseur, Casse, Réapprovisionnement..."
    )

    class Meta:
        ordering = ["-date"]
        verbose_name = "Mouvement de stock"
        verbose_name_plural = "Mouvements de stock"

    def __str__(self):
        return f"{self.produit.nom} — {self.get_type_mouvement_display()} — {self.quantite}"


# =====================================================
# CLIENT
# =====================================================

class Client(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, blank=True)

    telephone = models.CharField(max_length=20)

    email = models.EmailField(blank=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"


# =====================================================
# ADRESSE DE LIVRAISON
# =====================================================

class AdresseLivraison(models.Model):

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="adresses"
    )

    nom = models.CharField(
        max_length=50,
        help_text="Maison, Travail..."
    )

    adresse = models.TextField()

    latitude = models.DecimalField(
        max_digits=20,
        decimal_places=17,
        null=True,
        blank=True
    )

    longitude = models.DecimalField(
        max_digits=20,
        decimal_places=17,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.client} - {self.nom}"


# =====================================================
# COMMANDE
# =====================================================

class Commande(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        EN_PREPARATION = "EN_PREPARATION", "En préparation"
        PRETE = "PRETE", "Prête"
        EN_LIVRAISON = "EN_LIVRAISON", "En livraison"
        LIVREE = "LIVREE", "Livrée"
        ANNULEE = "ANNULEE", "Annulée"

    numero = models.CharField(max_length=30, unique=True)

    client = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name="commandes"
    )

    adresse_livraison = models.ForeignKey(
        AdresseLivraison,
        on_delete=models.PROTECT,
        null=True,
        blank=True
    )

    date_commande = models.DateTimeField(auto_now_add=True)

    frais_livraison = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    total = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    commentaire = models.TextField(blank=True)

    heure_souhaitee = models.TimeField(
        null=True,
        blank=True
    )

    a_livree = models.BooleanField(
        default=False,
        help_text="Cochez si la commande doit être livrée"
    )

    livreur = models.ForeignKey(
        'Livreur',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="commandes"
    )

    statut = models.CharField(
        max_length=30,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )

    def __str__(self):
        return self.numero

    def diminuer_stock(self):
        for ligne in self.lignes.select_related('produit'):
            if ligne.produit.soumis_stock:
                Produit.objects.filter(pk=ligne.produit_id).update(
                    stock=Greatest(F('stock') - ligne.quantite, 0)
                )
                MouvementStock.objects.create(
                    produit_id=ligne.produit_id,
                    type_mouvement=MouvementStock.TypeMouvement.SORTIE,
                    quantite=ligne.quantite,
                    description=f"Commande {self.numero}",
                )

    def rendre_stock(self):
        for ligne in self.lignes.select_related('produit'):
            if ligne.produit.soumis_stock:
                Produit.objects.filter(pk=ligne.produit_id).update(
                    stock=F('stock') + ligne.quantite
                )
                MouvementStock.objects.create(
                    produit_id=ligne.produit_id,
                    type_mouvement=MouvementStock.TypeMouvement.ENTREE,
                    quantite=ligne.quantite,
                    description=f"Retour commande {self.numero}",
                )


# =====================================================
# LIGNE COMMANDE
# =====================================================

class LigneCommande(models.Model):

    commande = models.ForeignKey(
        Commande,
        on_delete=models.CASCADE,
        related_name="lignes"
    )

    produit = models.ForeignKey(
        Produit,
        on_delete=models.PROTECT
    )

    quantite = models.PositiveIntegerField(default=1)

    prix_unitaire = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    sous_total = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    note = models.CharField(
        max_length=200,
        blank=True,
        help_text="Ex: Sans oignons, Sauce piquante..."
    )

    def save(self, *args, **kwargs):
        self.sous_total = self.quantite * self.prix_unitaire
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.commande.numero} - {self.produit.nom}"


# =====================================================
# FACTURE
# =====================================================

class Facture(models.Model):

    class Statut(models.TextChoices):
        NON_PAYEE = "NON_PAYEE", "Non payée"
        PARTIELLE = "PARTIELLE", "Partiellement payée"
        PAYEE = "PAYEE", "Payée"

    commande = models.OneToOneField(
        Commande,
        on_delete=models.CASCADE,
        related_name="facture"
    )

    numero = models.CharField(max_length=30, unique=True)

    date_facture = models.DateTimeField(auto_now_add=True)

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.NON_PAYEE
    )

    @property
    def montant_paye(self):
        return self.paiements.filter(statut=Paiement.Statut.VALIDE).aggregate(
            total=Sum('montant')
        )['total'] or 0

    @property
    def montant_restant(self):
        return self.montant - self.montant_paye

    def __str__(self):
        return self.numero


# =====================================================
# PAIEMENT
# =====================================================

class Paiement(models.Model):

    class ModePaiement(models.TextChoices):
        ESPECES = "ESPECES", "Espèces"
        MOBILE_MONEY = "MOBILE_MONEY", "Mobile Money"
        CARTE = "CARTE", "Carte bancaire"
        EN_LIGNE = "EN_LIGNE", "Paiement en ligne"

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        VALIDE = "VALIDE", "Validé"
        ANNULE = "ANNULE", "Annulé"

    facture = models.ForeignKey(
        Facture,
        on_delete=models.CASCADE,
        related_name="paiements"
    )

    date_paiement = models.DateTimeField(auto_now_add=True)

    montant = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    mode_paiement = models.CharField(
        max_length=20,
        choices=ModePaiement.choices
    )

    reference = models.CharField(
        max_length=100,
        blank=True
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )

    def __str__(self):
        return f"{self.facture.numero} - {self.montant}"


# =====================================================
# LIVREUR
# =====================================================

class Livreur(models.Model):

    class Etat(models.TextChoices):
        DISPONIBLE = "DISPONIBLE", "Disponible"
        EN_LIVRAISON = "EN_LIVRAISON", "En livraison"
        INACTIF = "INACTIF", "Inactif"

    nom = models.CharField(max_length=100)

    telephone = models.CharField(max_length=20)

    photo = models.ImageField(
        upload_to="livreurs/",
        blank=True,
        null=True
    )

    plaque_moto = models.CharField(
        max_length=30,
        blank=True
    )

    etat = models.CharField(
        max_length=20,
        choices=Etat.choices,
        default=Etat.DISPONIBLE
    )

    def __str__(self):
        return self.nom


# =====================================================
# LIVRAISON
# =====================================================

class Livraison(models.Model):

    class Statut(models.TextChoices):
        EN_ATTENTE = "EN_ATTENTE", "En attente"
        EN_ROUTE = "EN_ROUTE", "En route"
        LIVREE = "LIVREE", "Livrée"
        ANNULEE = "ANNULEE", "Annulée"

    commande = models.OneToOneField(
        Commande,
        on_delete=models.CASCADE,
        related_name="livraison"
    )

    livreur = models.ForeignKey(
        Livreur,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="livraisons"
    )

    adresse = models.TextField()

    date_livraison = models.DateTimeField(
        null=True,
        blank=True
    )

    heure_depart = models.DateTimeField(
        null=True,
        blank=True
    )

    heure_arrivee = models.DateTimeField(
        null=True,
        blank=True
    )

    cout_livraison = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=0
    )

    statut = models.CharField(
        max_length=20,
        choices=Statut.choices,
        default=Statut.EN_ATTENTE
    )

    def __str__(self):
        return f"Livraison {self.commande.numero}"