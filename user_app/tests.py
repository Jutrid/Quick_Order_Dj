from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from order_app.models import Categorie, Client, Commande, Facture, Livraison, Produit


class AuthViewsTests(TestCase):
    def test_login_page_is_available(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Connexion')

    def test_register_creates_user(self):
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'StrongPass123!',
            'password2': 'StrongPass123!',
            'first_name': 'New',
            'last_name': 'User',
        })

        self.assertEqual(response.status_code, 302)
        self.assertTrue(get_user_model().objects.filter(username='newuser').exists())

    def test_dashboard_requires_authentication(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/?next=/dashboard/', response.url)

    def test_login_with_wrong_credentials_shows_error(self):
        get_user_model().objects.create_user(username='validuser', password='GoodPass123!')
        response = self.client.post(reverse('login'), {
            'username': 'validuser',
            'password': 'WrongPass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nom d’utilisateur ou mot de passe incorrect.')

    def test_login_with_good_credentials_redirects(self):
        get_user_model().objects.create_user(username='validuser', password='GoodPass123!')
        response = self.client.post(reverse('login'), {
            'username': 'validuser',
            'password': 'GoodPass123!',
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('dashboard'))


class DashboardTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
        self.categorie = Categorie.objects.create(nom="Pizzas")
        self.produit = Produit.objects.create(
            categorie=self.categorie,
            nom="Pizza Margherita",
            prix=5000,
            soumis_stock=True,
            stock=10,
        )
        self.client_obj = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        self.commande = Commande.objects.create(
            numero="CMD-000001",
            client=self.client_obj,
            total=10000,
        )
        self.facture = Facture.objects.create(
            commande=self.commande,
            numero="FAC-000001",
            montant=10000,
        )

    def test_dashboard_affiche_des_donnees_reelles(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1</h4>')
        self.assertContains(response, 'CMD-000001')
        self.assertContains(response, 'FAC-000001')
        self.assertContains(response, 'Diop Moussa')
        self.assertNotContains(response, '248')

    def test_dashboard_affiche_les_statuts_des_factures(self):
        self.facture.statut = Facture.Statut.NON_PAYEE
        self.facture.save(update_fields=['statut'])
        response = self.client.get(reverse('dashboard'))
        self.assertContains(response, 'Non payée')
        self.assertEqual(response.context['nb_commandes'], 1)
        self.assertEqual(response.context['nb_factures'], 1)
        self.assertEqual(response.context['factures_impayees'], 1)
        self.assertEqual(response.context['stock_total'], 10)
        self.assertEqual(len(response.context['activites']), 2)

    def test_dashboard_est_vide_sans_donnees(self):
        Commande.objects.all().delete()
        Facture.objects.all().delete()
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['nb_commandes'], 0)
        self.assertEqual(response.context['activites'], [])
        self.assertContains(response, 'Aucune activité pour le moment.')
