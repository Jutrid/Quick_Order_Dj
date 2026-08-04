from django.contrib.auth import authenticate, get_user_model, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm as DjangoUserCreationForm
from django.contrib.auth.models import Group
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from order_app.forms import GroupForm, UserCreationForm


@require_http_methods(["GET", "POST"])
def logIn(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            next_url = request.POST.get('next') or request.GET.get('next') or 'dashboard'
            return redirect(next_url)

    return render(request, 'auth/login.html', {
        'next': request.GET.get('next', ''),
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
    return render(request, 'home.html')


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

