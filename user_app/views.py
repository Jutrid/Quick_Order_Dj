from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.models import Group
from django.db.models import Count, Sum
from django.db.models.functions import ExtractMonth, ExtractYear
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from order_app.forms import GroupForm, UserCreationForm
from order_app.models import Client, Commande, Facture, Livraison, MouvementStock, Paiement, Produit

MOIS_FR = ['Janv.', 'Févr.', 'Mars', 'Avr.', 'Mai', 'Juin', 'Juil.', 'Août', 'Sept.', 'Oct.', 'Nov.', 'Déc.']
SEUIL_REAPPROVISIONNEMENT = 5


def _badge_statut(statut):
    classes = {
        'LIVREE': 'badge-success',
        'EN_LIVRAISON': 'badge-info',
        'PRETE': 'badge-primary',
        'EN_PREPARATION': 'badge-info',
        'ANNULEE': 'badge-danger',
        'EN_ATTENTE': 'badge-warning',
        'EN_ROUTE': 'badge-warning',
        'PAYEE': 'badge-success',
        'PARTIELLE': 'badge-warning',
        'NON_PAYEE': 'badge-danger',
    }
    return classes.get(statut, 'badge-secondary')


def _derniers_mois(n=6):
    aujourd = timezone.localdate()
    annee, mois = aujourd.year, aujourd.month
    mois_list = []
    for _ in range(n):
        mois_list.append((annee, mois))
        if mois == 1:
            annee, mois = annee - 1, 12
        else:
            mois -= 1
    mois_list.reverse()
    return mois_list


@require_http_methods(["GET", "POST"])
def logIn(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    error = False
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)
        error = True

    return render(request, 'auth/login.html', {
        'next': request.GET.get('next', ''),
        'error': error,
    })


@require_http_methods(["GET", "POST"])
def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    form = DjangoUserCreationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        return redirect('dashboard')

    return render(request, 'auth/register.html', {'form': form})


@login_required(login_url='login')
def dashboard(request):
    nb_commandes = Commande.objects.count()
    nb_livraisons = Livraison.objects.count()
    nb_factures = Facture.objects.count()
    stock_total = Produit.objects.filter(soumis_stock=True).aggregate(
        total_stock=Sum('stock')
    )['total_stock'] or 0

    activites = []
    for c in Commande.objects.select_related('client').order_by('-date_commande')[:4]:
        activites.append({
            'ref': c.numero,
            'type': 'Commande',
            'statut': c.get_statut_display(),
            'badge': _badge_statut(c.statut),
            'client': str(c.client),
            'date': c.date_commande,
        })
    for l in Livraison.objects.select_related('commande__client').order_by('-pk')[:4]:
        activites.append({
            'ref': f'LVR-{l.pk:06d}',
            'type': 'Livraison',
            'statut': l.get_statut_display(),
            'badge': _badge_statut(l.statut),
            'client': str(l.commande.client),
            'date': l.commande.date_commande,
        })
    for f in Facture.objects.select_related('commande__client').order_by('-date_facture')[:4]:
        activites.append({
            'ref': f.numero,
            'type': 'Facture',
            'statut': f.get_statut_display(),
            'badge': _badge_statut(f.statut),
            'client': str(f.commande.client),
            'date': f.date_facture,
        })
    activites.sort(key=lambda a: a['date'], reverse=True)
    activites = activites[:8]

    livraisons_en_attente = Livraison.objects.filter(statut=Livraison.Statut.EN_ATTENTE).count()
    produits_a_reapprovisionner = Produit.objects.filter(
        soumis_stock=True, stock__lte=SEUIL_REAPPROVISIONNEMENT
    ).count()
    factures_impayees = Facture.objects.exclude(statut=Facture.Statut.PAYEE).count()

    mois_list = _derniers_mois()
    commande_rows = (
        Commande.objects
        .annotate(annee=ExtractYear('date_commande'), mois=ExtractMonth('date_commande'))
        .values('annee', 'mois')
        .annotate(total=Count('id'))
    )
    livraison_rows = (
        Livraison.objects.filter(date_livraison__isnull=False)
        .annotate(annee=ExtractYear('date_livraison'), mois=ExtractMonth('date_livraison'))
        .values('annee', 'mois')
        .annotate(total=Count('id'))
    )
    compte_commandes = {(r['annee'], r['mois']): r['total'] for r in commande_rows}
    compte_livraisons = {(r['annee'], r['mois']): r['total'] for r in livraison_rows}

    return render(request, 'home.html', {
        'nb_commandes': nb_commandes,
        'nb_livraisons': nb_livraisons,
        'nb_factures': nb_factures,
        'stock_total': stock_total,
        'activites': activites,
        'livraisons_en_attente': livraisons_en_attente,
        'produits_a_reapprovisionner': produits_a_reapprovisionner,
        'factures_impayees': factures_impayees,
        'chart_labels': [MOIS_FR[m - 1] for _, m in mois_list],
        'chart_commandes': [compte_commandes.get(m, 0) for m in mois_list],
        'chart_livraisons': [compte_livraisons.get(m, 0) for m in mois_list],
    })


@login_required(login_url='login')
def users_settings(request):
    User = get_user_model()
    users = User.objects.all().order_by('username')
    return render(request, 'settings/users_list.html', {'users': users})


@login_required(login_url='login')
def groups_settings(request):
    groups = Group.objects.all().order_by('name')
    return render(request, 'settings/groups_list.html', {'groups': groups})


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


def log_out(request):
    logout(request)
    return redirect('login')

