from django.db import connection
import random
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
