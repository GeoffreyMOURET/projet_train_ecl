# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey has `on_delete` set to the desired behavior.
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from django.contrib.auth.models import User


class Agence(models.Model):
    nom = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'agence'


class Billet(models.Model):
    gare_depart = models.ForeignKey('GareArret', models.DO_NOTHING, blank=True, null=True,  related_name='gare_depart')
    gare_arrivee = models.ForeignKey('GareArret', models.DO_NOTHING, blank=True, null=True,  related_name='gare_arrivee')
    place = models.ForeignKey('Place', models.DO_NOTHING, blank=True, null=True)
    client = models.ForeignKey('Client', models.DO_NOTHING, blank=True, null=True)
    confirmation = models.ForeignKey('Confirmation', models.DO_NOTHING, blank=True, null=True)
    agence = models.ForeignKey('Agence', models.DO_NOTHING, blank=True, null=True)
    prix = models.FloatField(blank=True, null=True)
    reduction = models.ForeignKey('Reduction', models.DO_NOTHING, blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'billet'


class Client(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE,blank=True, null=True)
    reduction = models.ForeignKey('Reduction', models.DO_NOTHING, blank=True, null=True)
    statut = models.ForeignKey('Statut', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'client'


class Confirmation(models.Model):
    heure_fin = models.DateTimeField(blank=True, null=True)
    validation = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'confirmation'


class Gare(models.Model):
    nom = models.CharField(max_length=200, blank=True, null=True)
    ville = models.ForeignKey('Ville', models.DO_NOTHING, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'gare'

class GareArret(models.Model):
    numero = models.IntegerField(blank=True, null = True)
    train = models.ForeignKey('Train', models.DO_NOTHING, blank=True, null=True)
    gare = models.ForeignKey('Gare', models.DO_NOTHING, blank=True, null=True)
    heure = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        managed = True
        db_table = 'gare_arret'


class Place(models.Model):
    situation = models.ForeignKey('Situation', models.DO_NOTHING, blank=True, null=True)
    voiture = models.ForeignKey('Voiture', models.DO_NOTHING, blank=True, null=True)
    numero = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'place'


class Reduction(models.Model):
    nom = models.CharField(max_length=100, blank=True, null=True)
    pourcentage = models.FloatField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'reduction'


class Situation(models.Model):
    nom = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'situation'


class Statut(models.Model):
    nom = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'statut'


class Token(models.Model):
    valeur = models.CharField(max_length = 200, blank = True, null = True)
    date_fin = models.DateTimeField(blank = True, null=True)
class Train(models.Model):
    class Meta:
        managed = True
        db_table = 'train'


class Ville(models.Model):
    nom = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'ville'


class Voiture(models.Model):
    train = models.ForeignKey(Train, models.DO_NOTHING, blank=True, null=True)
    numero = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = True
        db_table = 'voiture'
