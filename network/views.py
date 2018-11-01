from django.shortcuts import render as render_2
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import connection
from django.db.models import Q

from .models import *
from datetime import datetime, timedelta


import random
import string

def token_generator(size=200, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
# Create your views here.

def render(request, html, dico = {}):
	print(connection.queries)
	for k in connection.queries:
		file = open('requete.sql','a')
		file.write(k['sql']+'\n')
		file.close()
	return render_2(request, html, dico)


class Onglet:
	def __init__(self, reserver, trajet, connecter):
		self.reserver = reserver
		self.trajet = trajet
		self.connecter = connecter

def accueil(request):
	liste_gare = Gare.objects.values_list('nom', flat = True)
	connection.queries
	dico = {
		'onglet':Onglet(False,False,False),
		'liste_gare':liste_gare,
	}
	return render(request, "accueil.html", dico)

def rechercher_trajet(request):
	erreur = False
	message = ''
	gare_depart = ''
	gare_arrivee = ''
	date = ''
	if request.method == 'POST':
		form = request.POST
		gare_depart = form['gare_depart']
		gare_arrivee = form['gare_arrivee']
		date = form['date']
		if Gare.objects.filter(nom = gare_depart).exists() == False :
			erreur = True
			message = "La gare de départ sélectionnée n'existe pas"
		elif Gare.objects.filter(nom = gare_arrivee).exists() == False :
			erreur = True
			message = "La gare d'arrivée sélectionnée n'existe pas"
		elif gare_arrivee == gare_depart:
			erreur = True
			message = "Merci de sélectionner deux gares différentes"
		elif form['modifier'] == '0':
			print('test')
			gare_depart = Gare.objects.filter(nom = gare_depart).get()
			gare_arrivee = Gare.objects.filter(nom = gare_arrivee).get()
			date = datetime.strptime(form['date'], '%Y-%m-%d')
			date_fin = date + timedelta(days=1, hours=0, minutes=0, seconds=0)
			liste_train_depart = GareArret.objects.filter(heure__gte = date).filter(heure__lte = date_fin).filter(gare = gare_depart).values_list('train_id', flat = True)
			liste_train = []
			for train in liste_train_depart:
				liste_gare = GareArret.objects.filter(train_id = train)
				if liste_gare.filter(gare = gare_depart).get().numero < liste_gare.filter(gare = gare_arrivee).get().numero:
					liste_train.append(Train.objects.get(id = train))
			requete = Requete(gare_depart.nom, gare_arrivee.nom, date)
			liste_resultat = []
			for train in liste_train:
				numero = train.id
				print(type(gare_depart))
				gare_arret_depart = GareArret.objects.filter(train_id = train).filter(gare_id = gare_depart.id).get()
				gare_arret_arrivee = GareArret.objects.filter(train_id = train).filter(gare = gare_arrivee).get()
				billet_dispo = Billet.objects.filter(place__voiture__train=train).filter(gare_depart__numero__lte = gare_arret_arrivee.numero-1).filter(gare_arrivee__numero__gte = gare_arret_depart.numero+1)
				nb_place = Place.objects.filter(voiture__train = train).count() - billet_dispo.count()
				gare_depart_str = gare_arret_depart.gare.nom
				gare_arrivee_str = gare_arret_arrivee.gare.nom
				date_depart = gare_arret_depart.heure.strftime('%d/%m/%Y')
				date_arrivee = gare_arret_arrivee.heure.strftime('%d/%m/%Y')
				heure_depart = gare_arret_depart.heure.strftime('%H:%M')
				heure_arrivee = gare_arret_arrivee.heure.strftime('%H:%M')
				prix = random.randint(80,100)
				liste_resultat.append(Resultat_train(
						numero,
						gare_depart_str,
						gare_arrivee_str,
						date_depart,
						date_arrivee,
						heure_depart,
						heure_arrivee,
						nb_place,
						prix,
						gare_arret_depart.id,
						gare_arret_arrivee.id)
				)

			gare_depart = gare_depart.nom
			gare_arrivee = gare_arrivee.nom
			token = Token.objects.create(valeur = token_generator(), date_fin = datetime.now()+timedelta(days = 0, hours = 1, minutes = 0, seconds = 0)) 
			dico = {
				'token':token.valeur,
				'gare_depart':gare_depart,
				'gare_arrivee':gare_arrivee,
				'date': date.strftime('%d/%m/%Y'),
				'requete':requete,
				'liste_train' : liste_resultat
			}
			return render(request, "resultat_recherche.html", dico)
		elif form['modifier'] == '1':
			gare_depart = form['gare_depart']
			gare_arrivee = form['gare_arrivee']
			date = form['date']
		print(form)
	liste_gare = Gare.objects.values_list('nom', flat = True)
	dico = {
		'onglet':Onglet(True,False,False),
		'message':message,
		'liste_gare':liste_gare,
		'gare_depart':gare_depart,
		'gare_arrivee':gare_arrivee,
		'date':date,
	}
	return render(request, "rechercher_billet.html", dico)


class Resultat_train:
	def __init__(self, numero, gare_depart, gare_arrivee, date_depart, date_arrivee, heure_depart, heure_arrivee, place_restante, prix, gare_arret_depart_id, gare_arret_arrivee_id):
		self.numero = numero
		self.gare_depart = gare_depart
		self.gare_arrivee = gare_arrivee
		self.date_depart = date_depart
		self.date_arrivee = date_arrivee
		self.heure_depart = heure_depart
		self.heure_arrivee = heure_arrivee
		self.place_restante = place_restante
		self.prix = prix
		self.complet = place_restante == 0
		self.gare_arret_depart_id =gare_arret_depart_id
		self.gare_arret_arrivee_id = gare_arret_arrivee_id
		
class Requete:
	def __init__(self, gare_depart, gare_arrivee, date):
		self.gare_depart = gare_depart
		self.gare_arrivee = gare_arrivee
		self.date = date.strftime('%Y-%m-%d')
		
		
		
def resultat_recherche(request):
	liste_train = []
	for k in range(10):
		liste_train.append(Resultat_train('011001','Paris','Lyon','02/10/2018', '02/10/2018', '20h10', '22h10', '30', '200'))
	dico = {
		'liste_train' : liste_train
	}
	return render(request, "resultat_recherche.html", dico)



class Reservation:
	def __init__(self,numero, gare_depart, gare_arrivee, date_depart, date_arrivee, heure_depart, heure_arrivee, prix, voiture, place):
		self.numero = numero
		self.gare_depart = gare_depart
		self.gare_arrivee = gare_arrivee
		self.date_depart = date_depart
		self.date_arrivee = date_arrivee
		self.heure_depart = heure_depart
		self.heure_arrivee = heure_arrivee
		self.prix = prix
		self.voiture = voiture
		self.place = place


def reserver_billet(request):
	if request.method == 'POST':
		form = request.POST
		if not Token.objects.filter(valeur = form['token']).exists():
			liste_gare = Gare.objects.values_list('nom', flat = True)
			return render(request, 'rechercher_billet.html', {'liste_gare':liste_gare, 'erreur':True, 'message':'Votre session de reservation a expirée'})
		Token.objects.filter(valeur = form['token']).delete()	
		train = Train.objects.get(id = int(form['train_id']))
		liste_place = Place.objects.filter(voiture__train=train).filter(billet=None)
		if not liste_place.exists():
			pass
		elif liste_place.filter(situation__nom = form['cote']).exists():
			place = liste_place.filter(situation__nom = form['cote'])[0]
		else:
			place = liste_place[0]
		gare_arret_depart = GareArret.objects.get(id = int(form['gare_arret_depart_id']))
		gare_arret_arrivee = GareArret.objects.get(id = int(form['gare_arret_arrivee_id']))
		liste_billet = Billet.objects.filter(place__voiture__train=train)
		client = Client.objects.filter(user = request.user).get()
		Billet.objects.create(
			place = place, 
			client = client,
			gare_depart = gare_arret_depart,
			gare_arrivee = gare_arret_arrivee,
			prix = 100)
		reservation = Reservation (
			train.id,
			gare_arret_depart.gare.nom,
			gare_arret_arrivee.gare.nom,
			gare_arret_depart.heure.strftime('%d/%m/%Y'),
			gare_arret_arrivee.heure.strftime('%d/%m/%Y'),
			gare_arret_depart.heure.strftime('%H:%M'),
			gare_arret_arrivee.heure.strftime('%H:%M'),
			100,
			place.voiture.numero,
			place.numero
		)
		
	dico = {
		'reservation':reservation
	}
	return render(request, 'reserver_billet.html', dico)

def connexion(request):
	if request.method == 'POST':
		form = request.POST
		if form['type'] == 'connexion':
			logout(request)
			mail = form['mail']
			password = form['password']
			user = authenticate(request, username=mail, password=password)
			if user is not None:
				login(request,user)
			else:
				return render(request,'connexion.html', {'message' : 'Mot de passe incorrect ou utilisateur inexistant'})
			if (request.GET!={}): #redirection si il manquait une authentification
				return HttpResponseRedirect(request.GET['next'])
			return HttpResponseRedirect(reverse('accueil'))
		elif form['type'] == 'creer':
			logout(request)
			mail = form['mail']
			password = form['password']
			first_name = form['prenom']
			last_name = form['nom']
			if Statut.objects.filter(nom = form['statut']).exists():
				statut = Statut.objects.filter(nom = form['statut']).get()
			else:
				statut = Statut.objects.filter(nom = 'adulte').get()
			if User.objects.filter(email = mail).exists():
				return render(request,'connexion.html', {'message' : 'Cet e-mail est déjà utilisé'})
			user = User.objects.create_user(mail, mail, password)
			user.first_name = first_name
			user.last_name = last_name
			user.save()
			Client.objects.create(
				user = user,
				reduction = Reduction.objects.filter(nom = 'Aucune').get(),
				statut = statut
			)
			login(request, user)
	onglet = Onglet(False,False,True)
	dico = {
		'onglet':onglet,
	}
	return render(request, "connexion.html", dico)


class Element:
	def __init__(self, element, booleen):
		self.element = element
		self.booleen = booleen

def profil(request):
	message = ""
	if request.method == 'POST':
		form = request.POST
		user = request.user
		client = Client.objects.filter(user = user).get()
		client.reduction = Reduction.objects.filter(nom = form['reduction']).get()
		client.statut = Statut.objects.filter(nom = form['statut']).get()
		client.save()
		user.first_name = form['first_name']
		user.last_name = form['last_name']
		if form['email'] != user.email :
			if not User.objects.filter(email = form['email']).exists():
				user.email = form['email']
			else:
				message = "Le mail "+form['email']+" est déjà utilisé par un autre utilisateur"
		user.save()
	client = Client.objects.filter(user = request.user).get()		
	liste_reduction = Reduction.objects.values_list('nom', flat = True)
	reduction = []
	for element in liste_reduction:
		reduction.append(Element(element, client.reduction.nom == element))
	
	liste_statut = Statut.objects.values_list('nom', flat = True)
	statut = []
	for element in liste_statut:
		statut.append(Element(element, client.statut.nom == element))
	
	
	dico = {
		'message':message,
		'liste_statut':statut,
		'liste_reduction':reduction,
		'client':client,
		'onglet':Onglet(False,True,False),
	}
	return render(request, 'profil.html',dico)



def deconnexion(request):
	logout(request)
	return HttpResponseRedirect(reverse('connexion'))




def reservation(request):

	client = Client.objects.filter(user = request.user).get()
	liste_billets = Billet.objects.filter(client = client).order_by('-gare_depart__heure')
	liste_reservation = []
	for billet in liste_billets:
		train = billet.place.voiture.train
		place = billet.place
		reservation = Reservation (
			train.id,
			billet.gare_depart.gare.nom,
			billet.gare_arrivee.gare.nom,
			billet.gare_depart.heure.strftime('%d/%m/%Y'),
			billet.gare_arrivee.heure.strftime('%d/%m/%Y'),
			billet.gare_depart.heure.strftime('%H:%M'),
			billet.gare_arrivee.heure.strftime('%H:%M'),
			100,
			place.voiture.numero,
			place.numero
		)
		liste_reservation.append(reservation)
	dico = {
		'liste_reservation':liste_reservation,
	}
	return render(request, 'reservation.html', dico)

def admin_interface(request):
	liste_gare = Gare.objects.values_list('nom', flat = True)
	liste_agence = Agence.objects.values_list('nom', flat=True)
	message = ''
	if request.method == 'POST':
		form = request.POST
		gares = form.getlist('gares')
		liste_gare = []
		dates = form.getlist('dates')
		heures = form.getlist('heures')
		voitures = form.getlist('voitures')
		prix = form['prix']
		for gare in gares:
			if gare == '':
				pass
			elif not Gare.objects.filter(nom = gare).exists():
				message = 'La gare "'+gare+'" n\'existe pas'
			else:
				liste_gare.append(Gare.objects.filter(nom = gare).get())
		datetimes = []
		for i in range(len(dates)):
			datetimes.append(datetime.strptime(dates[i]+' '+heures[i],'%Y-%m-%d %H:%M'))
		for i in range(len(datetimes)-1):
			if datetimes[i]>datetimes[i+1]:
				message = 'La liste des gares n\'a pas été rentrée dans l\'ordre chronologique' 
		if message != '':
			dico = {
				'message':message,
				'liste_gare':liste_gare,
		
			}
			return render(request, 'admin.html', dico)
		else:
			train = Train.objects.create()
			gare_arret = []
			for i in range(len(liste_gare)):
				gare_arret.append(GareArret(gare = gares[i], heure = datetimes[i], train = train, numero = i))
			GareArret.objects.bulk_create(gare_arret)
			liste_voitures = []
			for i,voiture in enumerate(voitures):
				liste_voitures.append(Voiture(train = train, numero = i))
			Voiture.objects.bulk_create(liste_voitures)
			liste_place = []
			for i,nb_place in enumerate(voitures):
				voiture = liste_voitures[i]
				for j in range(int(nb_place)):
					liste_place.append(Place(voiture = voiture,numero = j, situation_id = j%2+1))
			Place.objects.bulk_create(liste_place)
		
	print(request.POST)
	dico = {
		'message':message,
		'liste_gare':liste_gare,
		'liste_agence':liste_agence
		
	}
	return render(request, 'admin.html', dico)



def admin_recherche_billet(request):
	if request.method == 'POST':
		form = request.POST
		print(form)
		numero = int(form['numero_billet'])
		if not Billet.objects.filter(id = numero).exists():
			return JsonResponse({'message':'Le billet indiqué n\'existe pas'}, status = 500)
		if not Agence.objects.filter(nom = form['agence']).exists():
			return JsonResponse({'message':'L\'agence indiquée n\'existe pas'}, status = 500)
		agence = Agence.objects.filter(nom = form['agence']).get().nom
		billet =  Billet.objects.get(id = numero)
		if billet.confirmation == None:
			validation = 0
		else:
			validation = billet.confirmation.validation
		dico = {
			'numero_billet' : billet.id,
			'numero' : billet.place.voiture.train.id,
			'gare_depart' : billet.gare_depart.gare.nom,
			'gare_arrivee' : billet.gare_arrivee.gare.nom,
			'date_depart' : billet.gare_depart.heure.strftime('%d/%m/%Y'),
			'date_arrivee' : billet.gare_arrivee.heure.strftime('%d/%m/%Y'),
			'heure_depart' : billet.gare_depart.heure.strftime('%H:%M'),
			'heure_arrivee' : billet.gare_arrivee.heure.strftime('%H:%M'),
			'prix' : billet.prix,
			'reduction':billet.reduction.nom,
			'voiture' : billet.place.voiture.numero,
			'place' : billet.place.numero,
			'payee' : validation,
			'agence' : agence,
		}
		return JsonResponse(dico)


def admin_paiement(request):
	liste_gare = Gare.objects.values_list('nom', flat = True)
	liste_agence = Agence.objects.values_list('nom', flat=True)
	if request.method == 'POST':
		form = request.POST
		numero = form['numero']
		billet =  Billet.objects.get(id = numero)
		if billet.confirmation == None:
			billet.confirmation = Confirmation.objects.create(validation = 1)
		else:
			billet.confirmation.validation = 1
		billet.save()

		dico = {
			'message_2': "Le paiement a bien été effectué",
			'liste_gare':liste_gare,
			'liste_agence':liste_agence
		
		}
		return render(request, 'admin.html', dico)
	dico = {
		'liste_gare':liste_gare,
		'liste_agence':liste_agence
	}
	return render(request, 'admin.html', dico)



def init_base(request):
	"""
	
	"""
	if request.method == 'POST':
		print('Coucou')
		
		Situation.objects.create(nom = 'fenetre')
		Situation.objects.create(nom = 'couloir')
		Statut.objects.create(nom = 'adulte')
		Statut.objects.create(nom = 'enfant')
		Reduction.objects.create(nom = 'Aucune', pourcentage = 1)
		Reduction.objects.create(nom = 'Etudiant', pourcentage = 0.5)
		Reduction.objects.create(nom = 'Tarif reduit', pourcentage = 0.7)
		Reduction.objects.create(nom = 'Handicape', pourcentage = 0.3)
		Reduction.objects.create(nom = 'Famille Nombreuse', pourcentage = 0.8)
		Ville.objects.create(nom = 'Paris')
		Ville.objects.create(nom = 'Lyon')
		Ville.objects.create(nom = 'Strasbourg')
		Ville.objects.create(nom = 'Macon')
		Ville.objects.create(nom = 'Rouen')
		Ville.objects.create(nom = 'Caen')
		
		
		Gare.objects.create(nom = 'Lyon Perrache', ville = Ville.objects.filter(nom = 'Lyon').get())
		Gare.objects.create(nom = 'Lyon Part-Dieu', ville = Ville.objects.filter(nom = 'Lyon').get())
		Gare.objects.create(nom = 'Macon', ville = Ville.objects.filter(nom = 'Macon').get())
		Gare.objects.create(nom = 'Paris Gare de Lyon', ville = Ville.objects.filter(nom = 'Paris').get())
		Gare.objects.create(nom = 'Paris Gare de l\'Est', ville = Ville.objects.filter(nom = 'Paris').get())
		Gare.objects.create(nom = 'Paris Gare du Nord', ville = Ville.objects.filter(nom = 'Paris').get())
		Gare.objects.create(nom = 'Paris Gare Saint Lazard', ville = Ville.objects.filter(nom = 'Paris').get())
		Gare.objects.create(nom = 'Strasbourg', ville = Ville.objects.filter(nom = 'Strasbourg').get())
		Gare.objects.create(nom = 'Rouen', ville = Ville.objects.filter(nom = 'Rouen').get())
		Gare.objects.create(nom = 'Caen', ville = Ville.objects.filter(nom = 'Caen').get())	

		Agence.objects.create(nom = 'Agence de Lyon 1')
	
		for k in range(100):
			Train.objects.create()
		liste_voiture = []
		for k in range(1000):
			liste_voiture.append(Voiture.objects.create())
		
		compteur = 0
		liste_place = []
		for voiture in liste_voiture:
			nombre_place = random.randint(35,50)
			for k in range(nombre_place):
				compteur += 1
				if compteur%2 == 0:
					liste_place.append(Place(voiture = voiture, situation = Situation.objects.get(pk = 1), numero = k))
				else:
					liste_place.append(Place(voiture = voiture, situation = Situation.objects.get(pk = 2), numero = k))
		Place.objects.bulk_create(liste_place)
	
		for k in range(1,101):
			train = Train.objects.get(pk = k)
			for j in range(1,11):
				id_voiture = 10*(k-1)+j
				voiture = Voiture.objects.get(pk = id_voiture)
				voiture.train = train
				voiture.numero = j
				voiture.save()
			if k>50:
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Lyon Perrache').get(), train = train, numero = 1, heure = datetime.strptime("21/11/18 16:30", "%d/%m/%y %H:%M"))
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Lyon Part-Dieu').get(), train = train, numero = 2, heure = datetime.strptime("21/11/18 17:00", "%d/%m/%y %H:%M"))
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Macon').get(), train = train, numero = 3, heure = datetime.strptime("21/11/18 17:30", "%d/%m/%y %H:%M"))
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Paris Gare de Lyon').get(), train = train, numero = 4, heure = datetime.strptime("21/11/18 18:30", "%d/%m/%y %H:%M"))
			else:
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Paris Gare Saint Lazard').get(), train = train, numero = 1, heure = datetime.strptime("21/11/18 14:30", "%d/%m/%y %H:%M"))
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Rouen').get(), train = train, numero = 2, heure = datetime.strptime("21/11/18 15:30", "%d/%m/%y %H:%M"))
				GareArret.objects.create(gare = Gare.objects.filter(nom = 'Caen').get(), train = train, numero = 3, heure = datetime.strptime("21/11/18 16:30", "%d/%m/%y %H:%M"))
			
		user = User.objects.create_user('karah@ec-lyon.fr', 'karah@ec-lyon.fr', 'geoffrey')
		user.first_name = 'Mathieu'
		user.last_name = 'Bourdin'
		user.save()
		Client.objects.create(user = user, reduction = Reduction.objects.filter(nom = 'Etudiant').get(), statut = Statut.objects.filter(nom = 'adulte').get())
		
		liste_billet = []
		liste_train = [Train.objects.get(pk = i) for i in range(1,10)]
		for train in liste_train:
			liste_voiture = Voiture.objects.filter(train = train).order_by('numero')
			for voiture in liste_voiture:
				liste_place = Place.objects.filter(voiture = voiture)
				for place in liste_place:
					if GareArret.objects.filter(train=train).filter(gare =Gare.objects.filter(nom = 'Lyon Perrache').get()).exists():
						liste_billet.append(Billet(
							gare_depart = GareArret.objects.filter(train=train).filter(gare =Gare.objects.filter(nom = 'Lyon Perrache').get()).get(),
							gare_arrivee = GareArret.objects.filter(train=train).filter(gare =Gare.objects.filter(nom = 'Paris Gare de Lyon').get()).get(),
							prix = 100,
							reduction = Reduction.objects.filter(nom = 'Etudiant').get(),
							place = place,
							client = Client.objects.filter(user__email = 'karah@ec-lyon.fr').get(),
							agence = Agence.objects.get(pk = 1),
						))
					else:
						liste_billet.append(Billet(
							gare_depart = GareArret.objects.filter(train=train).filter(gare =Gare.objects.filter(nom = 'Paris Gare Saint Lazard').get()).get(),
							gare_arrivee = GareArret.objects.filter(train=train).filter(gare =Gare.objects.filter(nom = 'Caen').get()).get(),
							prix = 80,
							reduction = Reduction.objects.filter(nom = 'Etudiant').get(),
							place = place,
							client = Client.objects.filter(user__email = 'karah@ec-lyon.fr').get(),
							agence = Agence.objects.get(pk = 1),
						))
		Billet.objects.bulk_create(liste_billet)
	
	dico = {
		'onglet':Onglet(False,False,False),
	}
	return render(request, "init_base.html", dico)
	

	
	
	
	



	
		
