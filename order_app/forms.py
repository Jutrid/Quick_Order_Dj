from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from .models import AdresseLivraison, Categorie, Client, Commande, Facture, LigneCommande, Livreur, Paiement, Produit, TailleProduit


class CategorieForm(forms.ModelForm):
    class Meta:
        model = Categorie
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Pizzas'})
        }


class TailleProduitForm(forms.ModelForm):
    class Meta:
        model = TailleProduit
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex : Grande'})
        }


class ProduitForm(forms.ModelForm):
    class Meta:
        model = Produit
        fields = [
            'categorie',
            'taille',
            'reference',
            'nom',
            'description',
            'prix',
            'image',
            'disponible',
            'soumis_stock',
            'stock',
            'temps_preparation_defini',
            'temps_preparation',
        ]
        widgets = {
            'categorie': forms.Select(attrs={'class': 'form-select'}),
            'taille': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prix': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'disponible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'soumis_stock': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'temps_preparation_defini': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'temps_preparation': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }

    stock = forms.IntegerField(
        required=False,
        min_value=0,
        initial=0,
        label='Quantité en stock',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    )

    temps_preparation = forms.IntegerField(
        required=False,
        min_value=0,
        label='Temps de préparation (minutes)',
        widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
    )

    def clean(self):
        cleaned = super().clean()
        soumis_stock = cleaned.get('soumis_stock')
        stock = cleaned.get('stock')
        if soumis_stock and stock is None:
            self.add_error('stock', 'Le produit étant soumis au stock, la quantité est requise.')
        elif not soumis_stock:
            cleaned['stock'] = 0

        temps_defini = cleaned.get('temps_preparation_defini')
        temps_preparation = cleaned.get('temps_preparation')
        if temps_defini and not temps_preparation:
            self.add_error('temps_preparation', 'Veuillez indiquer un temps de préparation.')
        elif not temps_defini:
            cleaned['temps_preparation'] = None

        return cleaned


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['nom', 'prenom', 'telephone', 'email']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }


class AdresseLivraisonForm(forms.ModelForm):
    class Meta:
        model = AdresseLivraison
        fields = ['client', 'nom', 'adresse', 'latitude', 'longitude']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000000000000001'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.00000000000000001'}),
        }


class AdresseLivraisonSelect(forms.Select):
    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        queryset = getattr(self.choices, 'queryset', None)
        if queryset is not None and value:
            raw = getattr(value, 'value', value)
            try:
                option['attrs']['data-client'] = queryset.get(pk=raw).client_id
            except (ValueError, TypeError, queryset.model.DoesNotExist):
                pass
        return option


class LigneCommandeForm(forms.ModelForm):
    class Meta:
        model = LigneCommande
        fields = ['produit', 'quantite']
        widgets = {
            'produit': forms.Select(attrs={'class': 'form-select select2-produit'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control ligne-quantite', 'min': '1'}),
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        if instance.prix_unitaire is None and instance.produit_id:
            instance.prix_unitaire = instance.produit.prix
        if commit:
            instance.save()
        return instance


class CommandeForm(forms.ModelForm):
    class Meta:
        model = Commande
        fields = ['client', 'adresse_livraison', 'frais_livraison', 'a_livree', 'livreur', 'commentaire']
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select select2-client'}),
            'adresse_livraison': AdresseLivraisonSelect(attrs={'class': 'form-select select2-adresse'}),
            'frais_livraison': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0'}),
            'a_livree': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'livreur': forms.Select(attrs={'class': 'form-select'}),
            'commentaire': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get('a_livree'):
            cleaned['adresse_livraison'] = None
            cleaned['frais_livraison'] = 0
            cleaned['livreur'] = None
        elif not cleaned.get('adresse_livraison'):
            self.add_error('adresse_livraison', "La livraison étant activée, l'adresse de livraison est requise.")
        return cleaned


class CommandeUpdateForm(CommandeForm):
    class Meta(CommandeForm.Meta):
        fields = CommandeForm.Meta.fields + ['statut']
        widgets = dict(CommandeForm.Meta.widgets)
        widgets['statut'] = forms.Select(attrs={'class': 'form-select'})


class LivreurForm(forms.ModelForm):
    class Meta:
        model = Livreur
        fields = ['nom', 'telephone', 'photo', 'plaque_moto', 'etat']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'plaque_moto': forms.TextInput(attrs={'class': 'form-control'}),
            'etat': forms.Select(attrs={'class': 'form-select'}),
        }


class PaiementForm(forms.ModelForm):
    class Meta:
        model = Paiement
        fields = ['facture', 'montant', 'mode_paiement', 'reference', 'statut']
        widgets = {
            'facture': forms.Select(attrs={'class': 'form-select'}),
            'montant': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'mode_paiement': forms.Select(attrs={'class': 'form-select'}),
            'reference': forms.TextInput(attrs={'class': 'form-control'}),
            'statut': forms.Select(attrs={'class': 'form-select'}),
        }


class UserCreationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), label='Confirmer le mot de passe')

    class Meta:
        model = get_user_model()
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        password_confirm = cleaned.get('password_confirm')
        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', 'Les mots de passe ne correspondent pas.')
        return cleaned

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
        }
