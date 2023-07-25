from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader
from django.urls import reverse
from .models import Game, Player, Mod, Kill, KillVideo, Profile, Team
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
import traceback, stripe, boto3
from datetime import *
import numpy as np
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .forms import VideoForm
from django.contrib.staticfiles.storage import staticfiles_storage
from django.conf import settings
import ffmpeg
import os
import random
from rest_framework.authtoken.models import Token
import string

from . import basic_views
from . import game_views
from . import views_functions
from . import game_functions

from . import rest_api


def getProfile(userID):
    try:
        return Profile.objects.get(userID = userID)
    except:
        return None

def userGames(userID):
    try:
        players = Player.objects.filter(userID = userID)
        mods = Mod.objects.filter(userID = userID)
        games = []

        for x in players:
            games.append(Game.objects.get(id = x.gameID).id)
        for x in mods:
            games.append(Game.objects.get(id = x.gameID).id)
        #sorting by date

        for x in range(len(games)):
            newArr = games[x:]
            y = np.argmax(newArr)
            placeholder = games[x]
            games[x] = newArr[y]
            games[x+y] = placeholder
        return games
    except Exception:
        print(traceback.print_exc())
        return []

def index(request):
    # createCompilation(36

    if views_functions.signedIn(request):
        try:
             gameID = request.session['autoJoinGameID']
             return game_views.joinGamePost(request)
        except:
            pass
        try:
             getToken = request.session['getToken']
             return HttpResponseRedirect(reverse('getToken'))        
        except:
            pass

        games = userGames(request.session['user'])
        newgames = []
        for x in games:
            playerCount = len(Player.objects.filter(gameID = x))
            killCount = 0
            try:
                killCount = len(Kill.objects.filter(gameID = x))
            except:
                pass

            newgames.append([x,views_functions.convertTo64(x),Game.objects.get(id=x).phase,playerCount,killCount,playerCount-killCount,Game.objects.get(id=x).gameString,Game.objects.get(id=x).gameName])

        template = loader.get_template('db/home.html')
        info = {'games':newgames, 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        return HttpResponse(template.render(info,request))

    try:
        getToken = request.session['getToken']
        template = loader.get_template('db/index.html')

        none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'getToken':True}
        return HttpResponse(template.render(none,request))
    except:
        try:
            gameID = request.session['autoJoinGameID']
            modName = User.objects.get(id = Mod.objects.get(gameID=gameID).userID).username
            template = loader.get_template('db/index.html')
            none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'gameID':gameID,'modName':modName}
            return HttpResponse(template.render(none,request))
        except:
            print(traceback.print_exc())
            template = loader.get_template('db/index.html')
            none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
            return HttpResponse(template.render(none,request))

def login(request):
    try:
        request.session['signedIn']
        return HttpResponseRedirect(reverse('index'))
    except:
        template = loader.get_template('db/login.html')
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        try:
            info = {'error_message':request.session['error_message'],'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))

def signup(request):
    try:
        request.session['signedIn']
        return HttpResponseRedirect(reverse('index'))
    except:
        template = loader.get_template('db/signup.html')
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        try:
            info = {'error_message':request.session['error_message']}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))

def home(request):
    return HttpResponseRedirect(reverse('index'))

def faq(request):
    template = loader.get_template('db/general-rules.html')
    none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
    return HttpResponse(template.render(none,request))

def intro(request):
    template = loader.get_template('db/introduction.html')
    none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
    return HttpResponse(template.render(none,request))


def signOut(request):
    try:
        del request.session['user']
        del request.session['signedIn']
    except:
        pass
    return HttpResponseRedirect(reverse('index'))


def signUpPost(request):
    # try:
    # if request.POST['termsconditions']=='termsconditions':
    username = request.POST['username']
    email = request.POST['email']
    password = request.POST['password']
    fullName = request.POST['fullName']

    if request.POST['repeatpassword']== password:
        try:
            User.objects.get(username=username)
            request.session['error_message'] = "Username already exists"
            return HttpResponseRedirect(reverse('signup'))
        except:
            try:
                User.objects.get(email=email)
                request.session['error_message'] = "Email already exists"
                return HttpResponseRedirect(reverse('signup'))
            except:
                try:
                    request.POST['termsconditions']=='termsconditions'
                    try:
                        # subject = 'Welcome to Assassin Live!'
                        # html_message = render_to_string('mail/welcome.html', {'user': username})
                        # plain_message = strip_tags(html_message)
                        # send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[email], html_message = html_message, fail_silently=False)
                        user = User.objects.create_user(username, email, password)
                        user.save()
                        Token.objects.get_or_create(user=user)
                        request.session['user'] = user.id
                        request.session['signedIn'] = True
                        p = Profile(userID = user.id, fullName = fullName)
                        p.save()

                        return HttpResponseRedirect(reverse('index'))
                    except:
                        print(traceback.print_exc())
                        request.session['error_message'] = "Email is invalid"
                        return HttpResponseRedirect(reverse('signup'))
                except:
                    request.session['error_message'] = "You must agree to the terms and conditions to sign up"
                    return HttpResponseRedirect(reverse('signup'))

    else:
        request.session['error_message'] = "Your passwords don't match."
        return HttpResponseRedirect(reverse('signup'))

def loginPost(request):
    try:
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(username=username, password=password)
        if user is not None:
            request.session['user'] = user.id
            request.session['signedIn'] = True
            return HttpResponseRedirect(reverse('index'))
        else:
            print(traceback.print_exc())
            request.session['error_message'] = "Your username or password is incorrect."
            print("here")
            return HttpResponseRedirect(reverse('login'))
    except:
        print(traceback.print_exc())
        request.session['error_message'] = "Your username or password is incorrect."
        return HttpResponseRedirect(reverse('login'))

def termsConditions(request):
    info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
    template = loader.get_template('db/termsConditions.html')
    return HttpResponse(template.render(info,request))


def profile(request, userID):
    try:
        prof = Profile.objects.get(userID = userID)
        user = User.objects.get(id = userID)
        if prof.public:
            template = loader.get_template('db/profile.html')
            games = []

            try:
                g = userGames(userID)
                newgames = []
                for x in g:
                    playerCount = len(Player.objects.filter(gameID = x))
                    killCount = 0
                    try:
                        killCount = len(Kill.objects.filter(gameID = x))
                    except:
                        print(traceback.print_exc())
                    newgames.append([x,views_functions.convertTo64(x),Game.objects.get(id=x).phase,playerCount,killCount,playerCount-killCount])
                    games = newgames
            except Exception:
                print(traceback.print_exc())

            info = {'username':user.username,'KD': prof.KD, 'gamecount':prof.games, 'mods':prof.mods, 'wins':prof.wins, 'id':userID, 'games':games,'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}

            return HttpResponse(template.render(info,request))
        else:
            template = loader.get_template('db/userNotFound.html')
            info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
            return HttpResponse(template.render(info,request))
    except:
        template = loader.get_template('db/userNotFound.html')
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        return HttpResponse(template.render(info,request))

def userSettings(request):
    if views_functions.signedIn(request):
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
            del request.session['error_message']
        except:
            pass
        template = loader.get_template('db/user-settings.html')
        return HttpResponse(template.render(info,request))

    return HttpResponseRedirect(reverse('login'))

def userSettingsPost(request):
    if views_functions.signedIn(request):
        user = User.objects.get(id = request.session['user'])
        changes = []
        try:
            if request.POST['public'] == "yes":
                user.public = True
                changes.append("profile publicity")

            if request.POST['public'] == "no":
                user.public = False
        except:
            pass
        if request.POST['newpassword'] != "":
            user.password = request.POST['newpassword']
            changes.append("password")

        if request.POST['newemail'] != "":
            email = request.POST['newemail']
            changes.append("email")

            try:
                User.objects.get(email=email)
                request.session['error_message'] = "Email already in use"
                return HttpResponseRedirect(reverse('userSettings'))

            except:
                user.email = email

        if request.POST['newuser'] != "":
            username = request.POST['newuser']
            changes.append("username")

            try:
                User.objects.get(username = username)
                request.session['error_message'] = "Username already in use"
                return HttpResponseRedirect(reverse('userSettings'))
            except:
                user.username = request.POST['newuser']

        try:
            subject = 'Your Assassin Live settings changed'
            html_message = render_to_string('mail/settingsChanged.html', {'changes':changes,'user': user.username})
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[user.email], html_message = html_message, fail_silently=False)
            user.save()
            HttpResponseRedirect(reverse('index'))
        except:
            request.session['error_message'] = "Email is invalid"
            return HttpResponseRedirect(reverse('userSettings'))

    return HttpResponseRedirect(reverse('login'))



def getPassword(request):

    try:
        error_message = request.session['error_message']
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'error_message':error_message}
        del request.session['error_message']
    except:
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
    template = loader.get_template('db/getPassword.html')
    return HttpResponse(template.render(info,request))

def getPasswordPost(request):
    template = loader.get_template('db/getPassword.html')
    try:
        u = User.objects.get(username = request.POST['username'], email = request.POST['email'])
        subject = 'Help request'
        html_message = render_to_string('mail/password.html', {'password': u.password})
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[u.email], html_message = html_message, fail_silently=False)
        request.session['error_message'] = "Check your email"
        return HttpResponseRedirect(reverse('getPassword'))
    except:
        request.session['error_message'] = "Username / email combination is invalid"
        return HttpResponseRedirect(reverse('getPassword'))
