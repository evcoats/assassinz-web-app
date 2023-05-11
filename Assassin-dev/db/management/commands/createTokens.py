from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
import os
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        for user in User.objects.all():
            Token.objects.get_or_create(user=user)
