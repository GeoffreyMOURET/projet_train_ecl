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

def get_liste_gare():
	with connection.cursor() as cursor:
		cursor.execute("SELECT `gare`.`nom` FROM `gare`")
		liste_tuple = cursor.fetchall()
		liste_gare = []
		for k in liste_tuple:
			liste_gare.append(k[0])
		return liste_gare

def get_liste_statut():
	with connection.cursor() as cursor:
		cursor.execute("SELECT `statut`.`nom` FROM `statut`")
		liste_tuple = cursor.fetchall()
		liste_statut = []
		for k in liste_tuple:
			liste_statut.append(k[0])
		return liste_statut

def get_liste_ville():
	with connection.cursor() as cursor:
		cursor.execute("SELECT `ville`.`nom` FROM `ville`")
		liste_tuple = cursor.fetchall()
		liste_ville = []
		for k in liste_tuple:
			liste_ville.append(k[0])
		return liste_ville

def get_liste_reduction():
	with connection.cursor() as cursor:
		cursor.execute("SELECT `statut`.`nom` FROM `statut`")
		liste_tuple = cursor.fetchall()
		liste_reduction = []
		for k in liste_tuple:
			liste_reduction.append(k[0])
		return liste_reduction

def get_liste_agence():
	with connection.cursor() as cursor:
		cursor.execute("SELECT `agence`.`nom` FROM `agence`")
		liste_tuple = cursor.fetchall()
		liste_agence = []
		for k in liste_tuple:
			liste_agence.append(k[0])
		return liste_agence

def token_generator(size=200, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
	return ''.join(random.choice(chars) for _ in range(size))
# Create your views here.

def render(request, html, dico = {}):
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
	liste_gare = get_liste_gare()
	dico = {
		'onglet':Onglet(False,False,False),
		'liste_gare':liste_gare,
	}
	return render(request, "accueil.html", dico)

def rechercher_trajet(request):
	with connection.cursor() as cursor:
		message = ''
		gare_depart = ''
		gare_arrivee = ''
		date = ''
		if request.method == 'POST':
			form = request.POST
			gare_depart = form['gare_depart'].replace("\"","'")
			gare_arrivee = form['gare_arrivee'].replace("\"","'")
			date = form['date']
			cursor.execute("SELECT COUNT(id) FROM `gare` WHERE `gare`.`nom` = '"+gare_depart+"' LIMIT 1")
			gare_depart_exists = cursor.fetchone()[0] == 1
			cursor.execute("SELECT COUNT(id) FROM `gare` WHERE `gare`.`nom` = '"+gare_arrivee+"' LIMIT 1")
			gare_arrivee_exists = cursor.fetchone()[0] == 1
			if not gare_depart_exists :
				message = "La gare de départ sélectionnée n'existe pas"
			elif not gare_arrivee_exists :
				message = "La gare d'arrivée sélectionnée n'existe pas"
			elif gare_arrivee == gare_depart:
				message = "Merci de sélectionner deux gares différentes"
			elif form['modifier'] == '0':
				cursor.execute("SELECT id FROM `gare` WHERE `gare`.`nom` = '"+gare_depart+"' LIMIT 1")
				gare_depart_id = cursor.fetchone()[0]
				cursor.execute("SELECT id FROM `gare` WHERE `gare`.`nom` = '"+gare_arrivee+"' LIMIT 1")
				gare_arrivee_id = cursor.fetchone()[0]
				
				date = datetime.strptime(form['date'], '%Y-%m-%d')
				date_fin = date + timedelta(days=1, hours=0, minutes=0, seconds=0)
				cursor.execute("SELECT `gare_arret`.`train_id` FROM `gare_arret` WHERE (`gare_arret`.`heure` >= '"+date.strftime("%Y-%m-%d")+" 00:00:00' AND `gare_arret`.`heure` <= '"+date_fin.strftime("%Y-%m-%d")+" 00:00:00' AND `gare_arret`.`gare_id` = "+str(gare_depart_id)+")")
				liste_train_depart_id = cursor.fetchall()
				liste_train = []
				for train in liste_train_depart_id:
					train = train[0]
					cursor.execute("SELECT `gare_arret`.`numero` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_depart_id)+")")
					numero_depart = cursor.fetchone()[0]
					cursor.execute("SELECT `gare_arret`.`numero` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_arrivee_id)+")")
					numero_arrivee = cursor.fetchone()[0]
					
					if numero_depart < numero_arrivee:
						liste_train.append(train)
				requete = Requete(gare_depart, gare_arrivee, date)
				liste_resultat = []
				for train in liste_train:
					numero = train
					cursor.execute("SELECT `gare_arret`.`id`,`gare_arret`.`numero`,`gare_arret`.`heure` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_depart_id)+")")
					id_depart, numero_depart, heure_depart = cursor.fetchone()
					
					cursor.execute("SELECT `gare_arret`.`id`,`gare_arret`.`numero`,`gare_arret`.`heure` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_arrivee_id)+")")
					id_arrivee, numero_arrivee,heure_arrivee = cursor.fetchone()
					
					cursor.execute("SELECT COUNT(`place`.`id`) FROM `place` INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) WHERE `voiture`.`train_id` = "+str(train))
					nb_place_total = cursor.fetchone()[0]
					cursor.execute("SELECT COUNT(`billet`.`id`) FROM `billet` INNER JOIN `place` ON (`billet`.`place_id` = `place`.`id`) INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) INNER JOIN `gare_arret` ON (`billet`.`gare_depart_id` = `gare_arret`.`id`) INNER JOIN `gare_arret` GA ON (`billet`.`gare_arrivee_id` = GA.`id`) WHERE (`voiture`.`train_id` = "+str(train)+" AND `gare_arret`.`numero` <= "+str(numero_arrivee-1)+" AND GA.`numero` >= "+str(numero_depart+1)+")")
					nb_billet_reserve = cursor.fetchone()[0]
					nb_place = nb_place_total - nb_billet_reserve
					date_depart = heure_depart.strftime('%d/%m/%Y')
					date_arrivee = heure_arrivee.strftime('%d/%m/%Y')
					heure_depart = heure_depart.strftime('%H:%M')
					heure_arrivee = heure_arrivee.strftime('%H:%M')
					prix = random.randint(80,100)
					liste_resultat.append(Resultat_train(
							numero,
							gare_depart,
							gare_arrivee,
							date_depart,
							date_arrivee,
							heure_depart,
							heure_arrivee,
							nb_place,
							prix,
							id_depart,
							id_arrivee)
					)

				date_fin = datetime.now()+timedelta(days = 0, hours = 1, minutes = 0, seconds = 0)
				token = token_generator()
				cursor.execute("INSERT INTO `network_token` (`valeur`, `date_fin`) VALUES ('"+token+"', '"+date_fin.strftime('%Y-%m-%d %H:%M:%S')+"')")
				dico = {
					'token':token,
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
			
		liste_gare = get_liste_gare()
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
			liste_gare = get_liste_gare()
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
	"""
	This method is called when the user wants to login or create a new account.
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'connexion.html',dico) 
			where 
		dico = {
			'onglet': (an Onglet object) Use to overline the good tab in the page,
		}
	"""
	if request.method == 'POST':
		# Récupération du formulaire
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
	"""
	A class used to store data. 
	Each element contains a string (self.element) and a boolean (self.booleen) to know whether the element design the user or not.
	"""
	def __init__(self, element, booleen):
		self.element = element
		self.booleen = booleen

def profil(request):
	"""
	This method is called when the profil page of an user is created
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'profil.html',dico) 
			where 
		dico = {
			'message': (str) An error message in case of error. Default value : ''
			'nom': (str) The lastname of the user
			'prenom': (str) The first name of the user
			'client_statut': (str) The status of the user
			'client_reduction': (str) The reduction of the user
			'liste_statut': (list) The list of all existing status in the database
			'liste_reduction': (list) The list of all existing reductions in the database
			'client_email': (str) The email of the client,
			'onglet': (an Onglet object) Use to overline the good tab in the page,
		}
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		######### Récupération du compte de l'utilisateur ###############
		cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%s')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
		session_data = cursor.fetchone()[0]
		message = ""
		user_id = request.session.decode(session_data)['_auth_user_id']
		#################################################################
		
		if request.method == 'POST':
			# Récupération du formulaire
			form = request.POST
			
			# Récupération de l'id du client
			cursor.execute("SELECT `client`.`id` FROM `client` WHERE `client`.`user_id` = "+str(user_id))
			client_id = cursor.fetchone()[0]
			
			# Récupération de l'id de la réduction du formulaire
			cursor.execute("SELECT `reduction`.`id` FROM `reduction` WHERE `reduction`.`nom` = '"+form["reduction"]+"'" )
			reduction_id = cursor.fetchone()[0]
			
			# Récupération de l'id du statut du formulaire
			cursor.execute("SELECT `statut`.`id` FROM `statut` WHERE `statut`.`nom` = '"+form['statut']+"'" )
			statut_id = cursor.fetchone()[0]
			
			#Mise à jour de la table 'client'
			cursor.execute("UPDATE `client` SET `reduction_id` = "+str(reduction_id)+", `statut_id` = "+str(statut_id)+" WHERE `client`.`id` = "+str(client_id))
			
			#Récupération de l'email de l'utilisateur
			cursor.execute("SELECT `auth_user`.`email` FROM `auth_user` WHERE `auth_user`.`id` = "+str(user_id))
			user_email = cursor.fetchone()[0]
			
			# Si l'email a été modifié...
			if form['email'] != user_email :
				cursor.execute("SELECT COUNT(id) FROM `auth_user` WHERE `auth_user`.`nom` = '"+form['email']+"' LIMIT 1")
				user_exists = cursor.fetchone()[0] == 1
				#... Et qu'un utilisateur ne possède pas déjà cet email...
				if not user_exists:
					# La modification est validée
					user.email = form['email']
					cursor.execute("UPDATE `auth_user` SET `username` = '"+form['email']+"', `first_name` = '"+form['first_name']+"', `last_name` = '"+form['last_name']+"', `email` = '"+form['email']+"' WHERE `auth_user`.`id` = "+str(user_id))
				# Sinon, la modification de l'email est rejetée
				else:
					message = "Le mail "+form['email']+" est déjà utilisé par un autre utilisateur"
					cursor.execute("UPDATE `auth_user` SET `username` = '"+form['email']+"', `first_name` = '"+form['first_name']+"', `last_name` = '"+form['last_name']+"' WHERE `auth_user`.`id` = "+str(user_id))
			
		# Récupération des informations concernant le profil de l'utilisateur
		cursor.execute("SELECT `auth_user`.`first_name`, `auth_user`.`last_name`, `auth_user`.`email` FROM `auth_user` WHERE `auth_user`.`id` = "+str(user_id))
		first_name, last_name, email = cursor.fetchone()
		cursor.execute("SELECT `client`.`statut_id`,`client`.`reduction_id` FROM `client` WHERE `client`.`user_id` = "+str(user_id))
		statut_id, reduction_id = cursor.fetchone()
		cursor.execute("SELECT `statut`.`nom` FROM `statut` WHERE `statut`.`id` = "+str(statut_id))
		client_statut = cursor.fetchone()[0]
		cursor.execute("SELECT `reduction`.`nom` FROM `reduction` WHERE `reduction`.`id` = "+str(reduction_id))
		client_reduction = cursor.fetchone()[0]
		
		# Récupération de la liste des réductions pour le template
		liste_reduction = get_liste_reduction()
		reduction = []
		for element in liste_reduction:
			reduction.append(Element(element, client_reduction == element))
	
		# Récupération de la liste des statuts pour le template
		liste_statut = get_liste_statut()
		statut = []
		for element in liste_statut:
			statut.append(Element(element, client_statut == element))
	
	
		dico = {
			'message':message,
			'nom':last_name,
			'prenom':first_name,
			'client_statut':client_statut,
			'client_reduction':client_reduction,
			'liste_statut':statut,
			'liste_reduction':reduction,
			'client_email':email,
			'onglet':Onglet(False,True,False),
		}
		return render(request, 'profil.html',dico)



def deconnexion(request):
	logout(request)
	return HttpResponseRedirect(reverse('connexion'))




def reservation(request):
	"""
	This method is called when all the bookings from a user
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'reservation.html',dico) 
			where 
		dico = {
			'liste_reservation' (list) A list of Reservation objects containing all the informations in order to create a reservation,
		}
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		######### Récupération du compte de l'utilisateur ###############
		cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%s')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
		session_data = cursor.fetchone()[0]
		message = ""
		user_id = request.session.decode(session_data)['_auth_user_id']
		#################################################################
		
		# Récupération de l'id du client
		cursor.execute("SELECT `client`.`id` FROM `client` WHERE `client`.`user_id` = "+str(user_id))
		client_id = cursor.fetchone()[0]
		
		cursor.execute("SELECT `billet`.`id`, `billet`.`gare_depart_id`, `billet`.`gare_arrivee_id`, `billet`.`place_id`, `billet`.`client_id`, `billet`.`confirmation_id`, `billet`.`agence_id`, `billet`.`prix`, `billet`.`reduction_id` FROM `billet` LEFT OUTER JOIN `gare_arret` ON (`billet`.`gare_depart_id` = `gare_arret`.`id`) WHERE `billet`.`client_id` = "+str(client_id)+" ORDER BY `gare_arret`.`heure` DESC")
		liste_billets_id = cursor.fetchall()
		
		liste_reservation = []
		for billet in liste_billets_id:
			billet_id, gare_depart_id, gare_arrivee_id, place_id, client_id, confirmation_id, agence_id, prix, reduction_id = billet
			cursor.execute("SELECT `place`.`situation_id`, `place`.`voiture_id`, `place`.`numero` FROM `place` WHERE `place`.`id` = "+str(place_id))
			situation_id, voiture_id, numero_place = cursor.fetchone()
			
			# Récupération de l'id du train et du numéro de la voiture
			cursor.execute("SELECT `voiture`.`train_id`,`voiture`.`numero` FROM `voiture` WHERE `voiture`.`id` = "+str(voiture_id))
			train_id,numero_voiture = cursor.fetchone()
			
			# Récupération de l'heure de départ et du nom de la gare de départ
			cursor.execute("SELECT `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_depart_id))
			gare_depart_id, heure_depart = cursor.fetchone()
			cursor.execute("SELECT `gare`.`nom` FROM `gare` WHERE `gare`.`id` = "+str(gare_depart_id))
			gare_depart_nom = cursor.fetchone()[0]
			
			# Récupération de l'heure d'arrivée et du nom de la gare d'arrivée
			cursor.execute("SELECT `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_arrivee_id))
			gare_arrivee_id, heure_arrivee = cursor.fetchone()
			cursor.execute("SELECT `gare`.`nom` FROM `gare` WHERE `gare`.`id` = "+str(gare_arrivee_id))
			gare_arrivee_nom = cursor.fetchone()[0]
			
			reservation = Reservation (
				train_id,
				gare_depart_nom,
				gare_arrivee_nom,
				heure_depart.strftime('%d/%m/%Y'),
				heure_arrivee.strftime('%d/%m/%Y'),
				heure_depart.strftime('%H:%M'),
				heure_arrivee.strftime('%H:%M'),
				100,
				numero_voiture,
				numero_place
			)
			liste_reservation.append(reservation)
		dico = {
			'liste_reservation':liste_reservation,
		}
		return render(request, 'reservation.html', dico)

def admin_interface(request):
	liste_gare = get_liste_gare()
	liste_agence = Agence.objects.values_list('nom', flat=True)
	liste_ville = get_liste_ville()
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
				'liste_ville':liste_ville,		
			}
			return render(request, 'admin.html', dico)
		else:
			train = Train.objects.create()
			gare_arret = []
			for i in range(len(liste_gare)):
				gare_arret.append(GareArret(gare = liste_gare[i], heure = datetimes[i], train = train, numero = i))
			GareArret.objects.bulk_create(gare_arret)
			liste_voitures = []
			for i in range(len(voitures)):
				liste_voitures.append(Voiture(train = train, numero = i+1))
			Voiture.objects.bulk_create(liste_voitures)
			liste_place = []
			for i,nb_place in enumerate(voitures):
				voiture = Voiture.objects.filter(train = train).filter(numero = i+1).get()
				for j in range(int(nb_place)):
					liste_place.append(Place(voiture = voiture,numero = j, situation_id = j%2+1))
			Place.objects.bulk_create(liste_place)
		
	print(request.POST)
	dico = {
		'message':message,
		'liste_gare':liste_gare,
		'liste_agence':liste_agence,
		'liste_ville':liste_ville,
		
	}
	return render(request, 'admin.html', dico)



def admin_recherche_billet(request):
	if request.method == 'POST':
		form = request.POST
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

def admin_creer_gare(request):
	message_3 = ''
	if request.method == 'POST':
		form = request.POST
		gare = form['gare']
		ville = form['ville']
		if Gare.objects.filter(nom = gare).exists():
			message_3 = 'Cette gare existe deja, sa ville a été mise à jour'
		else:
			if Ville.objects.filter(nom = ville).exists():
				ville_id = Ville.objects.filter(nom = ville).get().id
			else:
				ville_id = Ville.objects.create(nom = ville).id
			Gare.objects.create(nom = gare, ville_id = ville_id)
			message_3 = 'La gare a bien été créée'
	liste_gare = get_liste_gare()
	liste_agence = Agence.objects.values_list('nom', flat=True)
	liste_ville = get_liste_ville()
	dico = {
		'message_3':message_3,
		'liste_gare':liste_gare,
		'liste_ville':liste_ville,
		'liste_agence':liste_agence
	}
	return render(request, 'admin.html', dico)


def admin_paiement(request):
	liste_gare = get_liste_gare()
	liste_agence = get_liste_agence()
	liste_ville = get_liste_ville()
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
			'liste_agence':liste_agence,
			'liste_ville':liste_ville,
		
		}
		return render(request, 'admin.html', dico)
	dico = {
		'liste_gare':liste_gare,
		'liste_ville':liste_ville,
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
	

	
	
	
	



	
		
