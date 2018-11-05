from django.db import connection
from django.http import HttpResponseRedirect
from django.urls import reverse
import random
from datetime import datetime, timedelta
import string

############################################################################################################
### This file contains functions which aims to get list from the database or the function uned to create ###
########################################## a token #########################################################
############################################################################################################

def get_liste_gare():
	"""
	A getter to get all the train stations contained inside the database
	
	Parameters : 
		None
	Return :
		liste_gare (list of str) The list of train station contained inside the database
	"""
	with connection.cursor() as cursor:
		cursor.execute("SELECT `gare`.`nom` FROM `gare`")
		liste_tuple = cursor.fetchall()
		liste_gare = []
		for k in liste_tuple:
			liste_gare.append(k[0])
		return liste_gare

def get_liste_statut():
	"""
	A getter to get all the status contained inside the database
	
	Parameters : 
		None
	Return :
		liste_statut (list of str) The list of status contained inside the database
	"""
	with connection.cursor() as cursor:
		cursor.execute("SELECT `statut`.`nom` FROM `statut`")
		liste_tuple = cursor.fetchall()
		liste_statut = []
		for k in liste_tuple:
			liste_statut.append(k[0])
		return liste_statut

def get_liste_ville():
	"""
	A getter to get all the cities contained inside the database
	
	Parameters : 
		None
	Return :
		liste_statut (list of str) The list of cities contained inside the database
	"""
	with connection.cursor() as cursor:
		cursor.execute("SELECT `ville`.`nom` FROM `ville`")
		liste_tuple = cursor.fetchall()
		liste_ville = []
		for k in liste_tuple:
			liste_ville.append(k[0])
		return liste_ville

def get_liste_reduction():
	"""
	A getter to get all the reductions contained inside the database
	
	Parameters : 
		None
	Return :
		liste_statut (list of str) The list of reductions contained inside the database
	"""
	with connection.cursor() as cursor:
		cursor.execute("SELECT `reduction`.`nom` FROM `reduction`")
		liste_tuple = cursor.fetchall()
		liste_reduction = []
		for k in liste_tuple:
			liste_reduction.append(k[0])
		return liste_reduction

def get_liste_agence():
	"""
	A getter to get all the agencies contained inside the database
	
	Parameters : 
		None
	Return :
		liste_statut (list of str) The list of agencies contained inside the database
	"""
	with connection.cursor() as cursor:
		cursor.execute("SELECT `agence`.`nom` FROM `agence`")
		liste_tuple = cursor.fetchall()
		liste_agence = []
		for k in liste_tuple:
			liste_agence.append(k[0])
		return liste_agence


def token_generator(size=200, chars=string.ascii_lowercase + string.ascii_uppercase + string.digits):
	"""
	A token generator
	
	Parameters : 
		None
	Return :
		A str of 200 length
	"""
	return ''.join(random.choice(chars) for _ in range(size))


def connexion_requise(function):
	"""
	Decorator used to add the login permission
	"""
	def decorator(*args, **kwargs):
		with connection.cursor() as cursor:
			######### Récupération du compte de l'utilisateur ###############
			request = args[0]
			if request.session.session_key == None:
				return HttpResponseRedirect(reverse('connexion')+'?next='+request.get_full_path())
			cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
			session_data = cursor.fetchone()
			if session_data is not None:
				function(*args, **kwargs)
			else:
				return HttpResponseRedirect(reverse('connexion')+'?next='+request.get_full_path())
	return decorator


def admin_requis(function):
	"""
	Decorator used to add the admin permission
	"""
	def decorator(*args, **kwargs):
		with connection.cursor() as cursor:
			request = args[0]
			if request.session.session_key == None:
				return HttpResponseRedirect(reverse('connexion')+'?next='+request.get_full_path())
			cursor.execute("SELECT `django_session`.`session_data` FROM `django_session` WHERE (`django_session`.`expire_date` > '"+datetime.now().strftime('%Y-%m-%d %H:%M:%S')+"' AND `django_session`.`session_key` = '"+request.session.session_key+"')")
			session_data = cursor.fetchone()
			if session_data is not None:
				user_id = request.session.decode(session_data)['_auth_user_id']
				cursor.execute("SELECT `auth_user`.`is_superuser` FROM `auth_user` WHERE `auth_user`.`id` = "+str(user_id))
				is_superuser = cursor.fetchone()[0] == 1
				if is_superuser:
					function(*args, **kwargs)
				else:
					return HttpResponseRedirect(reverse('connexion')+'?next='+request.get_full_path())
				
			else:
				return HttpResponseRedirect(reverse('connexion')+'?next='+request.get_full_path())
	return decorator
