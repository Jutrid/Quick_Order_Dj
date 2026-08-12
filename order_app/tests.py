from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import AdresseLivraison, Categorie, Client, Commande, Facture, LigneCommande, Livraison, Livreur, MouvementStock, Paiement, Produit


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
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
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

    def test_adresse_update_page_is_accessible(self):
        adresse = AdresseLivraison.objects.get(client=self.client1)
        response = self.client.get(reverse('adresse_update', args=[adresse.pk]))
        self.assertEqual(response.status_code, 200)

    def test_adresse_update_saves_data(self):
        adresse = AdresseLivraison.objects.get(client=self.client1)
        response = self.client.post(reverse('adresse_update', args=[adresse.pk]), {
            'client': self.client1.pk,
            'nom': 'Travail',
            'adresse': 'Goma, RDC',
        })
        self.assertRedirects(response, reverse('adresses_livraison_list'))
        adresse.refresh_from_db()
        self.assertEqual(adresse.nom, 'Travail')
        self.assertEqual(adresse.adresse, 'Goma, RDC')

    def test_adresse_delete_removes_adresse(self):
        adresse = AdresseLivraison.objects.get(client=self.client1)
        response = self.client.post(reverse('adresse_delete', args=[adresse.pk]))
        self.assertRedirects(response, reverse('adresses_livraison_list'))
        self.assertFalse(AdresseLivraison.objects.filter(pk=adresse.pk).exists())


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
        self.assertContains(response, 'id="map"')

    def test_detail_livraison_affiche_le_marqueur_quand_coordonnees(self):
        self.adresse.latitude = '14.716677000000000000000000'
        self.adresse.longitude = '-17.467685000000000000000000'
        self.adresse.save(update_fields=['latitude', 'longitude'])
        self.client.post(reverse('commande_statut', args=[self.commande.pk]), {'statut': 'PRETE'})
        self.commande.refresh_from_db()
        livraison = self.commande.livraison
        response = self.client.get(reverse('livraison_detail', args=[livraison.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '"lat": 14.716677')
        self.assertContains(response, '"lon": -17.467685')
        self.assertContains(response, 'L.marker([lat, lon])')
        self.assertNotContains(response, 'ne possède pas de coordonnées GPS')

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


class StockTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='admin', password='StrongPass123!')
        self.client.force_login(self.user)
        self.categorie = Categorie.objects.create(nom="Pizzas")
        self.produit_stock = Produit.objects.create(
            categorie=self.categorie,
            nom="Pizza Margherita",
            prix=5000,
            soumis_stock=True,
            stock=10,
        )
        self.produit_sans_stock = Produit.objects.create(
            categorie=self.categorie,
            nom="Sauce piquante",
            prix=500,
            soumis_stock=False,
            stock=0,
        )
        self.client_objet = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        self.adresse = AdresseLivraison.objects.create(client=self.client_objet, nom="Maison", adresse="Dakar, Sénégal")

    def _post_commande(self, quantite=2):
        return self.client.post(reverse('commande_create'), {
            'client': self.client_objet.pk,
            'adresse_livraison': self.adresse.pk,
            'frais_livraison': '0',
            'a_livree': 'on',
            'commentaire': '',
            'lignes-TOTAL_FORMS': '2',
            'lignes-INITIAL_FORMS': '0',
            'lignes-MIN_NUM_FORMS': '0',
            'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-produit': self.produit_stock.pk,
            'lignes-0-quantite': str(quantite),
            'lignes-1-produit': self.produit_sans_stock.pk,
            'lignes-1-quantite': '3',
        })

    def test_creation_commande_ne_diminue_pas_le_stock(self):
        response = self._post_commande(quantite=2)
        self.assertRedirects(response, reverse('order_list') + '?commande_created=1')
        self.produit_stock.refresh_from_db()
        self.produit_sans_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 10)
        self.assertEqual(self.produit_sans_stock.stock, 0)

    def test_statut_prete_diminue_stock_des_produits_soumis_stock(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        self.produit_stock.refresh_from_db()
        self.produit_sans_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 8)
        self.assertEqual(self.produit_sans_stock.stock, 0)

    def test_annulation_commande_rend_stock(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 8)
        response = self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'ANNULEE'})
        self.assertRedirects(response, reverse('order_list'))
        commande.refresh_from_db()
        self.assertEqual(commande.statut, Commande.Statut.ANNULEE)
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 10)

    def test_annulation_commande_en_attente_ne_modifie_pas_le_stock(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'ANNULEE'})
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 10)

    def test_suppression_commande_rend_stock(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 8)
        response = self.client.post(reverse('commande_delete', args=[commande.pk]))
        self.assertRedirects(response, reverse('order_list'))
        self.assertFalse(Commande.objects.filter(pk=commande.pk).exists())
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 10)

    def test_modification_commande_ajuste_stock(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        ligne = commande.lignes.get(produit=self.produit_stock)
        response = self.client.post(reverse('commande_update', args=[commande.pk]), {
            'client': self.client_objet.pk,
            'adresse_livraison': self.adresse.pk,
            'frais_livraison': '0',
            'a_livree': 'on',
            'statut': 'PRETE',
            'commentaire': '',
            'lignes-TOTAL_FORMS': '1',
            'lignes-INITIAL_FORMS': '1',
            'lignes-MIN_NUM_FORMS': '0',
            'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-id': ligne.pk,
            'lignes-0-produit': self.produit_stock.pk,
            'lignes-0-quantite': '5',
        })
        self.assertRedirects(response, reverse('order_list'))
        self.produit_stock.refresh_from_db()
        self.assertEqual(self.produit_stock.stock, 5)

    def test_creation_commande_ne_cree_pas_de_mouvement_stock(self):
        self._post_commande(quantite=2)
        self.assertFalse(MouvementStock.objects.filter(produit=self.produit_stock).exists())
        self.assertFalse(MouvementStock.objects.filter(produit=self.produit_sans_stock).exists())

    def test_statut_prete_cree_un_mouvement_sortie_automatique(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        mouvement = MouvementStock.objects.get(produit=self.produit_stock)
        self.assertEqual(mouvement.type_mouvement, MouvementStock.TypeMouvement.SORTIE)
        self.assertEqual(mouvement.quantite, 2)
        self.assertEqual(mouvement.description, f"Commande {commande.numero}")
        self.assertFalse(MouvementStock.objects.filter(produit=self.produit_sans_stock).exists())

    def test_annulation_commande_cree_un_mouvement_entree_automatique(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'ANNULEE'})
        mouvements = MouvementStock.objects.filter(produit=self.produit_stock).order_by('id')
        self.assertEqual(mouvements.count(), 2)
        self.assertEqual(mouvements[0].type_mouvement, MouvementStock.TypeMouvement.SORTIE)
        self.assertEqual(mouvements[1].type_mouvement, MouvementStock.TypeMouvement.ENTREE)
        self.assertEqual(mouvements[1].description, f"Retour commande {commande.numero}")

    def test_suppression_commande_cree_un_mouvement_entree_automatique(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        self.client.post(reverse('commande_delete', args=[commande.pk]))
        mouvements = MouvementStock.objects.filter(produit=self.produit_stock).order_by('id')
        self.assertEqual(mouvements.count(), 2)
        self.assertEqual(mouvements[0].type_mouvement, MouvementStock.TypeMouvement.SORTIE)
        self.assertEqual(mouvements[1].type_mouvement, MouvementStock.TypeMouvement.ENTREE)
        self.assertEqual(mouvements[1].quantite, 2)

    def test_modification_commande_cree_un_mouvement_pour_le_delta(self):
        self._post_commande(quantite=2)
        commande = Commande.objects.get(client=self.client_objet)
        self.client.post(reverse('commande_statut', args=[commande.pk]), {'statut': 'PRETE'})
        ligne = commande.lignes.get(produit=self.produit_stock)
        self.client.post(reverse('commande_update', args=[commande.pk]), {
            'client': self.client_objet.pk,
            'adresse_livraison': self.adresse.pk,
            'frais_livraison': '0',
            'a_livree': 'on',
            'statut': 'PRETE',
            'commentaire': '',
            'lignes-TOTAL_FORMS': '1',
            'lignes-INITIAL_FORMS': '1',
            'lignes-MIN_NUM_FORMS': '0',
            'lignes-MAX_NUM_FORMS': '1000',
            'lignes-0-id': ligne.pk,
            'lignes-0-produit': self.produit_stock.pk,
            'lignes-0-quantite': '5',
        })
        mouvements = MouvementStock.objects.filter(produit=self.produit_stock).order_by('id')
        self.assertEqual(mouvements.count(), 2)
        self.assertEqual(mouvements[0].quantite, 2)
        self.assertEqual(mouvements[1].type_mouvement, MouvementStock.TypeMouvement.SORTIE)
        self.assertEqual(mouvements[1].quantite, 3)


class MouvementStockTests(TestCase):
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
        self.produit_sans_stock = Produit.objects.create(
            categorie=self.categorie,
            nom="Sauce piquante",
            prix=500,
            soumis_stock=False,
            stock=0,
        )

    def test_bouton_stock_present_dans_liste_des_produits(self):
        response = self.client.get(reverse('products_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'btn-mouvement-stock')
        self.assertContains(response, 'form-mouvement-stock')

    def test_entree_augmente_le_stock_et_enregistre_le_mouvement(self):
        response = self.client.post(reverse('produit_stock_mouvement', args=[self.produit.pk]), {
            'type_mouvement': 'ENTREE',
            'quantite': '5',
            'description': 'Réception fournisseur',
        })
        self.assertRedirects(response, reverse('products_list'))
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.stock, 15)
        mouvement = MouvementStock.objects.get(produit=self.produit)
        self.assertEqual(mouvement.type_mouvement, MouvementStock.TypeMouvement.ENTREE)
        self.assertEqual(mouvement.quantite, 5)
        self.assertEqual(mouvement.description, 'Réception fournisseur')
        self.assertIsNotNone(mouvement.date)

    def test_sortie_diminue_le_stock_et_enregistre_le_mouvement(self):
        self.client.post(reverse('produit_stock_mouvement', args=[self.produit.pk]), {
            'type_mouvement': 'SORTIE',
            'quantite': '3',
            'description': 'Casse',
        })
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.stock, 7)
        mouvement = MouvementStock.objects.get(produit=self.produit)
        self.assertEqual(mouvement.type_mouvement, MouvementStock.TypeMouvement.SORTIE)
        self.assertEqual(mouvement.quantite, 3)

    def test_sortie_ne_descend_pas_en_dessous_de_zero(self):
        self.client.post(reverse('produit_stock_mouvement', args=[self.produit.pk]), {
            'type_mouvement': 'SORTIE',
            'quantite': '50',
            'description': 'Casse',
        })
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.stock, 0)

    def test_mouvement_ignore_pour_produit_non_soumis_stock(self):
        self.client.post(reverse('produit_stock_mouvement', args=[self.produit_sans_stock.pk]), {
            'type_mouvement': 'ENTREE',
            'quantite': '5',
            'description': '',
        })
        self.produit_sans_stock.refresh_from_db()
        self.assertEqual(self.produit_sans_stock.stock, 0)
        self.assertEqual(MouvementStock.objects.count(), 0)

    def test_quantite_invalide_ignoree(self):
        self.client.post(reverse('produit_stock_mouvement', args=[self.produit.pk]), {
            'type_mouvement': 'ENTREE',
            'quantite': 'abc',
            'description': '',
        })
        self.produit.refresh_from_db()
        self.assertEqual(self.produit.stock, 10)
        self.assertEqual(MouvementStock.objects.count(), 0)


class DetailPagesTests(TestCase):
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
        self.client_objet = Client.objects.create(nom="Diop", prenom="Moussa", telephone="771234567")
        self.adresse = AdresseLivraison.objects.create(client=self.client_objet, nom="Maison", adresse="Dakar, Sénégal")
        self.commande = Commande.objects.create(
            numero="CMD-000003",
            client=self.client_objet,
            adresse_livraison=self.adresse,
            total=10000,
        )
        self.ligne = LigneCommande.objects.create(
            commande=self.commande,
            produit=self.produit,
            quantite=2,
            prix_unitaire=5000,
            note="Sans oignons",
        )
        self.facture = Facture.objects.create(
            commande=self.commande,
            numero="FAC-000003",
            montant=10000,
        )
        self.paiement = Paiement.objects.create(
            facture=self.facture,
            montant=4000,
            mode_paiement=Paiement.ModePaiement.ESPECES,
            statut=Paiement.Statut.VALIDE,
        )

    def test_mouvements_stock_list_affiche_les_mouvements(self):
        MouvementStock.objects.create(
            produit=self.produit,
            type_mouvement=MouvementStock.TypeMouvement.ENTREE,
            quantite=5,
            description="Réception fournisseur",
        )
        response = self.client.get(reverse('mouvements_stock_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pizza Margherita')
        self.assertContains(response, 'Réception fournisseur')
        self.assertContains(response, 'badge-success')

    def test_mouvements_stock_list_page_accessible_sans_mouvement(self):
        response = self.client.get(reverse('mouvements_stock_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Historique des mouvements')
        self.assertContains(response, 'Aucun mouvement de stock')

    def test_commande_detail_affiche_infos_et_lignes(self):
        response = self.client.get(reverse('commande_detail', args=[self.commande.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CMD-000003')
        self.assertContains(response, 'Diop Moussa')
        self.assertContains(response, 'Pizza Margherita')
        self.assertContains(response, 'Sans oignons')
        self.assertContains(response, '10 000 CDF')

    def test_facture_detail_affiche_la_facture_professionnelle(self):
        response = self.client.get(reverse('facture_detail', args=[self.facture.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'FACTURE')
        self.assertContains(response, 'FAC-000003')
        self.assertContains(response, 'Pizza Margherita')
        self.assertContains(response, 'Reste à payer')
        self.assertContains(response, 'Espèces')
        self.assertContains(response, 'Imprimer')

    def test_produit_detail_affiche_infos_et_mouvements(self):
        MouvementStock.objects.create(
            produit=self.produit,
            type_mouvement=MouvementStock.TypeMouvement.ENTREE,
            quantite=5,
            description="Réception fournisseur",
        )
        response = self.client.get(reverse('produit_detail', args=[self.produit.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pizza Margherita')
        self.assertContains(response, self.produit.reference)
        self.assertContains(response, 'Pizzas')
        self.assertContains(response, '5 000 CDF')
        self.assertContains(response, 'Total vendu')

    def test_client_detail_affiche_infos_adresses_et_commandes(self):
        response = self.client.get(reverse('client_detail', args=[self.client_objet.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Diop Moussa')
        self.assertContains(response, '771234567')
        self.assertContains(response, 'Maison')
        self.assertContains(response, 'Dakar, Sénégal')
        self.assertContains(response, 'CMD-000003')
        self.assertContains(response, 'Historique des commandes')
