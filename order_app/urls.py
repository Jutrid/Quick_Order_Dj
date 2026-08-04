from django.urls import path
from order_app import views

urlpatterns = [
    path('order/list', views.order_list, name='order_list'),
    path('order/create', views.commande_create, name='commande_create'),
    path('order/<int:pk>/edit', views.commande_update, name='commande_update'),
    path('clients/list', views.clients_list, name='clients_list'),
    path('clients/create', views.client_create, name='client_create'),
    path('products/list', views.products_list, name='products_list'),
    path('products/create', views.produit_create, name='produit_create'),
    path('products/<int:pk>/edit', views.produit_update, name='produit_update'),
    path('factures/list', views.factures_list, name='factures_list'),
    path('paiements/list', views.paiements_list, name='paiements_list'),
    path('paiements/create', views.paiement_create, name='paiement_create'),
    path('livraisons/list', views.livraisons_list, name='livraisons_list'),
    path('adresses/livraison', views.adresses_livraison_list, name='adresses_livraison_list'),
    path('adresses/create', views.adresse_create, name='adresse_create'),
    path('categories/list', views.categories_list, name='categories_list'),
    path('categories/create', views.categorie_create, name='categorie_create'),
    path('tailles/list', views.tailles_list, name='tailles_list'),
    path('tailles/create', views.taille_create, name='taille_create'),
    path('livreurs/list', views.livreurs_list, name='livreurs_list'),
    path('livreurs/create', views.livreur_create, name='livreur_create'),
]