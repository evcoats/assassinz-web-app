from django.core.management.base import BaseCommand, CommandError
from db.models import  Player, Game, Kill, Mod, KillVideo
import traceback
from datetime import *
from django.contrib.auth.models import User
import random
import string


class Command(BaseCommand):
    def handle(self, *args, **options):
        for x in Game.objects.all():
            gameString = ""
            validString = False
            while validString == False:
                gameString = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                if (Game.objects.filter(gameString = gameString).count() == 0):
                    validString = True
            
            x.gameString = gameString
            x.save()

