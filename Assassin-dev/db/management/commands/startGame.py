from django.core.management.base import BaseCommand, CommandError
from db.models import  Player, Game, Kill, Mod, KillVideo
import traceback
from datetime import *
from django.contrib.auth.models import User


class Command(BaseCommand):
    def handle(self, *args, **options):
        g = Game(WitnessProtection = True,Safety = True, SafetyCircumstances = "safetyC", KillMethod = "killMethod", ExtraRules = "extraRules", TimeCreated = datetime.now(),otherContactInfo = "other", email = True, phone="phone", killCam = True, teams = 1)
        g.save()
        mod = Mod(gameID = g.id, userID = User.objects.get(username = "evan").id)
        mod.save()
        p = Player(userID = User.objects.get(username = "6").id,gameID = g.id, alive = True)
        p.save()
        p = Player(userID = User.objects.get(username = "5").id,gameID = g.id, alive = True)
        p.save()
        p = Player(userID = User.objects.get(username = "4").id,gameID = g.id, alive = True)
        p.save()
        p = Player(userID = User.objects.get(username = "2").id,gameID = g.id, alive = True)
        p.save()
        p = Player(userID = User.objects.get(username = "3").id,gameID = g.id, alive = True)
        p.save()
        p = Player(userID = User.objects.get(username = "1").id,gameID = g.id, alive = True)
        p.save()
