from django.db import models
from decimal import *
from django.utils import timezone
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

class Profile(models.Model):
    userID = models.IntegerField(default=0)
    KD = models.DecimalField(max_digits=20,decimal_places=2, default=Decimal(0.00))
    games = models.IntegerField(default=0)
    wins = models.IntegerField(default=0)
    mods = models.IntegerField(default=0)
    public = models.BooleanField(default=True)
    kills = models.IntegerField(default=0)
    fullName = models.CharField(max_length=100,blank= True,null = True)
    coins = models.IntegerField(default=0)


class Player(models.Model):
    userID =  models.IntegerField(default=0)
    gameID = models.IntegerField(default=0)
    kills = models.IntegerField(default=0)
    score = models.IntegerField(default=0)
    targetID = models.IntegerField(default=0, null = True, blank = True)
    alive = models.BooleanField(default = True)
    killConfirmed = models.BooleanField(default = False)
    deathConfirmed = models.BooleanField(default = False)
    killedBy = models.IntegerField(null = True, blank = True)
    teamID = models.IntegerField(null = True, blank = True)
    extraInfo = models.CharField(max_length=100,blank= True,null = True)


    @property
    def my_field(self):
        u = User.objects.get()

        return []

class Kill(models.Model):
    killerID =  models.IntegerField(default=0)
    killedID =  models.IntegerField(default=0)
    gameID = models.IntegerField(default=0)
    timeKilled = models.DateTimeField('time killed')

class Mod(models.Model):
    gameID = models.IntegerField(default=0)
    userID = models.IntegerField(default=0)

class Game(models.Model):
    WitnessProtection = models.BooleanField(null = True,blank= True)
    Safety = models.BooleanField(null = True, default = False)
    SafetyCircumstances = models.CharField(max_length=500,blank= True,null = True)
    KillMethod = models.CharField(max_length=10000,blank= True,null = True)
    ExtraRules = models.CharField(max_length=500,blank= True,null = True)
    TimeCreated = models.DateTimeField('time')
    TimeStart = models.DateTimeField('time',null = True,blank= True)
    TimeEnd = models.DateTimeField('time',null = True,blank= True)
    phase =  models.IntegerField(default=0)
    otherContactInfo = models.CharField(max_length=500,blank= True,null = True)
    email = models.BooleanField(default=True)
    phone =  models.CharField(max_length=20,blank= True,null = True)
    killCam = models.BooleanField(default=True)
    compilationDone = models.BooleanField(default=False)
    limit = models.IntegerField(default=0)
    teams = models.IntegerField(default=1)
    randomTeams = models.BooleanField(default=False)
    ExtraUserInfoString = models.CharField(max_length=100,blank= True,null = True)
    gameName = models.CharField(max_length=50,blank= True,null = True)
    gameString = models.CharField(max_length=15,blank= True,null = True)


    def __str__(self):
        return '%s' % (self.id)

class KillVideo(models.Model):
    killID = models.IntegerField(blank= True,null = True)
    killConf = models.BooleanField(default=False)
    killerID =  models.IntegerField(default=0)
    killedID =  models.IntegerField(default=0)
    gameID = models.IntegerField(default=0)
    usable = models.BooleanField(default=True)

class Team(models.Model):
    gameID = models.IntegerField(default=0)
    targetID = models.IntegerField(default=0)
    alive = models.BooleanField(default=True)
    name = models.CharField(max_length=20,blank= True,null = True)

class Proposal(models.Model):
    gameID = models.IntegerField(default=0)
    name = models.CharField(max_length=20,blank= True,null = True)
    approvedForVoting = models.BooleanField(default=False)
    desc = models.IntegerField(default=0)
    votesFor = models.IntegerField(default=0)
    votesAgainst = models.IntegerField(default=0)
    timeCreated = models.DateTimeField('time')
    timeEnding = models.DateTimeField('time')






# Create your models here.
