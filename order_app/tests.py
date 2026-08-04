from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AdresseLivraison, Categorie, Client


class FormViewsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')

    def test_category_create_page_is_accessible(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('categorie_create'))
        self.assertEqual(response.status_code, 200)

    def test_category_create_saves_data(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('categorie_create'), {'nom': 'Desserts'})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Categorie.objects.filter(nom='Desserts').exists())

    def test_client_create_page_is_accessible(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('client_create'))
        self.assertEqual(response.status_code, 200)


class AdressesLivraisonViewsTests(TestCase):
    def setUp(self):
        self.client1 = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        self.client2 = Client.objects.create(nom="Ba", prenom="Awa", telephone="781234567")

        AdresseLivraison.objects.create(client=self.client1, nom="Maison", adresse="Dakar, Sénégal")
        AdresseLivraison.objects.create(client=self.client2, nom="Bureau", adresse="Thiès, Sénégal")

    def test_adresses_page_is_available(self):
        response = self.client.get(reverse('adresses_livraison_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Adresses de livraison')

    def test_adresses_can_be_filtered_by_client(self):
        response = self.client.get(reverse('adresses_livraison_list'), {'client': self.client1.id})
        self.assertContains(response, 'Maison')
        self.assertNotContains(response, 'Bureau')

    def test_adresses_can_be_searched_by_text(self):
        response = self.client.get(reverse('adresses_livraison_list'), {'q': 'thiès'})
        self.assertContains(response, 'Bureau')
        self.assertNotContains(response, 'Maison')
