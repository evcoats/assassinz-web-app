from django.contrib import admin
from .models import Profile, Player, Kill, Mod, Game, KillVideo, Team
# Register your models here.
admin.site.register(Profile)
admin.site.register(Player)
admin.site.register(Kill)
admin.site.register(Mod)
admin.site.register(Game)
admin.site.register(KillVideo)
admin.site.register(Team)
