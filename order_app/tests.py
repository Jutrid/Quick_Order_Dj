from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AdresseLivraison, Categorie, Client, Commande, Facture, Livraison, Livreur, Paiement


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


class FacturePaiementTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
        client = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        adresse = AdresseLivraison.objects.create(client=client, nom="Maison", adresse="Dakar, Sénégal")
        commande = Commande.objects.create(
            numero="CMD-000001",
            client=client,
            adresse_livraison=adresse,
            total=10000,
        )
        self.facture = Facture.objects.create(
            commande=commande,
            numero="FAC-000001",
            montant=10000,
        )

    def test_paiement_total_marque_facture_payee(self):
        response = self.client.post(reverse('facture_paiement', args=[self.facture.pk]), {'montant': '10000'})
        self.assertRedirects(response, reverse('factures_list') + '?paye=1')
        self.facture.refresh_from_db()
        self.assertEqual(self.facture.statut, Facture.Statut.PAYEE)
        self.assertEqual(self.facture.montant_paye, 10000)

    def test_paiement_partiel_marque_facture_partielle(self):
        response = self.client.post(reverse('facture_paiement', args=[self.facture.pk]), {'montant': '4000'})
        self.assertRedirects(response, reverse('factures_list') + '?paye=1')
        self.facture.refresh_from_db()
        self.assertEqual(self.facture.statut, Facture.Statut.PARTIELLE)
        self.assertEqual(self.facture.montant_restant, 6000)

    def test_paiement_depassant_reste_est_refuse(self):
        response = self.client.post(reverse('facture_paiement', args=[self.facture.pk]), {'montant': '15000'})
        self.assertRedirects(response, reverse('factures_list') + '?error=montant')
        self.facture.refresh_from_db()
        self.assertEqual(self.facture.statut, Facture.Statut.NON_PAYEE)
        self.assertEqual(Paiement.objects.count(), 0)

    def test_paiement_apres_paiement_complet_est_refuse(self):
        self.client.post(reverse('facture_paiement', args=[self.facture.pk]), {'montant': '10000'})
        response = self.client.post(reverse('facture_paiement', args=[self.facture.pk]), {'montant': '100'})
        self.assertRedirects(response, reverse('factures_list') + '?error=montant')
        self.assertEqual(Paiement.objects.filter(statut=Paiement.Statut.VALIDE).count(), 1)


class LivraisonTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
        self.client_objet = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        self.adresse = AdresseLivraison.objects.create(client=self.client_objet, nom="Maison", adresse="Dakar, Sénégal")
        self.commande = Commande.objects.create(
            numero="CMD-000002",
            client=self.client_objet,
            adresse_livraison=self.adresse,
            total=5000,
            a_livree=True,
        )

    def test_statut_prete_cree_la_livraison_si_a_livree(self):
        response = self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.assertRedirects(response, reverse('order_list') + '?facture_created=CMD-000002')
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.statut, Commande.Statut.PRETE)
        self.assertTrue(hasattr(self.commande, 'livraison'))
        self.assertEqual(self.commande.livraison.adresse, 'Dakar, Sénégal')
        self.assertEqual(self.commande.livraison.statut, Livraison.Statut.EN_ATTENTE)

    def test_statut_prete_ne_cree_pas_la_livraison_si_pas_a_livree(self):
        self.commande.a_livree = False
        self.commande.save(update_fields=['a_livree'])
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.assertFalse(hasattr(self.commande, 'livraison'))

    def test_passer_prete_deux_fois_ne_cree_qu_une_livraison(self):
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.assertEqual(Livraison.objects.filter(commande=self.commande).count(), 1)

    def test_changement_statut_livraison(self):
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.commande.refresh_from_db()
        livraison = self.commande.livraison
        response = self.client.post(reverse('livraison_statut', args=[livraison.pk]), {'statut': 'LIVREE'})
        self.assertRedirects(response, reverse('livraisons_list') + '?statut_updated=LIVREE')
        livraison.refresh_from_db()
        self.assertEqual(livraison.statut, Livraison.Statut.LIVREE)
        self.assertIsNotNone(livraison.date_livraison)

    def test_liste_livraisons_est_fonctionnelle(self):
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        response = self.client.get(reverse('livraisons_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'LVR-')
        self.assertContains(response, 'CMD-000002')

    def test_detail_livraison_affiche_la_carte(self):
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.commande.refresh_from_db()
        livraison = self.commande.livraison
        response = self.client.get(reverse('livraison_detail', args=[livraison.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Livraison LVR-')
        self.assertContains(response, 'Dakar, Sénégal')

    def test_livreur_de_la_commande_est_reporte_sur_la_livraison(self):
        livreur = Livreur.objects.create(nom="Ibrahima", telephone="771234567")
        self.commande.livreur = livreur
        self.commande.save(update_fields=['livreur'])
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.commande.refresh_from_db()
        self.assertEqual(self.commande.livraison.livreur, livreur)


class LivreurTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
        self.livreur = Livreur.objects.create(nom="Ibrahima", telephone="771234567", plaque_moto="DK-1245-A")

    def test_liste_livreurs_est_fonctionnelle(self):
        response = self.client.get(reverse('livreurs_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ibrahima')
        self.assertContains(response, 'DK-1245-A')

    def test_formulaire_livreur_update(self):
        response = self.client.post(reverse('livreur_update', args=[self.livreur.pk]), {
            'nom': 'Ibrahima Sarr',
            'telephone': '771234567',
            'plaque_moto': 'DK-9999-Z',
            'etat': 'DISPONIBLE',
        })
        self.assertRedirects(response, reverse('livreurs_list'))
        self.livreur.refresh_from_db()
        self.assertEqual(self.livreur.nom, 'Ibrahima Sarr')

    def test_suppression_livreur(self):
        response = self.client.post(reverse('livreur_delete', args=[self.livreur.pk]))
        self.assertRedirects(response, reverse('livreurs_list'))
        self.assertFalse(Livreur.objects.filter(pk=self.livreur.pk).exists())
