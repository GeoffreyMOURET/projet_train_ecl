from django.urls import path
from . import views

"""
Here is put all the URLs of the website and their link to the funtion to call.

Syntax is like this :
Inside the list "urlpatterns", put arguments with the following format :
path('path_to_the_page/without/the_site_name_at_the_beguinning/<function_arg>', views.function_to_call, name = 'name') (to use the {% url name%} in html file to get the url of the page.

"""


urlpatterns = [
    path('accueil', views.accueil, name = 'accueil'),
    path('rechercher_trajet', views.rechercher_trajet, name = 'rechercher_billet'),
    path('init_base', views.init_base, name = 'init_base'),
    path('connexion', views.connexion, name = 'connexion'),
    path('profil', views.profil, name = 'profil'),
    path('reserver_billet', views.reserver_billet, name = 'reserver_billet'),
    path('deconnexion', views.deconnexion, name = 'deconnexion'),
    path('reservation', views.reservation, name = 'reservation'),
    path('admin', views.admin_interface, name = 'admin_interface'),
    path('admin_recherche_billet', views.admin_recherche_billet, name = 'admin_recherche_billet'),
    path('admin_paiement', views.admin_paiement, name = 'admin_paiement'),
    path('admin_creer_gare', views.admin_creer_gare, name = 'admin_creer_gare'),
    
]

