from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from .forms import (
    AdresseLivraisonForm,
    CategorieForm,
    ClientForm,
    CommandeForm,
    GroupForm,
    LivreurForm,
    PaiementForm,
    ProduitForm,
    TailleProduitForm,
    UserCreationForm,
)
from .models import AdresseLivraison, Categorie, Client, Commande, Livreur, Produit, TailleProduit


# Create your views here.

def order_list(request):
    return render(request, 'order_list.html')


@login_required(login_url='login')
def categorie_create(request):
    form = CategorieForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('categories_list')
    return render(request, 'forms/categorie_form.html', {'form': form, 'title': 'Ajouter une catégorie'})


@login_required(login_url='login')
def taille_create(request):
    form = TailleProduitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('tailles_list')
    return render(request, 'forms/taille_form.html', {'form': form, 'title': 'Ajouter une taille'})


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
def client_create(request):
    form = ClientForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('clients_list')
    return render(request, 'forms/client_form.html', {'form': form, 'title': 'Ajouter un client'})


@login_required(login_url='login')
def adresse_create(request):
    form = AdresseLivraisonForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('adresses_livraison_list')
    return render(request, 'forms/adresse_form.html', {'form': form, 'title': 'Ajouter une adresse'})


@login_required(login_url='login')
def commande_create(request):
    form = CommandeForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('order_list')
    return render(request, 'forms/commande_form.html', {'form': form, 'title': 'Ajouter une commande'})


@login_required(login_url='login')
def commande_update(request, pk):
    commande = get_object_or_404(Commande, pk=pk)
    form = CommandeForm(request.POST or None, instance=commande)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('order_list')
    return render(request, 'forms/commande_form.html', {'form': form, 'title': 'Modifier une commande'})


@login_required(login_url='login')
def livreur_create(request):
    form = LivreurForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('livreurs_list')
    return render(request, 'forms/livreur_form.html', {'form': form, 'title': 'Ajouter un livreur'})


def clients_list(request):
    return render(request, 'clients_list.html')


def products_list(request):
    return render(request, 'products_list.html')


def factures_list(request):
    return render(request, 'factures_list.html')


def paiements_list(request):
    return render(request, 'paiements_list.html')


def livraisons_list(request):
    return render(request, 'livraisons_list.html')


def categories_list(request):
    return render(request, 'categories_list.html')


def tailles_list(request):
    return render(request, 'tailles_list.html')


def livreurs_list(request):
    return render(request, 'livreurs_list.html')


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
    })