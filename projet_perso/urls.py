from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls), #application d'administration, non-utilisée ici
    path('train/', include('network.urls')), #application pour le projet sncf
]
