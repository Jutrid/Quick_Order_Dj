from decimal import Decimal, InvalidOperation

from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Count, ProtectedError, Q, Sum
from django.forms import inlineformset_factory
from django.shortcuts import get_object_or_404, redirect, render, reverse
from django.utils import timezone

from .forms import (
    AdresseLivraisonForm,
    CategorieForm,
    ClientForm,
    CommandeForm,
    CommandeUpdateForm,
    GroupForm,
    LigneCommandeForm,
    LivreurForm,
    PaiementForm,
    ProduitForm,
    TailleProduitForm,
    UserCreationForm,
)
from .models import AdresseLivraison, Categorie, Client, Commande, Facture, LigneCommande, Livraison, Livreur, Paiement, Produit, TailleProduit


# Create your views here.


def order_list(request):
    commandes = Commande.objects.select_related('client', 'adresse_livraison').order_by('-date_commande')
    total = commandes.count()
    en_attente = commandes.filter(statut=Commande.Statut.EN_ATTENTE).count()
    en_preparation = commandes.filter(statut=Commande.Statut.EN_PREPARATION).count()
    livrees = commandes.filter(statut=Commande.Statut.LIVREE).count()
    return render(request, 'order_list.html', {
        'commandes': commandes,
        'total': total,
        'en_attente': en_attente,
        'en_preparation': en_preparation,
        'livrees': livrees,
        'statuts': Commande.Statut.choices,
        'facture_created': request.GET.get('facture_created'),
    })


def _produits_prices():
    return {str(p.pk): float(p.prix) for p in Produit.objects.all()}


def _commande_lignes_formset(data=None, instance=None):
    LigneFormSet = inlineformset_factory(
        Commande,
        LigneCommande,
        form=LigneCommandeForm,
        extra=1,
        can_delete=True,
    )
    return LigneFormSet(data or None, instance=instance)


@login_required(login_url='login')
def commande_create(request):
    form = CommandeForm(request.POST or None)
    formset = _commande_lignes_formset(request.POST or None)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        if not any(
            f.cleaned_data.get('produit')
            for f in formset.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE')
        ):
            form.add_error(None, 'Ajoutez au moins un produit à la commande.')
        else:
            commande = form.save(commit=False)
            commande.statut = Commande.Statut.EN_ATTENTE
            commande.save()
            commande.numero = f"CMD-{commande.pk:06d}"
            commande.save(update_fields=['numero'])
            formset.instance = commande
            formset.save()
            commande.total = (
                sum(l.sous_total for l in commande.lignes.all()) + commande.frais_livraison
            )
            commande.save(update_fields=['total'])
            return redirect('order_list')
    return render(request, 'forms/commande_form.html', {
        'form': form,
        'ligne_formset': formset,
        'title': 'Ajouter une commande',
        'produits_prices': _produits_prices(),
    })


@login_required(login_url='login')
def commande_update(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    form = CommandeUpdateForm(request.POST or None, instance=commande)
    formset = _commande_lignes_formset(request.POST or None, instance=commande)
    if request.method == 'POST' and form.is_valid() and formset.is_valid():
        if not any(
            f.cleaned_data.get('produit')
            for f in formset.forms
            if f.cleaned_data and not f.cleaned_data.get('DELETE')
        ):
            form.add_error(None, 'Ajoutez au moins un produit à la commande.')
        else:
            commande = form.save()
            formset.save()
            commande.total = (
                sum(l.sous_total for l in commande.lignes.all()) + commande.frais_livraison
            )
            commande.save(update_fields=['total'])
            return redirect('order_list')
    return render(request, 'forms/commande_form.html', {
        'form': form,
        'ligne_formset': formset,
        'title': f'Modifier la commande {commande.numero}',
        'produits_prices': _produits_prices(),
    })


@login_required(login_url='login')
def commande_delete(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    if request.method == 'POST':
        commande.delete()
    return redirect('order_list')


@login_required(login_url='login')
def commande_statut(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    facture_creee = False
    if request.method == 'POST':
        statut = request.POST.get('statut')
        if statut in Commande.Statut.values:
            if commande.statut in (Commande.Statut.PRETE, Commande.Statut.EN_LIVRAISON, Commande.Statut.LIVREE) \
                    and statut != Commande.Statut.ANNULEE:
                pass
            else:
                commande.statut = statut
                commande.save(update_fields=['statut'])
                if statut == Commande.Statut.PRETE:
                    if not hasattr(commande, 'facture'):
                        Facture.objects.create(
                            commande=commande,
                            numero=f"FAC-{commande.pk:06d}",
                            montant=commande.total,
                        )
                        facture_creee = True
                    if commande.a_livree and not hasattr(commande, 'livraison') and commande.adresse_livraison:
                        Livraison.objects.create(
                            commande=commande,
                            livreur=commande.livreur,
                            adresse=commande.adresse_livraison.adresse,
                            cout_livraison=commande.frais_livraison,
                        )
    if facture_creee:
        return redirect(reverse('order_list') + f'?facture_created={commande.numero}')
    return redirect('order_list')


@login_required(login_url='login')
def categorie_create(request):
    form = CategorieForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('categories_list')
    return render(request, 'forms/categorie_form.html', {'form': form, 'title': 'Ajouter une catégorie'})


@login_required(login_url='login')
def categorie_update(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    form = CategorieForm(request.POST or None, instance=categorie)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('categories_list')
    return render(request, 'forms/categorie_form.html', {'form': form, 'title': 'Modifier une catégorie'})


@login_required(login_url='login')
def categorie_delete(request, pk):
    categorie = get_object_or_404(Categorie, pk=pk)
    if request.method == 'POST':
        try:
            categorie.delete()
        except ProtectedError:
            return redirect(reverse('categories_list') + '?error=protected')
    return redirect('categories_list')


@login_required(login_url='login')
def taille_create(request):
    form = TailleProduitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tailles_list')
    return render(request, 'forms/taille_form.html', {'form': form, 'title': 'Ajouter une taille'})


@login_required(login_url='login')
def taille_update(request, pk):
    taille = get_object_or_404(TailleProduit, pk=pk)
    form = TailleProduitForm(request.POST or None, instance=taille)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tailles_list')
    return render(request, 'forms/taille_form.html', {'form': form, 'title': 'Modifier une taille'})


@login_required(login_url='login')
def taille_delete(request, pk):
    taille = get_object_or_404(TailleProduit, pk=pk)
    if request.method == 'POST':
        try:
            taille.delete()
        except ProtectedError:
            return redirect(reverse('tailles_list') + '?error=protected')
    return redirect('tailles_list')


@login_required(login_url='login')
def produit_create(request):
    form = ProduitForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('products_list')
    return render(request, 'forms/produit_form.html', {'form': form, 'title': 'Ajouter un produit'})


@login_required(login_url='login')
def produit_update(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    form = ProduitForm(request.POST or None, request.FILES or None, instance=produit)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('products_list')
    return render(request, 'forms/produit_form.html', {'form': form, 'title': 'Modifier un produit'})


@login_required(login_url='login')
def produit_delete(request, pk):
    produit = get_object_or_404(Produit, pk=pk)
    if request.method == 'POST':
        produit.delete()
    return redirect('products_list')


@login_required(login_url='login')
def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('clients_list')
    return render(request, 'forms/client_form.html', {'form': form, 'title': 'Ajouter un client'})


@login_required(login_url='login')
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)
    form = ClientForm(request.POST or None, instance=client)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('clients_list')
    return render(request, 'forms/client_form.html', {'form': form, 'title': 'Modifier un client'})


@login_required(login_url='login')
def client_delete(request, pk):
    client = get_object_or_404(Client, pk=pk)
    if request.method == 'POST':
        client.delete()
    return redirect('clients_list')


@login_required(login_url='login')
def adresse_create(request):
    form = AdresseLivraisonForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('adresses_livraison_list')
    return render(request, 'forms/adresse_form.html', {'form': form, 'title': 'Ajouter une adresse'})


@login_required(login_url='login')
def livreur_create(request):
    form = LivreurForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('livreurs_list')
    return render(request, 'forms/livreur_form.html', {'form': form, 'title': 'Ajouter un livreur'})


def clients_list(request):
    clients = Client.objects.annotate(nb_commandes=Count('commandes')).all()
    total = clients.count()
    avec_commandes = clients.filter(nb_commandes__gt=0).count()
    sans_commandes = clients.filter(nb_commandes=0).count()
    total_commandes = Commande.objects.count()
    return render(request, 'clients_list.html', {
        'clients': clients,
        'total': total,
        'avec_commandes': avec_commandes,
        'sans_commandes': sans_commandes,
        'total_commandes': total_commandes,
    })


def products_list(request):
    produits = Produit.objects.select_related('categorie', 'taille').all()
    total = produits.count()
    disponibles = produits.filter(disponible=True).count()
    indisponibles = produits.filter(disponible=False).count()
    categories = Categorie.objects.count()
    return render(request, 'products_list.html', {
        'produits': produits,
        'total': total,
        'disponibles': disponibles,
        'indisponibles': indisponibles,
        'categories': categories,
    })


def factures_list(request):
    factures = Facture.objects.select_related('commande__client').order_by('-date_facture')
    total = factures.count()
    payees = factures.filter(statut=Facture.Statut.PAYEE).count()
    non_payees = factures.filter(statut=Facture.Statut.NON_PAYEE).count()
    montant_total = factures.aggregate(montant_total=Sum('montant'))['montant_total'] or 0
    return render(request, 'factures_list.html', {
        'factures': factures,
        'total': total,
        'payees': payees,
        'non_payees': non_payees,
        'montant_total': montant_total,
        'paye': request.GET.get('paye'),
        'error': request.GET.get('error'),
    })


@login_required(login_url='login')
def facture_delete(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        facture.delete()
    return redirect('factures_list')


@login_required(login_url='login')
def facture_paiement(request, pk):
    facture = get_object_or_404(Facture, pk=pk)
    if request.method == 'POST':
        try:
            montant = Decimal(request.POST.get('montant', '') or 0)
        except InvalidOperation:
            montant = Decimal('0')
        reste = facture.montant_restant
        if montant <= 0 or montant > reste:
            return redirect(reverse('factures_list') + '?error=montant')
        mode = request.POST.get('mode_paiement')
        if mode not in Paiement.ModePaiement.values:
            mode = Paiement.ModePaiement.ESPECES
        Paiement.objects.create(
            facture=facture,
            montant=montant,
            mode_paiement=mode,
            statut=Paiement.Statut.VALIDE,
        )
        if facture.montant_paye >= facture.montant:
            facture.statut = Facture.Statut.PAYEE
        else:
            facture.statut = Facture.Statut.PARTIELLE
        facture.save(update_fields=['statut'])
        return redirect(reverse('factures_list') + '?paye=1')
    return redirect('factures_list')


def paiements_list(request):
    paiements = Paiement.objects.select_related('facture__commande__client').order_by('-date_paiement')
    total = paiements.count()
    valides = paiements.filter(statut=Paiement.Statut.VALIDE).count()
    en_attente = paiements.filter(statut=Paiement.Statut.EN_ATTENTE).count()
    encaisse = paiements.filter(statut=Paiement.Statut.VALIDE).aggregate(encaisse=Sum('montant'))['encaisse'] or 0
    return render(request, 'paiements_list.html', {
        'paiements': paiements,
        'total': total,
        'valides': valides,
        'en_attente': en_attente,
        'encaisse': encaisse,
    })


@login_required(login_url='login')
def paiement_delete(request, pk):
    paiement = get_object_or_404(Paiement, pk=pk)
    if request.method == 'POST':
        paiement.delete()
    return redirect('paiements_list')


def livraisons_list(request):
    livraisons = Livraison.objects.select_related('commande__client', 'livreur').order_by('-pk')
    total = livraisons.count()
    en_attente = livraisons.filter(statut=Livraison.Statut.EN_ATTENTE).count()
    en_route = livraisons.filter(statut=Livraison.Statut.EN_ROUTE).count()
    livrees = livraisons.filter(statut=Livraison.Statut.LIVREE).count()
    return render(request, 'livraisons_list.html', {
        'livraisons': livraisons,
        'total': total,
        'en_attente': en_attente,
        'en_route': en_route,
        'livrees': livrees,
        'statuts': Livraison.Statut.choices,
        'statut_updated': request.GET.get('statut_updated'),
    })


@login_required(login_url='login')
def livraison_statut(request, pk):
    livraison = get_object_or_404(Livraison, pk=pk)
    if request.method == 'POST':
        statut = request.POST.get('statut')
        if statut in Livraison.Statut.values:
            livraison.statut = statut
            if statut == Livraison.Statut.LIVREE and not livraison.date_livraison:
                livraison.date_livraison = timezone.now()
            livraison.save()
            return redirect(reverse('livraisons_list') + f'?statut_updated={statut}')
    return redirect('livraisons_list')


def livraison_detail(request, pk):
    livraison = get_object_or_404(
        Livraison.objects.select_related('commande__client', 'commande__adresse_livraison', 'livreur'),
        pk=pk,
    )
    coords = None
    adresse_obj = livraison.commande.adresse_livraison
    if adresse_obj is not None and adresse_obj.latitude is not None and adresse_obj.longitude is not None:
        coords = {'lat': float(adresse_obj.latitude), 'lon': float(adresse_obj.longitude)}
    return render(request, 'livraison_detail.html', {
        'livraison': livraison,
        'coords': coords,
    })


def categories_list(request):
    categories = Categorie.objects.annotate(nb_produits=Count('produits')).all()
    total = categories.count()
    avec_produits = categories.filter(nb_produits__gt=0).count()
    sans_produits = categories.filter(nb_produits=0).count()
    total_produits = Produit.objects.count()
    return render(request, 'categories_list.html', {
        'categories': categories,
        'total': total,
        'avec_produits': avec_produits,
        'sans_produits': sans_produits,
        'total_produits': total_produits,
        'error': request.GET.get('error'),
    })


def tailles_list(request):
    tailles = TailleProduit.objects.annotate(nb_produits=Count('produits')).all()
    total = tailles.count()
    avec_produits = tailles.filter(nb_produits__gt=0).count()
    sans_produits = tailles.filter(nb_produits=0).count()
    total_produits = Produit.objects.count()
    return render(request, 'tailles_list.html', {
        'tailles': tailles,
        'total': total,
        'avec_produits': avec_produits,
        'sans_produits': sans_produits,
        'total_produits': total_produits,
        'error': request.GET.get('error'),
    })


def livreurs_list(request):
    livreurs = Livreur.objects.annotate(nb_livraisons=Count('livraisons')).all()
    total = livreurs.count()
    disponibles = livreurs.filter(etat=Livreur.Etat.DISPONIBLE).count()
    en_livraison = livreurs.filter(etat=Livreur.Etat.EN_LIVRAISON).count()
    inactifs = livreurs.filter(etat=Livreur.Etat.INACTIF).count()
    return render(request, 'livreurs_list.html', {
        'livreurs': livreurs,
        'total': total,
        'disponibles': disponibles,
        'en_livraison': en_livraison,
        'inactifs': inactifs,
        'error': request.GET.get('error'),
    })


@login_required(login_url='login')
def livreur_update(request, pk):
    livreur = get_object_or_404(Livreur, pk=pk)
    form = LivreurForm(request.POST or None, request.FILES or None, instance=livreur)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('livreurs_list')
    return render(request, 'forms/livreur_form.html', {'form': form, 'title': f'Modifier le livreur {livreur.nom}'})


@login_required(login_url='login')
def livreur_delete(request, pk):
    livreur = get_object_or_404(Livreur, pk=pk)
    if request.method == 'POST':
        try:
            livreur.delete()
        except ProtectedError:
            return redirect(reverse('livreurs_list') + '?error=protected')
    return redirect('livreurs_list')


@login_required(login_url='login')
def paiement_create(request):
    form = PaiementForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('paiements_list')
    return render(request, 'forms/paiement_form.html', {'form': form, 'title': 'Ajouter un paiement'})


@login_required(login_url='login')
def user_create(request):
    form = UserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('users_settings')
    return render(request, 'forms/user_form.html', {'form': form, 'title': 'Ajouter un utilisateur'})


@login_required(login_url='login')
def group_create(request):
    form = GroupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('groups_settings')
    return render(request, 'forms/group_form.html', {'form': form, 'title': 'Ajouter un groupe'})


def adresses_livraison_list(request):
    adresses = AdresseLivraison.objects.select_related('client').all()
    clients = Client.objects.all()

    selected_client_id = request.GET.get('client')
    query = request.GET.get('q', '').strip()

    if selected_client_id:
        adresses = adresses.filter(client_id=selected_client_id)

    if query:
        adresses = adresses.filter(
            Q(nom__icontains=query) |
            Q(adresse__icontains=query) |
            Q(client__nom__icontains=query) |
            Q(client__prenom__icontains=query)
        )

    return render(request, 'adresses_livraison_list.html', {
        'adresses': adresses,
        'clients': clients,
        'selected_client_id': selected_client_id,
        'query': query,
        'adresses_coords': [
            {
                'lat': float(a.latitude),
                'lon': float(a.longitude),
                'nom': a.nom,
                'client': str(a.client),
                'adresse': a.adresse,
            }
            for a in adresses
            if a.latitude is not None and a.longitude is not None
        ],
    })