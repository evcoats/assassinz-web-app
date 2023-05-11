from django.core.management.base import BaseCommand, CommandError
from db.models import Player, Game, Kill, Mod, KillVideo
import traceback


class Command(BaseCommand):
    def handle(self, *args, **options):
        # User.objects.all().delete()
        Player.objects.all().delete()
        Game.objects.all().delete()
        Kill.objects.all().delete()
        Mod.objects.all().delete()
        KillVideo.objects.all().delete()
