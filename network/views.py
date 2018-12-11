from django.shortcuts import render as render_2
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, Http404, HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import connection
from django.db.models import Q
from django.contrib.auth.hashers import make_password #Hachage des mots de passe

from .models import *
from .getter import *
from datetime import datetime, timedelta


import random
import string


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

@connexion_requise
def rechercher_trajet(request):
	with connection.cursor() as cursor:
		message = ''
		gare_depart = ''
		gare_arrivee = ''
		date = ''
		if request.method == 'POST':
			# Récupération des informations concernant le profil de l'utilisateur
			cursor.execute("SELECT `auth_user`.`first_name`, `auth_user`.`last_name`, `auth_user`.`email` FROM `auth_user` WHERE `auth_user`.`id` = "+str(user_id))
			first_name, last_name, email = cursor.fetchone()
			cursor.execute("SELECT `client`.`statut_id`,`client`.`reduction_id` FROM `client` WHERE `client`.`user_id` = "+str(user_id))
			statut_id, reduction_id = cursor.fetchone()
			########
			
			form = request.POST
			gare_depart = form['gare_depart'].replace("\"","'")
			gare_arrivee = form['gare_arrivee'].replace("\"","'")
			gare_depart = form['gare_depart'].replace("\'","\\\'")
			gare_arrivee = form['gare_arrivee'].replace("\'","\\\'")
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
				liste_prix = []
				for train in liste_train_depart_id:
					train = train[0]
					cursor.execute("SELECT `gare_arret`.`numero` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_depart_id)+")")
					numero_depart = cursor.fetchone()[0]
					cursor.execute("SELECT `gare_arret`.`numero` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_arrivee_id)+")")
					numero_arrivee = cursor.fetchone()
					if numero_arrivee is not None:
						numero_arrivee = numero_arrivee[0]
						cursor.execute("SELECT prix FROM train WHERE id="+str(train))
						prix = cursor.fetchone()[0]
						if numero_depart < numero_arrivee:
							liste_train.append(train)
							liste_prix.append(prix)
				requete = Requete(gare_depart, gare_arrivee, date)
				liste_resultat = []
				for i,train in enumerate(liste_train):
					numero = train
					cursor.execute("SELECT `gare_arret`.`id`,`gare_arret`.`numero`,`gare_arret`.`heure` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_depart_id)+")")
					id_depart, numero_depart, heure_depart = cursor.fetchone()
					
					cursor.execute("SELECT `gare_arret`.`id`,`gare_arret`.`numero`,`gare_arret`.`heure` FROM `gare_arret` WHERE (`gare_arret`.`train_id` = "+str(train)+" AND `gare_arret`.`gare_id` = "+str(gare_arrivee_id)+")")
					id_arrivee, numero_arrivee,heure_arrivee = cursor.fetchone()
					
					cursor.execute("SELECT COUNT(`place`.`id`) FROM `place` INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) WHERE `voiture`.`train_id` = "+str(train))
					nb_place_total = cursor.fetchone()[0]
					cursor.execute("SELECT COUNT(`billet`.`id`) FROM `billet` INNER JOIN `place` ON (`billet`.`place_id` = `place`.`id`) INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) INNER JOIN `gare_arret` ON (`billet`.`gare_depart_id` = `gare_arret`.`id`) INNER JOIN `gare_arret` GA ON (`billet`.`gare_arrivee_id` = GA.`id`) WHERE (`voiture`.`train_id` = "+str(train)+" AND `gare_arret`.`numero` <= "+str(numero_arrivee-1)+" AND GA.`numero` >= "+str(numero_depart+1)+")")
					
					
					
					cursor.execute("SELECT `pourcentage` FROM `reduction` WHERE `id`="+str(reduction_id))
					pourcentage = cursor.fetchone()[0]
					
					nb_billet_reserve = cursor.fetchone()[0]
					nb_place = nb_place_total - nb_billet_reserve
					date_depart = heure_depart.strftime('%d/%m/%Y')
					date_arrivee = heure_arrivee.strftime('%d/%m/%Y')
					heure_depart = heure_depart.strftime('%H:%M')
					heure_arrivee = heure_arrivee.strftime('%H:%M')
					prix = liste_prix[i]*pourcentage
					liste_resultat.append(Resultat_train(
							numero,
							form['gare_depart'],
							form['gare_arrivee'],
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
				cursor.execute("INSERT INTO `token` (`valeur`, `date_fin`) VALUES ('"+token+"', '"+date_fin.strftime('%Y-%m-%d %H:%M:%S')+"')")
				dico = {
					'token':token,
					'gare_depart':form['gare_depart'],
					'gare_arrivee':form['gare_arrivee'],
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
		
		



class Reservation:
	def __init__(self,numero, gare_depart, gare_arrivee, date_depart, date_arrivee, heure_depart, heure_arrivee, prix, voiture, place, reference = ''):
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
		self.reference = reference

@connexion_requise
def reserver_billet(request):
	"""
	This method is called when the user wants to login or create a new account.
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'connexion.html',dico) 
			where 
		dico = {
			'reservation': A Reservation object which contains all the information about the reservation made by the user
		}
	"""
	with connection.cursor() as cursor:
		if request.method == 'POST':
			form = request.POST
			# On vérifie que le token existe déjà
			cursor.execute("SELECT COUNT(id) FROM `token` WHERE `token`.`valeur` = '"+form['token'].replace('\'','\\\'')+"' LIMIT 1")
			token_exists = cursor.fetchone()[0] == 1
			if not token_exists:
				liste_gare = get_liste_gare()
				return render(request, 'rechercher_billet.html', {'liste_gare':liste_gare, 'erreur':True, 'message':'Votre session de reservation a expirée'})
			cursor.execute("DELETE FROM `token` WHERE `token`.`valeur` = '"+form['token'].replace('\'','\\\'')+"'")
			train_id = form['train_id']
			cursor.execute("SELECT `train`.`prix` FROM `train` WHERE `id`="+str(train_id))
			prix = cursor.fetchone()[0]
			cursor.execute("SELECT `place`.`id` FROM `place` INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) LEFT OUTER JOIN `billet` ON (`place`.`id` = `billet`.`place_id`) WHERE (`voiture`.`train_id` = "+str(train_id)+" AND `billet`.`id` IS NULL) LIMIT 1")
			liste_place = cursor.fetchone()
			liste_place_exists = liste_place != None
			if not liste_place_exists:
				pass
			else:
				cursor.execute("SELECT `place`.`id` FROM `place` INNER JOIN `voiture` ON (`place`.`voiture_id` = `voiture`.`id`) LEFT OUTER JOIN `billet` ON (`place`.`id` = `billet`.`place_id`) INNER JOIN `situation` ON (`place`.`situation_id` = `situation`.`id`) WHERE (`voiture`.`train_id` = "+str(train_id)+" AND `billet`.`id` IS NULL AND `situation`.`nom` = '"+str(form['cote']).replace('\'','\\\'')+"') LIMIT 1")
				liste_place_cote = cursor.fetchone()
				if liste_place_cote != None:
					place_id = liste_place_cote[0]
				else:
					place_id = liste_place[0]
			gare_arret_depart_id = int(form['gare_arret_depart_id'])
			gare_arret_arrivee_id = int(form['gare_arret_arrivee_id'])
			
			######### Récupération du compte de l'utilisateur ###############
			cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
			session_data = cursor.fetchone()[0]
			user_id = request.session.decode(session_data)['_auth_user_id']
			#################################################################
		
			# Récupération de l'id du client
			cursor.execute("SELECT `client`.`id`,`client`.`reduction_id` FROM `client` WHERE `client`.`user_id` = "+str(user_id))
			client_id,reduction_id = cursor.fetchone()[0]
			
			# Création de la confirmation
			cursor.execute("INSERT INTO `confirmation` (`heure_fin`,`validation`) VALUES ('"+(datetime.now()+timedelta(days = 10, hours = 1, minutes = 0, seconds = 0)).strftime('%Y-%m-%d %H:%M:%S.%s')+"',0)")
			cursor.execute("SELECT LAST_INSERT_ID() FROM `confirmation`")
			confirmation_id = cursor.fetchone()[0]
			if reduction_id is None:
				reduction_id = 1
			cursor.execute("SELECT `pourcentage` FROM `reduction` WHERE `id`="+str(reduction_id))
			pourcentage = cursor.fetchone()[0]
			cursor.execute("INSERT INTO `billet` (`place_id`,`client_id`,`confirmation_id`,`gare_depart_id`,`gare_arrivee_id`,`prix`,`reduction_id`) VALUES ("+str(place_id)+","+str(client_id)+","+str(confirmation_id)+","+str(gare_arret_depart_id)+","+str(gare_arret_arrivee_id)+", "+str(round(prix*pourcentage,2))+","+reduction_id+")")
			cursor.execute("SELECT LAST_INSERT_ID() FROM `billet`")
			billet_id = cursor.fetchone()[0]
			
			cursor.execute("SELECT `place`.`situation_id`, `place`.`voiture_id`, `place`.`numero` FROM `place` WHERE `place`.`id` = "+str(place_id))
			situation_id, voiture_id, numero_place = cursor.fetchone()
			
			# Récupération de l'id du train et du numéro de la voiture
			cursor.execute("SELECT `voiture`.`train_id`,`voiture`.`numero` FROM `voiture` WHERE `voiture`.`id` = "+str(voiture_id))
			train_id,numero_voiture = cursor.fetchone()
			
			# Récupération de l'heure de départ et du nom de la gare de départ
			cursor.execute("SELECT `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_arret_depart_id))
			gare_depart_id, heure_depart = cursor.fetchone()
			cursor.execute("SELECT `gare`.`nom` FROM `gare` WHERE `gare`.`id` = "+str(gare_depart_id))
			gare_depart_nom = cursor.fetchone()[0]
			
			# Récupération de l'heure d'arrivée et du nom de la gare d'arrivée
			cursor.execute("SELECT `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_arret_arrivee_id))
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
				numero_place,
				billet_id
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
	with connection.cursor() as cursor:
		if request.method == 'POST':
			# Récupération du formulaire
			form = request.POST
			if form['type'] == 'connexion':
				logout(request)
				mail = form['mail'].replace('\'','\\\'')
				password = form['password']
				cursor.execute("SELECT `auth_user`.`password` FROM `auth_user` WHERE `auth_user`.`email` = '"+mail+"' LIMIT 1" )
				password_base = cursor.fetchone()
				
				if password_base == None:
					return render(request,'connexion.html', {'message' : 'Mot de passe incorrect ou utilisateur inexistant'})
				password_base = password_base[0]
				hasher = password_base.split('$')[0]
				salt = password_base.split('$')[2]
				password = make_password(password,salt,hasher)
				
				if password != password_base :
					return render(request,'connexion.html', {'message' : 'Mot de passe incorrect ou utilisateur inexistant'})
				cursor.execute("SELECT `auth_user`.`id` FROM `auth_user` WHERE `auth_user`.`email` = '"+mail+"' LIMIT 1" )
				user_id = cursor.fetchone()[0]
				login(request,User.objects.get(pk = user_id))
				
				if (request.GET!={}): #redirection si il manquait une authentification
					return HttpResponseRedirect(request.GET['next'])
				return HttpResponseRedirect(reverse('accueil'))
			elif form['type'] == 'creer':
				logout(request)
				mail = form['mail'].replace('\'','\\\'')
				password = form['password']
				first_name = form['prenom'].replace('\'','\\\'')
				last_name = form['nom'].replace('\'','\\\'')
				
				#On récupère l'id du statut entré par l'utilisateur
				cursor.execute("SELECT `statut`.`id` FROM `statut` WHERE `statut`.`nom` = '"+form["statut"]+"' LIMIT 1" )
				statut_id = cursor.fetchone()[0]
				
				# On récupère l'id de la réduction par défaut
				cursor.execute("SELECT `reduction`.`id` FROM `reduction` WHERE `reduction`.`nom` = 'Aucune' LIMIT 1" )
				reduction_id = cursor.fetchone()[0]
				
				# On vérifie que l'email n'existe déjà pas
				cursor.execute("SELECT COUNT(id) FROM `auth_user` WHERE `auth_user`.`username` = '"+mail+"' LIMIT 1")
				user_exists = cursor.fetchone()[0] == 1
				#... Et qu'un utilisateur ne possède pas déjà cet email...
				if user_exists:
					return render(request,'connexion.html', {'message' : 'Cet e-mail est déjà utilisé'})
				password = make_password(password,token_generator(12))
				
				cursor.execute("INSERT INTO `auth_user` (`username`,`first_name`,`last_name`,`email`,`password`,`is_superuser`,`is_staff`,`is_active`,`date_joined`) VALUES ('"+mail+"','"+first_name+"','"+last_name+"','"+mail+"','"+password+"',0,0,1,'"+datetime.now().strftime('%Y-%m-%d %H:%M:%S.%s')+"')")
				cursor.execute("SELECT LAST_INSERT_ID() FROM `auth_user`")
				user_id = cursor.fetchone()[0]

				cursor.execute("INSERT INTO `client` (`user_id`,`reduction_id`,`statut_id`) VALUES ("+str(user_id)+","+str(reduction_id)+","+str(statut_id)+")")
				
				login(request, User.objects.get(pk = user_id))
				return HttpResponseRedirect(reverse('accueil'))
		if (request.GET!={}): 
			if request.session.session_key == None:
				message = 'Vous devez vous connecter pour accéder à cette page'
			else:
				message = "Vous n'avez pas les droits d'accéder à cette page"
		else:
			message = ''
			
		onglet = Onglet(False,False,True)
		dico = {
			'onglet':onglet,
			'message':message
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

@connexion_requise
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
		cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
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
				cursor.execute("SELECT COUNT(id) FROM `auth_user` WHERE `auth_user`.`username` = '"+form['email']+"' LIMIT 1")
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
	"""
	This method is called when user wants to logout
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		HttpResponseRedirect(reverse('connexion'))
	"""
	logout(request)
	return HttpResponseRedirect(reverse('connexion'))



@connexion_requise
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
		cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
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
				numero_place,
				billet_id
			)
			liste_reservation.append(reservation)
		dico = {
			'liste_reservation':liste_reservation,
		}
		return render(request, 'reservation.html', dico)
@admin_requis
def admin_interface(request):
	"""
	This method is called to load the administrator interface
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'admin.html', dico)
			 
		dico = {
			'message': (str) an error message (default : '')
			'liste_gare': (list of str) The list of all train stations contained in the database
			'liste_agence': (list of str) The list of all agencies contained in the database
			'liste_ville': (list of str) The list of all cities contained in the database
		
		}
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		liste_gare = get_liste_gare()
		liste_agence = get_liste_agence()
		liste_ville = get_liste_ville()
		message = ''
		if request.method == 'POST':
			# On récupère les informations du formulaire
			form = request.POST
			gares = form.getlist('gares')
			liste_gare = []
			dates = form.getlist('dates')
			heures = form.getlist('heures')
			voitures = form.getlist('voitures')
			prix = form['prix']
			for gare in gares:
				# On regarde si la gare rentrée par l'utilisateur existe
				gare = gare.replace('\'','\\\'')
				cursor.execute("SELECT COUNT(id) FROM `gare` WHERE `gare`.`nom` = '"+gare+"' LIMIT 1")
				gare_exists = cursor.fetchone()[0] == 1
				# Si elle n'existe pas, on renvoit un message
				if not gare_exists:
					message = 'La gare "'+gare+'" n\'existe pas'
				else:
					# Sinon, on récupère son id
					cursor.execute("SELECT `gare`.`id`,`gare`.`nom` FROM `gare` WHERE `gare`.`nom` = '"+str(gare)+"'")
					gare_id = cursor.fetchone()[0]
					# Et on ajoute l'id à la liste des gares			
					liste_gare.append(gare_id)
			# On transforme les dates en format datetime
			datetimes = []
			for i in range(len(dates)):
				datetimes.append(datetime.strptime(dates[i]+' '+heures[i],'%Y-%m-%d %H:%M'))
			# On vérifie qu'elles sont bien dans l'ordre chronologique
			for i in range(len(datetimes)-1):
				if datetimes[i]>datetimes[i+1]:
					message = 'La liste des gares n\'a pas été rentrée dans l\'ordre chronologique' 
			# S'il y a eu une erreur, le traitement s'arrete là et on renvoit le message
			if message != '':
				return HttpResponseRedirect(reverse('admin_interface')+'?message='+message)
			# Sinon, les informations ont été rentrées correctement
			else:
				# On crée un nouveau train et on récupère son id
				cursor.execute("INSERT INTO train(id,prix) VALUES (DEFAULT,"+str(prix)+")")
				cursor.execute("SELECT LAST_INSERT_ID() FROM `train`")
				train_id = cursor.fetchone()[0]
				
				# On crée toutes les gare_arret du formulaire
				string_gare_arret = ''
				for i in range(len(liste_gare)):
					string_gare_arret+="("+str(liste_gare[i])+",'"+datetimes[i].strftime('%Y-%m-%d %H:%M:%S')+"',"+str(train_id)+","+str(i)+"),"
				string_gare_arret = string_gare_arret[:-1]
				cursor.execute("INSERT INTO `gare_arret` (`gare_id`, `heure`, `train_id`, `numero`) VALUES " +string_gare_arret)
				
				# On crée toutes les voitures du formulaire
				string_liste_voitures = ''
				for i in range(len(voitures)):
					string_liste_voitures += "("+str(train_id)+","+str(i+1)+"),"
				string_liste_voitures = string_liste_voitures[:-1]
				cursor.execute("INSERT INTO `voiture` (`train_id`, `numero`) VALUES "+string_liste_voitures)
				
				# On crée toutes les places du formulaire
				string_liste_place = ''
				for i,nb_place in enumerate(voitures):
					cursor.execute("SELECT `voiture`.`id` FROM `voiture` WHERE (`voiture`.`train_id` = "+str(train_id)+" AND `voiture`.`numero` = "+str(i+1)+")")
					voiture_id = cursor.fetchone()[0]
					for j in range(int(nb_place)):
						string_liste_place += "("+str(voiture_id)+","+str(j)+","+str(j%2+1)+"),"
				string_liste_place = string_liste_place[:-1]
				cursor.execute("INSERT INTO `place` (`voiture_id`, `numero`, `situation_id`) VALUES "+string_liste_place)
				message = 'Le train a bien été créé'
				return HttpResponseRedirect(reverse('admin_interface')+'?message='+message)
		dico = {
			'liste_gare':liste_gare,
			'liste_agence':liste_agence,
			'liste_ville':liste_ville,
		
		}
		if (request.GET!={}): #redirection si il manquait une authentification
			nom_message = request.GET.keys()
			for i in nom_message:
				dico[i] = request.GET[i]
			
		# On renvoit la page avec le cas échéant un message
		
		return render(request, 'admin.html', dico)


@admin_requis
def admin_recherche_billet(request):
	"""
	This method is called in order to search in the database the corresponding train reservation to display it for the administrator
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		JsonResponse(dico)
			 
		dico = {
				'numero_billet' : (int) The id of the ticket
				'numero' : (int) The id of the train
				'gare_depart' : (str) The name of the departure station,
				'gare_arrivee' : (str) The name of the arrival station,
				'date_depart' : (str) The date of the departure,
				'date_arrivee' : (str) The date of the arrival,
				'heure_depart' : (str) The time of the departure,
				'heure_arrivee' : (str) The time of the arrival,
				'prix' : (float) The price of the ticket,
				'reduction': (str) The name of the reduction,
				'voiture' : (int) The car number,
				'place' : (int) The place number,
				'payee' : (int) Values 1 if the ticket was paid,
				'agence' : (str) The name of the agency,
			}
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		if request.method == 'POST':
			#On récupère le numéro du billet du formulaire
			form = request.POST
			numero = int(form['numero_billet'])
			# On regarde si le billet existe
			cursor.execute("SELECT COUNT(id) FROM `billet` WHERE `billet`.`id` = "+str(numero))
			billet_exists = cursor.fetchone()[0] == 1
			if not billet_exists:
				return JsonResponse({'message':'Le billet indiqué n\'existe pas'}, status = 500)
			cursor.execute("SELECT COUNT(id) FROM `agence` WHERE `agence`.`nom` = '"+form['agence'].replace('\'','\\\'')+"'")
			agence_exists = cursor.fetchone()[0] == 1
			if not agence_exists:
				return JsonResponse({'message':'L\'agence indiquée n\'existe pas'}, status = 500)
			cursor.execute("SELECT `billet`.`gare_depart_id`, `billet`.`gare_arrivee_id`, `billet`.`place_id`, `billet`.`client_id`, `billet`.`confirmation_id`, `billet`.`agence_id`, `billet`.`prix`, `billet`.`reduction_id` FROM `billet` WHERE `billet`.`id` = "+str(numero))
			gare_depart_id, gare_arrivee_id, place_id, client_id, confirmation_id, agence_id, prix, reduction_id = cursor.fetchone()
			
			cursor.execute("SELECT `place`.`situation_id`, `place`.`voiture_id`, `place`.`numero` FROM `place` WHERE `place`.`id` = "+str(place_id))
			situation_id, voiture_id, numero_place = cursor.fetchone()
			
			cursor.execute("SELECT `voiture`.`train_id`, `voiture`.`numero` FROM `voiture` WHERE `voiture`.`id` = "+str(voiture_id))
			train_id, numero_voiture = cursor.fetchone()
			
			cursor.execute("SELECT `gare_arret`.`numero`, `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_depart_id))
			numero_depart, gare_id_depart, heure_depart = cursor.fetchone()
			
			cursor.execute("SELECT `gare_arret`.`numero`, `gare_arret`.`gare_id`, `gare_arret`.`heure` FROM `gare_arret` WHERE `gare_arret`.`id` = "+str(gare_arrivee_id))
			numero_arrivee, gare_id_arrivee, heure_arrivee = cursor.fetchone()
			
			cursor.execute("SELECT `gare`.`nom` FROM `gare` WHERE `gare`.`id` = "+str(gare_id_depart))
			nom_gare_depart = cursor.fetchone()[0]
			
			cursor.execute("SELECT `gare`.`nom` FROM `gare` WHERE `gare`.`id` = "+str(gare_id_arrivee))
			nom_gare_arrivee = cursor.fetchone()[0]
			
			# Si jamais la réduction n'a pas été définie à l'achat, on prend la réduction par défaut
			if reduction_id == None:
				cursor.execute("UPDATE `billet` SET `reduction_id` = 1 WHERE `billet`.`id` = "+str(numero))
				reduction_id = 1
			cursor.execute("SELECT `reduction`.`nom` FROM `reduction` WHERE `reduction`.`id` = "+str(reduction_id))
			nom_reduction = cursor.fetchone()[0]
						
			if confirmation_id == None:
				validation = 0
			else:
				cursor.execute("SELECT `confirmation`.`validation` FROM `confirmation` WHERE `confirmation`.`id` = "+str(confirmation_id))
				validation = cursor.fetchone()[0]
			dico = {
				'numero_billet' : numero,
				'numero' : train_id,
				'gare_depart' : nom_gare_depart,
				'gare_arrivee' : nom_gare_arrivee,
				'date_depart' : heure_depart.strftime('%d/%m/%Y'),
				'date_arrivee' : heure_arrivee.strftime('%d/%m/%Y'),
				'heure_depart' : heure_depart.strftime('%H:%M'),
				'heure_arrivee' : heure_arrivee.strftime('%H:%M'),
				'prix' : prix,
				'reduction': nom_reduction,
				'voiture' : numero_voiture,
				'place' : numero_place,
				'payee' : validation,
				'agence' : form['agence'],
			}
			for k in connection.queries:
				file = open('requete.sql','a')
				file.write(k['sql']+'\n')
				file.close()
			return JsonResponse(dico)

@admin_requis
def admin_creer_gare(request):
	"""
	This method is called when a form in order to create a train station and city is called
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		render(request, 'admin.html',dico) 
			where 
		dico = {
			'message_3': (str) A message to display for the user
			'liste_gare': (list of str) The list of all the train stations in the database
			'liste_ville': (list of str) The list of all the city in the database
			'liste_agence': (list of str) The list of all the agency in the database
		}
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		message_3 = ''
		if request.method == 'POST':
			form = request.POST
			gare = form['gare']
			ville = form['ville']
			# On regarde si la gare rentrée par l'utilisateur existe
			gare = gare.replace('\'','\\\'')
			cursor.execute("SELECT COUNT(id) FROM `gare` WHERE `gare`.`nom` = '"+gare+"' LIMIT 1")
			gare_exists = cursor.fetchone()[0] == 1
			if gare_exists:
				message_3 = 'Cette gare existe deja, sa ville a été mise à jour'
			else:
				# On regarde si la ville rentrée par l'utilisateur existe
				ville = ville.replace('\'','\\\'')
				cursor.execute("SELECT COUNT(id) FROM `ville` WHERE `ville`.`nom` = '"+ville+"' LIMIT 1")
				ville_exists = cursor.fetchone()[0] == 1
				if ville_exists:
					# On récupère son id
					cursor.execute("SELECT `ville`.`id` FROM `ville` WHERE `ville`.`nom` = '"+ville+"' LIMIT 1")
					ville_id = cursor.fetchone()[0]
				else:
					# On la crée la ville si elle n'existe pas
					cursor.execute("INSERT INTO `ville` (`nom`) VALUES ('"+ville+"')")
					# On récupère son id
					cursor.execute("SELECT LAST_INSERT_ID() FROM `ville`")
					ville_id = cursor.fetchone()[0]
				cursor.execute("INSERT INTO `gare` (`nom`,`ville_id`) VALUES ('"+gare+"',"+str(ville_id)+")")
				message_3 = 'La gare a bien été créée'
				return HttpResponseRedirect(reverse('admin_interface')+'?message_3='+message_3)
		return HttpResponseRedirect(reverse('admin_interface'))

@admin_requis
def admin_paiement(request):
	"""
	This method is called when a form in order to create a train station and city is called
	
	Parameters : 
		- request : Django requires it. Contains all the data about the HTTP Request done.
	---------
	Return :
		HttpResponseRedirect(reverse('admin_interface'))
	"""
	with connection.cursor() as cursor: #Connexion a la base de donnees
		liste_gare = get_liste_gare()
		liste_agence = get_liste_agence()
		liste_ville = get_liste_ville()
		if request.method == 'POST':
			form = request.POST
			numero = form['numero']
			cursor.execute("SELECT `billet`.`confirmation_id` FROM `billet` WHERE `billet`.`id` ="+str(numero)+" LIMIT 1")
			confirmation_id = cursor.fetchone()[0]
			# Si jamais l'objet confirmation n'a pas déjà été créén on le crée
			if confirmation_id == None:
				cursor.execute("INSERT INTO `confirmation` (`heure_fin`,`validation`) VALUES ( NULL,1)")
				# On récupère son id
				cursor.execute("SELECT LAST_INSERT_ID() FROM `confirmation`")
				confirmation_id = cursor.fetchone()[0]
				cursor.execute("UPDATE `billet` SET `confirmation_id` = "+str(confirmation_id)+" WHERE `billet`.`id` = "+str(numero))
				
			else:
				cursor.execute("UPDATE `confirmation` SET `validation` = 1 WHERE `confirmation`.`id` = "+str(confirmation_id))
			message_2 = "Le paiement a bien été effectué"
			return HttpResponseRedirect(reverse('admin_interface')+'?message_2='+message_2)
		return HttpResponseRedirect(reverse('admin_interface'))


@admin_requis
def admin_gestion(request):
	message_5 = ''
	message_6 = ''
	with connection.cursor() as cursor: #Connexion a la base de donnees
		if request.method == 'POST':
			form = request.POST
			mail = form['mail'].replace("\"","'")
			cursor.execute("SELECT `id` FROM `auth_user` WHERE `auth_user`.`email` = '"+mail+"' LIMIT 1" )
			mail_exists = cursor.fetchone()
			if form['type']=='retirer':
				if mail_exists == None:
					message_6 = 'Le mail entré n\'existe pas'
					return HttpResponseRedirect(reverse('admin_interface')+'?message_6='+message_6)
				else:
					user_id = mail_exists[0]
					cursor.execute("UPDATE `auth_user` SET `is_superuser` = 0 WHERE `auth_user`.`id` = "+str(user_id))
					message_6 = 'Le mail entré a été retiré des administrateurs'
					return HttpResponseRedirect(reverse('admin_interface')+'?message_6='+message_6)
			if form['type']=='ajouter':
				if mail_exists == None:
					message_5 = 'Le mail entré n\'existe pas'
					return HttpResponseRedirect(reverse('admin_interface')+'?message_5='+message_5)
				else:
					user_id = mail_exists[0]
					cursor.execute("UPDATE `auth_user` SET `is_superuser` = 1 WHERE `auth_user`.`id` = "+str(user_id))	
					message_5 = 'Le mail entré a été ajouté des administrateurs'	
					return HttpResponseRedirect(reverse('admin_interface')+'?message_5='+message_5)
		return HttpResponseRedirect(reverse('admin_interface'))		
		
		
		

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
		liste_train = [Train.objects.get(pk = i, prix = 100) for i in range(1,10)]
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
	

	
	
	
	



	
		
