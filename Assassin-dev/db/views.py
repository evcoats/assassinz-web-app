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



def convertTo64(num):
    newnum = str(np.int64(num))
    zeros = 8-len(newnum)
    for x in range(zeros):
        newnum = "0"+newnum

    return newnum

def convertFrom64(num):
    cont = True
    while(cont):
        if num[0] == "0":
            num = num[1:]
        else:
            cont = False

    return int(np.int64(num))

def signedIn(request):
    try:
        name = request.session['signedIn']
        return True
    except Exception:
        return False

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

    if signedIn(request):
        try:
             gameID = request.session['autoJoinGameID']
             return joinGamePost(request)
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

            newgames.append([x,convertTo64(x),Game.objects.get(id=x).phase,playerCount,killCount,playerCount-killCount,Game.objects.get(id=x).gameString])

        template = loader.get_template('db/home.html')
        info = {'games':newgames, 'signedIn':signedIn(request), 'user':getUser(request)}
        return HttpResponse(template.render(info,request))

    try:
        getToken = request.session['getToken']
        template = loader.get_template('db/index.html')

        none = {'signedIn':signedIn(request), 'user':getUser(request),'getToken':True}
        return HttpResponse(template.render(none,request))
    except:
        try:
            gameID = request.session['autoJoinGameID']
            modName = User.objects.get(id = Mod.objects.get(gameID=gameID).userID).username
            template = loader.get_template('db/index.html')
            none = {'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID,'modName':modName}
            return HttpResponse(template.render(none,request))
        except:
            print(traceback.print_exc())
            template = loader.get_template('db/index.html')
            none = {'signedIn':signedIn(request), 'user':getUser(request)}
            return HttpResponse(template.render(none,request))

def login(request):
    try:
        request.session['signedIn']
        return HttpResponseRedirect(reverse('index'))
    except:
        template = loader.get_template('db/login.html')
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
        try:
            info = {'error_message':request.session['error_message'],'signedIn':signedIn(request), 'user':getUser(request)}
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
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
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
    none = {'signedIn':signedIn(request), 'user':getUser(request)}
    return HttpResponse(template.render(none,request))

def intro(request):
    template = loader.get_template('db/introduction.html')
    none = {'signedIn':signedIn(request), 'user':getUser(request)}
    return HttpResponse(template.render(none,request))


def signOut(request):
    try:
        del request.session['user']
        del request.session['signedIn']
    except:
        pass
    return HttpResponseRedirect(reverse('index'))

def startGame(request):
    if signedIn(request):
        template = loader.get_template('db/startGame.html')
        none = {'signedIn':signedIn(request), 'user':getUser(request)}
        try:
            none = {'signedIn':signedIn(request), 'user':getUser(request), 'error_message':request.session['error_message']}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(none,request))

    return HttpResponseRedirect(reverse('login'))

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
                        subject = 'Welcome to Assassin Live!'
                        html_message = render_to_string('mail/welcome.html', {'user': username})
                        plain_message = strip_tags(html_message)
                        send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[email], html_message = html_message, fail_silently=False)
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

def startGamePost(request):
    if signedIn(request):
        if not request.POST['killmethod'] == "":
            witnessProtection = False
            if request.POST['witnessprotection'] == 'yes':
                witnessProtection = True

            gameName = request.POST['gameName']

            safety = False
            safetyC = ""
            limit = 0
            if not (request.POST['safetyCircumstances'] == ""):
                safety = True
                safetyC = request.POST['safetyCircumstances']

            if request.POST['limitNum']:
                limit = request.POST['limitNum']

            killCam = False
            killMethod = request.POST['killmethod'].strip().capitalize()
            teams = 1
            # randomTeams = True 
            # if request.POST['teams'] == "1":
            #     randomTeams = False
            # if (request.POST['killCam']=="yes"):
            #     killCam = True
            #     killMethod = killMethod[0].lower() + s[1:]
            #
            # else:
            #     killMethod.capitalize()

            validString = False
            gameString = ""
            while validString == False:
                gameString = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(8))
                if (Game.objects.filter(gameString = gameString).count() == 0):
                    validString = True

            extraRules = request.POST['extrarules']
            email = False
            try:
                email = (request.POST['email'] == "yes")
            except:
                pass
            phone = request.POST['phone']
            other = request.POST['other']
            g = Game(WitnessProtection = witnessProtection, gameString = gameString, gameName = gameName, limit = limit, Safety = safety, SafetyCircumstances = safetyC, KillMethod = killMethod, ExtraRules = extraRules, TimeCreated = datetime.now(),otherContactInfo = other, email = email, phone=phone, killCam = killCam)
            g.save()
            mod = Mod(gameID = g.id, userID = request.session['user'])
            mod.save()
            request.session['error_message'] = "Welcome to your game, moderator! You can get back to this point under the \"Your Games\" tab. Now it's time to invite players!"
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : g.id}))
        else:
            request.session['error_message'] = "You must fill out the assassination method field."
            return HttpResponseRedirect(reverse('startGame'))
    return HttpResponseRedirect(reverse('login'))

def autoJoin(request,gameID):
    request.session['autoJoinGameID'] = gameID
    if signedIn(request):
        try:
            Player.objects.get(userID = request.session['user'], gameID = gameID)
            del request.session['autoJoinGameID']
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : gameID}))
        except:
            pass
        try:
            return joinGamePost(request)
        except:
            return HttpResponseRedirect(reverse('joinGame'))
    else:
        return HttpResponseRedirect(reverse('index'))

def joinGame(request):
    if signedIn(request):
        template = loader.get_template('db/join-game.html')
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':signedIn(request), 'user':getUser(request)}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contract(request,gameID):
    if signedIn(request):
        template = loader.get_template('db/contract.html')
        game = Game.objects.get(id = gameID)
        safetyCircumstances = []
        try:
            safetyCircumstances = [sc.strip().capitalize() for sc in game.SafetyCircumstances.split(",")]

        except:
            print(traceback.print_exc())
        extraRules = []
        try:
            extraRules = game.ExtraRules.split(",")
        except:
            print(traceback.print_exc())


        info = {'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID,'id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID,'id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contractPost(request,gameID):
    if signedIn(request):
        try:
            game = Game.objects.get(pk = gameID)
            try:
                Player.objects.get(gameID = game.id, userID = request.session['user'])
                request.session['error_message'] = "You have already entered the game."
                return HttpResponseRedirect(reverse('joinGame'))
            except Exception:
                try:
                    Mod.objects.get(gameID = game.id, userID = request.session['user'])
                    request.session['error_message'] = "You have already entered the game."
                    return HttpResponseRedirect(reverse('joinGame'))
                except Exception:
                    if game.phase==0:
                        try:
                            checkbox = request.POST['checkbox']
                            p = Player(userID = request.session['user'],gameID = game.pk, alive = True)
                            p.save()
                            return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : game.id}))

                        except Exception:
                            request.session['error_message'] = "To join, you must agree to the contract."
                            return HttpResponseRedirect(reverse('joinGame'))

                    request.session['error_message'] = "Game has already started."
                    return HttpResponseRedirect(reverse('joinGame'))

        except Exception:
            print(traceback.print_exc())
            request.session['error_message'] = "Game does not exist."
            return HttpResponseRedirect(reverse('joinGame'))
    return HttpResponseRedirect(reverse('login'))

def contractExtraInfo(request,gameID):
    if signedIn(request):
        template = loader.get_template('db/contractExtraInfo.html')
        game = Game.objects.get(id = gameID)
        safetyCircumstances = []
        try:
            safetyCircumstances = [sc.strip().capitalize() for sc in game.SafetyCircumstances.split(",")]

        except:
            print(traceback.print_exc())
        extraRules = []
        try:
            extraRules = game.ExtraRules.split(",")
        except:
            print(traceback.print_exc())


        info = {'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID,'id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'gameExtraInfo':game.ExtraUserInfoString}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID,'id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'gameExtraInfo':game.ExtraUserInfoString}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contractExtraInfoPost(request,gameID):
    if signedIn(request):
        try:
            game = Game.objects.get(pk = gameID)
            try:
                Player.objects.get(gameID = game.id, userID = request.session['user'])
                request.session['error_message'] = "You have already entered the game."
                return HttpResponseRedirect(reverse('joinGame'))
            except Exception:
                try:
                    Mod.objects.get(gameID = game.id, userID = request.session['user'])
                    request.session['error_message'] = "You have already entered the game."
                    return HttpResponseRedirect(reverse('joinGame'))
                except Exception:
                    if game.phase==0:
                        try:
                            checkbox = request.POST['checkbox']
                            p = Player(userID = request.session['user'],gameID = game.pk, alive = True, extraInfo = request.POST['extraInfo'])
                            print("HERE" + request.POST['extraInfo'])
                            p.save()
                            return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : game.id}))

                        except Exception:
                            request.session['error_message'] = "To join, you must agree to the contract."
                            return HttpResponseRedirect(reverse('joinGame'))

                    request.session['error_message'] = "Game has already started."
                    return HttpResponseRedirect(reverse('joinGame'))

        except Exception:
            print(traceback.print_exc())
            request.session['error_message'] = "Game does not exist."
            return HttpResponseRedirect(reverse('joinGame'))
    return HttpResponseRedirect(reverse('login'))


def joinGamePost(request):
    if signedIn(request):
        try:
            game = None
            try:
                game = Game.objects.get(gameString = request.POST['gameid'])
            except:
                pass
            try:
                gid = request.session['autoJoinGameID']
                try:
                    del request.session['autoJoinGameID']
                    game = Game.objects.get(pk = gid)
                except Exception:
                    request.session['error_message'] = "Game does not exist."
                    return HttpResponseRedirect(reverse('joinGame'))
            except:
                pass
            try:
                Player.objects.get(gameID = game.id, userID = request.session['user'])
                request.session['error_message'] = "You have already entered the game."
                return HttpResponseRedirect(reverse('joinGame'))
            except Exception:
                try:
                    Mod.objects.get(gameID = game.id, userID = request.session['user'])
                    request.session['error_message'] = "You have already entered the game."
                    return HttpResponseRedirect(reverse('joinGame'))
                except:
                    if game.phase==0:
                        try:
                            if Player.objects.filter(gameID = game.id).count() >= game.limit and game.limit != 0:
                                request.session['error_message'] = "Game is past its player limit."
                                return HttpResponseRedirect(reverse('joinGame'))
                        except:
                            print(traceback.print_exc())
                        if game.ExtraUserInfoString != None:
                            if len(game.ExtraUserInfoString) > 0:
                                return HttpResponseRedirect(reverse('contractExtraInfo', kwargs = {'gameID' : game.id}))
                        else:
                            return HttpResponseRedirect(reverse('contract', kwargs = {'gameID' : game.id}))

                    request.session['error_message'] = "Game has already started."
                    return HttpResponseRedirect(reverse('joinGame'))

        except Exception:
            request.session['error_message'] = "Game does not exist."
            return HttpResponseRedirect(reverse('joinGame'))
    return HttpResponseRedirect(reverse('login'))

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
                    newgames.append([x,convertTo64(x),Game.objects.get(id=x).phase,playerCount,killCount,playerCount-killCount])
                    games = newgames
            except Exception:
                print(traceback.print_exc())

            info = {'username':user.username,'KD': prof.KD, 'gamecount':prof.games, 'mods':prof.mods, 'wins':prof.wins, 'id':userID, 'games':games,'signedIn':signedIn(request), 'user':getUser(request)}

            return HttpResponse(template.render(info,request))
        else:
            template = loader.get_template('db/userNotFound.html')
            info = {'signedIn':signedIn(request), 'user':getUser(request)}
            return HttpResponse(template.render(info,request))
    except:
        template = loader.get_template('db/userNotFound.html')
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
        return HttpResponse(template.render(info,request))

def userSettings(request):
    if signedIn(request):
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':signedIn(request), 'user':getUser(request)}
            del request.session['error_message']
        except:
            pass
        template = loader.get_template('db/user-settings.html')
        return HttpResponse(template.render(info,request))

    return HttpResponseRedirect(reverse('login'))

def userSettingsPost(request):
    if signedIn(request):
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

def game(request, gameID):
    try:
        type = 0
        game = Game.objects.get(id = gameID)
        oldplayers = []
        ids = []
        teams1 = []
        usernames = []
        safetyCircumstances = []
        try:
            safetyCircumstances = [sc.strip().capitalize() for sc in game.SafetyCircumstances.split(",")]

        except:
            print(traceback.print_exc())
        extraRules = []
        try:
            extraRules = game.ExtraRules.split(",")
        except:
            print(traceback.print_exc())

        try:
            for x in filterPlayers(Player.objects.filter(gameID = gameID)):
                if x.alive:
                    oldplayers.append([x.kills,"Yes"])
                else:
                    oldplayers.append([x.kills,"No"])

                ids.append([x.userID,x.id])
                if (game.teams > 1):
                    print(x.teamID)
                    teams1.append(x.teamID)
                else:
                    teams1.append(0)

                usernames.append(User.objects.get(id = x.userID).username)

        except Exception:
            print(traceback.print_exc())
        players = []

        for x in range(len(oldplayers)):
            if (game.teams > 1):
                print(teams1[x])
                players.append([usernames[x],ids[x],oldplayers[x],teams1[x]])
            else:
                players.append([usernames[x],ids[x],oldplayers[x]])
            

        info = {'gameString':game.gameString,'id':convertTo64(gameID),'players':players, 'signedIn':signedIn(request), 'user':getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances,'teams':game.teams}

        try:
            Mod.objects.get(gameID = gameID,userID = request.session['user'])
            type = 2
        except Exception:
            print(traceback.print_exc())
        try:
            Player.objects.get(gameID = gameID, userID = request.session['user'])
            type = 1
        except Exception:
            print(traceback.print_exc())

## For players
        if type == 1:
            p = Player.objects.get(userID = request.session['user'], gameID = gameID)
            if game.phase == 0:
                template = loader.get_template('db/game-player-setup.html')
                return HttpResponse(template.render(info,request))
            elif game.phase == 1:
                template = loader.get_template('db/game-player-live.html')
                target = None
                targetID = None
                targetPlayerID = None
                targetName = None
                targetFullName = None
                targetExtraInfo = None
                try:
                    target = User.objects.get(id = Player.objects.get(id = Player.objects.get(userID = request.session['user'],gameID = gameID).targetID, gameID = gameID).userID)
                    targetID = target.id
                    targetPlayerID = Player.objects.get(id = Player.objects.get(userID = request.session['user'],gameID = gameID).targetID).id
                    targetName = target.username
                    targetFullName = Profile.objects.get(userID = target.id).fullName
                    targetExtraInfo = Player.objects.get(id = targetPlayerID).extraInfo
                except Exception:
                    print(traceback.print_exc())
                info = {'gameString':game.gameString,'id':gameID,'players': players, 'targetname':targetName, 'playerExtraInfo':targetExtraInfo,'targetID':targetID, 'playerID':p.id, 'alive':p.alive, '64id': convertTo64(gameID), 'signedIn':signedIn(request), 'user':getUser(request), 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'killConf':p.killConfirmed,'deathConfirmed':p.deathConfirmed,'targetPlayerID':targetPlayerID,'targetFullName':targetFullName}
                return HttpResponse(template.render(info,request))

## for moderators
        if type == 2:

            if game.phase == 0:
                template = loader.get_template('db/game-mod-setup.html')
                info = None
                try:
                    r = request.session['error_message']
                    info = {'gameString':game.gameString,'id':convertTo64(gameID),'players':players, 'postID':gameID, 'signedIn':signedIn(request), 'user':getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'error_message':r,'teams':game.teams}
                    del request.session['error_message']
                except:
                    info = {'gameString':game.gameString,'id':convertTo64(gameID),'players':players, 'postID':gameID, 'signedIn':signedIn(request), 'user':getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'teams':game.teams}
                return HttpResponse(template.render(info,request))
            elif game.phase == 1:
                template = loader.get_template('db/game-mod-live.html')
                newplayers = []
                for x in range(len(players)):
                    alive = False
                    if (players[x][2][1]=="Yes"):
                        alive = True
                    target = 0
                    targetname = "none"
                    targetPlayerID = 0
                    targetID = 0
                    killed = None
                    gameID = gameID
                    try:

                        targetPlayer = Player.objects.get(id = Player.objects.get(userID = players[x][1][0],gameID = gameID).targetID, gameID = gameID)
                        target = User.objects.get(id = targetPlayer.userID)
                        targetID = target.id
                        targetPlayerID = targetPlayer.id
                        targetname = target.username

                    except:
                        print(traceback.print_exc())

                    try:
                        killed = Player.objects.get(userID = players[x][1][0], gameID = gameID).killedBy
                    except:
                        print(traceback.print_exc())
                    if (game.teams>1):
                        newplayers.append([players[x][0],players[x][1],players[x][2][0],players[x][2][1],targetID,targetname,alive,targetPlayerID, killed,players[x][3]])
                    else:
                        newplayers.append([players[x][0],players[x][1],players[x][2][0],players[x][2][1],targetID,targetname,alive,targetPlayerID, killed])

                try:
                    r = request.session['error_message']
                    info = {'gameString':game.gameString,'id':gameID,'players': newplayers, 'gameID':gameID, '64id': convertTo64(gameID), 'signedIn':signedIn(request), 'user':getUser(request),'error_message':r,'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam,'teams':game.teams}
                    del request.session['error_message']
                except:
                    info = {'gameString':game.gameString,'id':gameID,'players': newplayers, 'gameID':gameID, '64id': convertTo64(gameID), 'signedIn':signedIn(request), 'user':getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam,'teams':game.teams}
                return HttpResponse(template.render(info,request))

        if type == 0:
            if game.phase == 0 or game.phase == 1:
                template = loader.get_template('db/game-public.html')
                return HttpResponse(template.render(info,request))


        if game.phase == 2:
            champion = Player.objects.filter(gameID = gameID, alive = True)[0]
            access = False
            response = None
            try:
                modobj = Mod.objects.get(gameID = gameID)
                if modobj.userID == request.session['user']:
                    access = True
                try:
                    Player.objects.get(gameID = gameID, userID = request.session['user'])
                    access = True
                except:
                    pass
                if access and game.compilationDone:
                    s3 = boto3.resource('s3')
                    try:
                        response = s3.meta.client.generate_presigned_url('get_object',Params={'Bucket': 'videosassassinlive','Key': "comps/"+str(gameID)+".mp4"},ExpiresIn=300)
                    except:
                        print(traceback.print_exc())
            except:
                print(traceback.print_exc())
            info = {'gameString':game.gameString,'id':convertTo64(gameID),'players':players, 'champUserID' : champion.userID, 'champUsername': User.objects.get(id = champion.userID).username, 'signedIn':signedIn(request), 'user':getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'mod':access,'comp':game.compilationDone,'link':response,'teams':game.teams}
            template = loader.get_template('db/game-finished.html')
            return HttpResponse(template.render(info,request))

    except Exception:
        print(traceback.print_exc())
        if signedIn(request):
            return HttpResponse("not found")
        return HttpResponseRedirect(reverse('login'))

def assign_team_initial_bijection(attackingTeam,defendingTeam):
    ## initially assigns a bijection from attackingTeam to defendingTeam, unless |defendingTeam| < |attackingTeam|, then assigns a target twice

    defending = []
    attacking = []


    for x in Player.objects.filter(teamID = defendingTeam, alive = True):
        defending.append(x)

    for x in Player.objects.filter(teamID = attackingTeam, alive = True):
        attacking.append(x)

    print(len(attacking))
    print(len(defending))
    print("IDS:")
    print(attacking[0].id)
    print(defending[0].id)

    defending = randomize_array(defending)
    for x in range(len(attacking)):
        if x >= len(defending)-1:
            print(x)
            print(len(defending)-1)
            attacking[x].targetID = defending[len(defending)-1].id
            attacking[x].save()
            print("here")
            print(User.objects.get(id = attacking[x].userID).username)
            print(User.objects.get(id = (Player.objects.get(id = attacking[x].targetID).userID)).username)
            print(attacking[x])
            print(attacking[x].targetID)
            print(defending[len(defending)-1].id)
        else:
            attacking[x].targetID = defending[x].id
            attacking[x].save()
            print("here")
            print("here")

            print(User.objects.get(id = attacking[x].userID).username)
            print(User.objects.get(id = defending[x].userID).username)

            print(attacking[x])
            print(attacking[x].targetID)
            print(defending[x].id)

def create_random_teams(players):
    game = Game.objects.get(id = players[0].gameID)
    teamSize = game.teams
    players = randomize_array(players)
    teams = []
    print(len(players))
    print(len(players)/teamSize)
    for x in range(int(len(players)/teamSize)):
        team = []

        for y in range(teamSize+1):
            if not ((x*teamSize + y) > (len(players)-1)):
                team.append(players[x*teamSize + y])
        
        teams.append(team)

    if (len(teams)*teamSize < len(players)):
        team = players[len(teams)*teamSize-1:]
        teams.append(team)
        
    for x in teams:
        t = Team(gameID = game.id)
        t.save()
        for y in x:
            y.teamID = t.id
            y.save()
    


def randomize_array(array):
    randomArr = []
    for x in range(len(array)):
        randomNum = random.randint(0,len(array)-1)
        randomArr.append(array[randomNum])
        array.pop(randomNum)

    return randomArr

    

def randomizeTargets(request,gameID):
    try:
        game = Game.objects.get(id = gameID)
        if (Mod.objects.get(gameID = gameID).userID == request.session['user'] and game.phase == 1):
            playerList = Player.objects.filter(gameID = gameID, alive = True)
            nl = []
            pl = []

            for x in playerList:
                pl.append(x)     

            for x in range(len(pl)):
                randomNum = random.randint(0,len(pl)-1)
                nl.append(pl[randomNum])
                pl.pop(randomNum)

            playerList = nl

            for x in range(len(playerList)):
                if x < len(playerList)-1:
                    playerList[x].targetID = playerList[x+1].id
                    playerList[x].save()

            else:
                playerList[x].targetID = playerList[0].id
                playerList[x].save()
            
        return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : gameID}))

    except:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))

   

def startPlaying(request,gameID):
    if signedIn(request):
        try:
            game = Game.objects.get(id = convertFrom64(str(gameID)))
            if Mod.objects.get(gameID = gameID).userID == request.session['user'] and game.phase == 0 and Player.objects.filter(gameID = gameID).count() > 1:
                playerList = Player.objects.filter(gameID = gameID)

                nl = []
                pl = []

                for x in playerList:
                    pl.append(x)

                if game.teams > 1:
                    print(pl)
                    create_random_teams(pl)
                    teams = []
                    for x in Team.objects.filter(gameID = game.id):
                        teams.append(x)
                    
                    print(teams)

                    teams = randomize_array(teams)
                    


                    for x in range(len(teams)):
                        if x < len(teams)-1:
                            teams[x].targetID = teams[x+1].id
                            teams[x].save()

                        else:
                            teams[x].targetID = teams[0].id
                            teams[x].save()

                    for x in Team.objects.filter(gameID = game.id):
                        print(x.id)
                        for y in Player.objects.filter(teamID = x.id):
                            print("player")
                            print(y.id)
                    
                    for x in Team.objects.filter(gameID = game.id):
                        assign_team_initial_bijection(x.id,x.targetID)

                else:
                    for x in range(len(pl)):
                        randomNum = random.randint(0,len(pl)-1)
                        nl.append(pl[randomNum])
                        pl.pop(randomNum)

                    playerList = nl

                    for x in range(len(playerList)):
                        if x < len(playerList)-1:
                            playerList[x].targetID = playerList[x+1].id
                            playerList[x].save()

                        else:
                            playerList[x].targetID = playerList[0].id
                            playerList[x].save()

                game.TimeStart = datetime.now()
                game.phase = 1
                game.save()
                info = []

                for x in Player.objects.filter(gameID = gameID):
                    try:
                        info.append({'user':User.objects.get(id = x.userID).username, 'targetID':Player.objects.get(id = x.targetID).userID, 'targetName':User.objects.get(id = Player.objects.get(id = x.targetID).userID).username, 'gameID':gameID,'email':User.objects.get(id = x.userID).email})
                    except:
                        print(traceback.print_exc())

                send_email("gamestart",info)
                try:
                    mod = Mod.objects.get(gameID = gameID)
                    subject = 'Game ' + convertTo64(gameID) +' has started!'
                    html_message = render_to_string('mail/mod-gameStart.html', {'user':User.objects.get(id = mod.userID).username, 'gameID':gameID})
                    plain_message = strip_tags(html_message)
                    send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = mod.userID).email], html_message = html_message, fail_silently=False)
                except:
                    print(traceback.print_exc())

                request.session['error_message'] = "Let the games begin! Now you can sit back and wait. Players might have a dispute. They will contact you with the contact information you provided."
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : gameID}))
            else:
                request.session['error_message'] = "The game must have more than one player to start."
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : gameID}))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))

    return HttpResponseRedirect(reverse('login'))

def completeKill(assassinPlayerID, assassinatedPlayerID, gameID):
    assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
    assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
    game = Game.objects.get(id = gameID)
    assassinatedTargetID = assassinated.targetID
    k = Kill(gameID = gameID, killerID = assassin.id, killedID = assassinated.id, timeKilled = datetime.now())
    k.save()

    assassin.kills = assassin.kills + 1
    assassin.score = assassin.score + 10
    assassin.killConfirmed = False
    assassin.save()
    if (game.teams == 1):
        assassin.targetID = assassinatedTargetID
        assassin.save()
    else:
        attackingTeam = Team.objects.get(id = assassin.teamID)
        defendingTeam = Team.objects.get(id = assassinated.teamID)
        if (Player.objects.filter(teamID = defendingTeam.id, alive = True).count() == 1):
            attackingTeam.targetID = defendingTeam.targetID
            defendingTeam.alive = False
            defendingTeam.targetID = 0
            assassinated.alive = False
            assassinated.save()
            attackingTeam.save()
            defendingTeam.save()

            if not (Team.objects.filter(gameID = gameID, alive = True).count() <= 1):
                assign_team_initial_bijection(attackingTeam.id,attackingTeam.targetID)
        else:
            assassinated.alive = False
            assassinated.save()
            assassin.targetID = Player.objects.filter(teamID = defendingTeam.id, alive = True)[0].id
            assassin.save()
            
    
    assassinated.targetID = 0
    assassinated.alive = False
    assassinated.killedBy = assassinPlayerID
    assassinated.save()
    if game.killCam:
        try:
            kv = KillVideo.objects.get(killerID = assassinPlayerID, killedID = assassinatedPlayerID, gameID = gameID)
            kv.killID = k.id
            kv.killConf = True
            kv.save()
        except Exception:
            print(traceback.print_exc())
    finished = checkFinished(gameID)
    if not finished:
        try:
            subject = 'Your kill was confirmed - your new target awaits.'
            html_message = render_to_string('mail/player-kill.html', {'killedID': assassinated.userID, 'killed':User.objects.get(id = assassinated.userID).username,'user':User.objects.get(id = assassin.userID).username, 'targetID':Player.objects.get(id = assassin.targetID).userID, 'target':User.objects.get(id = Player.objects.get(id = assassin.targetID).userID).username, 'gameID':gameID })
            plain_message = strip_tags(html_message)
            send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = assassin.userID).email], html_message = html_message, fail_silently=False)
        except:
            print(traceback.print_exc())


def modKill(request,assassinPlayerID, assassinatedPlayerID, gameID):
    try:
        Mod.objects.get(gameID = gameID,userID = request.session['user'])
        assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
        assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
        if assassinated.alive and assassin.alive:
            completeKill(assassinPlayerID,assassinatedPlayerID,gameID)
        return HttpResponseRedirect(reverse('game', kwargs={'gameID':gameID}))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))

def modReverseDeath(request, assassinPlayerID, assassinatedPlayerID, gameID):
    try:
        Mod.objects.get(gameID = gameID,userID = request.session['user'])
        assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
        assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
        if not(assassinated.alive) and assassin.alive:
            reverseDeath(assassinPlayerID,assassinatedPlayerID,gameID)
            return HttpResponseRedirect(reverse('game', kwargs={'gameID':gameID}))
        return HttpResponseRedirect(reverse('game', kwargs={'gameID':gameID}))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))


def reverseDeath(assassinPlayerID, assassinatedPlayerID, gameID):
    assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
    assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
    assassinTargetID = assassin.targetID
    k = Kill.objects.get(gameID = gameID, killerID = assassin.id, killedID = assassinated.id)
    k.delete()
    assassin.targetID = assassinatedPlayerID
    assassin.kills = assassin.kills - 1
    assassin.killConfirmed = False
    assassin.save()
    assassinated.targetID = assassinTargetID
    assassinated.alive = True
    assassinated.killedBy = None
    assassinated.deathConfirmed = False
    assassinated.save()
    if Game.objects.get(id = gameID).killCam:
        try:
            kv = KillVideo.objects.get(killerID = assassinPlayerID, killedID = assassinatedPlayerID, gameID = gameID)
            deleteKillVideo(kv.id)
        except:
            print(traceback.print_exc())


def confirmDeath(request, playerID):
    try:
        p = Player.objects.get(id = playerID)
        g = Game.objects.get(id = p.gameID)
        if request.session['user'] == p.userID:
            if p.deathConfirmed == True:
                try:
                    kv = KillVideo.objects.get(killerID = Player.objects.get(targetID = playerID).id, killedID = playerID, gameID = Player.objects.get(id = playerID).gameID)
                    deleteKillVideo(kv.id)
                except:
                    print(traceback.print_exc())
                try:
                    kv = KillVideo.objects.get(killerID = Player.objects.get(targetID = playerID).id, targetID = playerID, gameID = gameID)
                    kv.delete()
                except:
                    pass
                p.deathConfirmed = False
                p.save()
            else:
                if g.killCam:
                    info = {'gameID':g.id,'killedID':playerID,'signedIn':signedIn(request), 'user':getUser(request)}
                    template = loader.get_template('db/decideVidAccess.html')
                    return HttpResponse(template.render(info,request))
                else:
                    p.deathConfirmed = True
                    p.save()
                    try:
                        subject = 'Your death was confirmed'
                        html_message = render_to_string('mail/player-deathConfirmed.html', {'user':User.objects.get(id = p.userID).username, 'kills':p.kills, 'gameID':p.gameID})
                        plain_message = strip_tags(html_message)
                        send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = p.userID).email], html_message = html_message, fail_silently=False)
                    except:
                        print(traceback.print_exc())
                    doubleConf(Player.objects.get(targetID = playerID).id, playerID, p.gameID)
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':p.gameID}))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))

def allowVideoUsePost(request,killedID,gameID):
    try:
        p = Player.objects.get(id = killedID)
        if request.session['user']==p.userID and p.alive and p.deathConfirmed == False and Game.objects.get(id = p.gameID):
            allowed = False
            try:
                if request.POST['compilationUse'] == "yes":
                    allowed = True
            except:
                pass
            kv = KillVideo(killerID = Player.objects.get(targetID = killedID).id, killedID = killedID, gameID = gameID, usable = allowed)
            try:
                kv = KillVideo.objects.get(killerID = Player.objects.get(targetID = killedID).id, killedID = killedID, gameID = gameID)
                if allowed == False:
                    kv.usable = False
            except:
                pass
            kv.save()
            p.deathConfirmed = True
            p.save()
            try:
                subject = 'Your death was confirmed'
                html_message = render_to_string('mail/player-deathConfirmed.html', {'user':User.objects.get(id = p.userID).username, 'kills':p.kills, 'gameID':p.gameID})
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = p.userID).email], html_message = html_message, fail_silently=False)
            except:
                print(traceback.print_exc())
            doubleConf(Player.objects.get(targetID = killedID).id, killedID, p.gameID)
        return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
    except:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))





def confirmKill(request, playerID):
    try:
        p = Player.objects.get(id = playerID)
        if request.session['user'] == p.userID and not Game.objects.get(id = p.gameID).killCam:
            if p.killConfirmed == False:
                p.killConfirmed = True
                p.save()
                doubleConf(playerID, p.targetID, p.gameID)
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID':p.gameID}))

            else:
                p.killConfirmed = False
                p.save()
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID':p.gameID}))

    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))

def doubleConf(assassinPlayerID,assassinatedPlayerID, gameID):
    assassin = Player.objects.get(id = assassinPlayerID)
    assassinated= Player.objects.get(id = assassinatedPlayerID)
    if assassin.killConfirmed and assassinated.deathConfirmed:
        completeKill(assassinPlayerID,assassinatedPlayerID, gameID)

def checkFinished(gameID):
    g = Game.objects.get(id = gameID)
    players = Player.objects.filter(gameID = gameID)
    kills = Kill.objects.filter(gameID = gameID)
    aliveTeams = Team.objects.filter(gameID = gameID, alive = True).count()
    if (len(players) - len(kills) == 1) or aliveTeams == 1:
        g.phase = 2
        g.TimeEnd = datetime.now()
        g.save()
        for x in kills:
            p = Profile.objects.get(userID = Player.objects.get(id = x.killerID).userID)
            p.kills = p.kills + 1
            p.save()
        for x in players:
            p = Profile.objects.get(userID = x.userID)
            p.games = p.games + 1
            p.save()
            updateKD(x.userID)

        champion = Profile.objects.get(userID = 1)
    
        if (game.teams > 1):
            winningTeam = Team.objects.get(gameID = gameID, alive = True)
            champions = Player.objects.filter(gameID = gameID, teamID = winningTeam.id)
            for x in champions:
                champion = Profile.objects.get(userID = x.userID)
                champion.wins = champion.wins + 1
                champion.save()
        else:
            champion = Profile.objects.get(userID = Player.objects.get(gameID = gameID, alive = True).userID)
            champion.wins = champion.wins + 1
            champion.save()


        mod = Profile.objects.get(userID = Mod.objects.get(gameID = gameID).userID)
        mod.mods = mod.mods + 1
        mod.save()
        startComp(gameID)
        info = []

        for x in Player.objects.filter(gameID = gameID):
            try:
                info.append({'gameID':gameID,'champID':champion.userID,'champName':User.objects.get(id = champion.userID).username,'email':User.objects.get(id = x.userID).email})
            except:
                print(traceback.print_exc())

        try:
            info.append({'gameID':gameID,'champID':champion.userID,'champName':User.objects.get(id = champion.userID).username,'email':User.objects.get(id = mod.userID).email})
            send_email("gamefinish",info)
        except:
            pass
        return True
    return False



def updateKD(userID):
    profile = Profile.objects.get(userID = userID)
    KD = 0
    KD = profile.kills / profile.games
    profile.KD = KD
    profile.save()


def gameSettings(request, gameID):
    if signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            game = Game.objects.get(id = gameID)
            if (game.phase == 0 or game.phase == 1):
                info = {'gameID' : gameID,'witnessProtection': game.WitnessProtection, 'limit':game.limit,'circumstances': game.SafetyCircumstances, 'killMethod': game.KillMethod, 'killCam':game.killCam, 'extraRules': game.ExtraRules, 'contactInfo':game.otherContactInfo, 'email':game.email, 'phone': game.phone, '64id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request)}
                template = loader.get_template('db/game-mod-settings.html')
                return HttpResponse(template.render(info,request))
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))

def duelSubmission(request,gameID):
    if signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            game = Game.objects.get(id = gameID)
            if (game.phase == 1):
                info = {'gameID' : gameID,'64id':convertTo64(gameID),'signedIn':signedIn(request), 'user':getUser(request)}
                template = loader.get_template('db/game-mod-duel-submission.html')
                return HttpResponse(template.render(info,request))
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login')) 

def duelSubmissionPost(request, gameID):
    if signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            g = Game.objects.get(id = gameID)

            user1 = User.objects.get(username = request.POST['champion'])
            user2 = User.objects.get(username = request.POST['loser'])

            player1 = Player.objects.get(gameID = gameID, userID = user1.id)
            player2 = Player.objects.get(gameID = gameID, userID = user2.id)

            if (player1.targetID == player2.id):
                k = Kill(gameID = gameID, killerID = player1.id, killedID = player2.id, timeKilled = datetime.now())
                k.save()
                player1.kills = player1.kills + 1
                player1.killConfirmed = False
                player1.targetID = player2.targetID
                player1.save()
                player2.targetID = 0
                player2.alive = False
                player2.killedBy = player1.id
                player2.save()

            else:
                k = Kill(gameID = gameID, killerID = player1.id, killedID = player2.id, timeKilled = datetime.now())
                k.save()
                player1.kills = player1.kills + 1
                player1.save()
                player2assassin = Player.objects.get(gameID = gameID, targetID = player2.id)
                player2assassin.targetID = player2.targetID
                player2assassin.save()
                player2.targetID = 0
                player2.alive = False
                player2.killedBy = player1.id
                player2.save()

            finished = checkFinished(gameID)

            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))

        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))

def getPassword(request):

    try:
        error_message = request.session['error_message']
        info = {'signedIn':signedIn(request), 'user':getUser(request),'error_message':error_message}
        del request.session['error_message']
    except:
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
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


def gameSettingsPost(request, gameID):
    if signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            g = Game.objects.get(id = gameID)
            witnessProtection = False
            if request.POST['witnessprotection'] == 'yes':
                witnessProtection = True

            safety = False
            safetyC = ""
            limit = 0
            if not (request.POST['safetyCircumstances'] == ""):
                safety = True
                safetyC = request.POST['safetyCircumstances']
            killCam = False
            killMethod = request.POST['killmethod']
            killMethod[0].upper()
            if request.POST['limitNum']:
                limit = request.POST['limitNum']

            # if (request.POST['killCam']=="yes"):
            #     killCam = True
            #     killMethod[0].lower()
            # else:
            #     killMethod[0].upper()

            extraRules = request.POST['extrarules']
            g.WitnessProtection = witnessProtection
            g.Safety = safety
            g.SafetyCircumstances = safetyC
            g.KillMethod = killMethod
            g.ExtraRules = extraRules
            g.otherContactInfo = request.POST['other']
            g.phone = request.POST['phone']
            g.killCam = killCam
            g.limit = limit
            email = False
            try:
                email = (request.POST['email'] == "yes")
            except:
                pass
            g.email = email
            g.save()
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))

        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))

def getUser(request):
    try:
        return request.session['user']
    except Exception:
        return None

def filterPlayers(players):
    alive = []
    dead = []
    for x in players:
        if x.alive:
            alive.append(x)
        else:
            dead.append(x)

    alive = sortByKills(alive)
    dead = sortByKills(dead)
    alive.extend(dead)
    players = alive
    return players

def sortByKills(players):
    random.shuffle(players)
    try:
        for x in range(len(players)):
            newArr = players[x:]
            maxID = 0
            for y in range(len(newArr)):
                if newArr[y].kills > newArr[maxID].kills:
                    maxID = y

            print(maxID)
            p = players[x]
            players[x] = newArr[maxID]
            players[x+maxID] = p
            print(players)
            print(players[x+maxID].id)
        return players
    except Exception:
        print(traceback.print_exc())
        return []

def deletePlayer(request,playerID,gameID):
    if signedIn(request):
        try:
            if request.session['user'] == Mod.objects.get(gameID = gameID).userID:
                if (Game.objects.get(id = gameID).phase == 0):
                    Player.objects.get(id = playerID).delete()
                    return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))

            return HttpResponseRedirect(reverse('index'))

        except:
            return HttpResponseRedirect(reverse('index'))

    return HttpResponseRedirect(reverse('login'))

def termsConditions(request):
    info = {'signedIn':signedIn(request), 'user':getUser(request)}
    template = loader.get_template('db/termsConditions.html')
    return HttpResponse(template.render(info,request))


def modHelp(request):
        template = loader.get_template('db/mod-help.html')
        info = {'signedIn':signedIn(request), 'user':getUser(request)}
        return HttpResponse(template.render(info,request))

def deleteGame(request,gameID):
    if signedIn(request):
        try:
            if request.session['user'] == Mod.objects.get(gameID = gameID).userID:
                if (Game.objects.get(id = gameID).phase == 0):
                    Game.objects.get(id = gameID).delete()
                    Player.objects.filter(gameID = gameID).delete()
                    Mod.objects.filter(gameID = gameID).delete()
                    Team.objects.filter(gameID = gameID).delete()
            return HttpResponseRedirect(reverse('index'))
        except:
            return HttpResponseRedirect(reverse('index'))

    return HttpResponseRedirect(reverse('login'))


def contactMod(request,gameID):
    if signedIn(request):
        try:
            Player.objects.get(userID = request.session['user'],gameID = gameID)
            template = loader.get_template('db/mod-contact.html')
            email = ""
            g = Game.objects.get(id = gameID)
            if g.email:
                email = User.objects.get(id = Mod.objects.get(gameID = gameID).userID).email
            info = {'signedIn':signedIn(request), 'user':getUser(request), 'phone':g.phone, 'email':email,'contact':g.otherContactInfo, 'id': convertTo64(g.id),'gameID': gameID}
            return HttpResponse(template.render(info,request))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))


def checkout(request):
    if signedIn(request):
        session = stripe.checkout.Session.create(
          payment_method_types=['card'],
          mode='payment',
          success_url='https://example.com/success?session_id={CHECKOUT_SESSION_ID}',
          cancel_url='https://example.com/cancel',
        )
        info = {'session':session.id,'signedIn':signedIn(request), 'user':getUser(request)}
        template = loader.get_template('db/checkout.html')
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def killVideo(request,killerID,targetID,gameID):
    try:
        game = Game.objects.get(id = gameID)
        killer = Player.objects.get(id = killerID)

        if game.killCam == True and request.session['user'] == killer.userID and killer.targetID == targetID:
            if killer.killConfirmed == True:
                killer.killConfirmed = False
                killer.save()
                try:
                    kv = KillVideo.objects.get(killerID = killerID, killedID = targetID, gameID = gameID)
                    deleteKillVideo(kv.id)
                except:
                    print(traceback.print_exc())
                try:
                    kv = KillVideo.objects.get(killerID = killerID, targetID = targetID, gameID = gameID)
                    kv.delete()
                except:
                    pass
                return HttpResponseRedirect(reverse('index'))
            else:
                template = loader.get_template('db/submitKillVid.html')
                g = Game.objects.get(id = gameID)
                killCam = g.killCam
                killMethod = g.KillMethod
                info = {'signedIn':signedIn(request), 'user':getUser(request),'killerID':killerID,'targetID':targetID,'gameID':gameID, 'killCam': killCam, 'killMethod': killMethod}
                try:
                    info = {'signedIn':signedIn(request), 'user':getUser(request),'killerID':killerID,'targetID':targetID,'gameID':gameID,'error_message':request.session['error_message'], 'killCam':killCam, 'killMethod':killMethod}
                    del request.session['error_message']
                except:
                    pass
                return HttpResponse(template.render(info,request))
        return HttpResponseRedirect(reverse('login'))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('login'))

def killVideoPost(request,killerID,targetID,gameID):
    try:
        game = Game.objects.get(id = gameID)
        killer = Player.objects.get(id = killerID)
        if request.method == 'POST':
            if game.killCam == True and request.session['user'] == killer.userID and killer.targetID == targetID and killer.killConfirmed == False:

                try:
                    form = VideoForm(request.POST, request.FILES)
                except:
                    request.session['error_message'] = "You must upload a video."
                    return HttpResponseRedirect(reverse('killVideo', kwargs = {'gameID' : game.id, 'killerID' : killerID, 'targetID' : targetID}))


                print(request.FILES)
                if request.FILES['video'].size < 10000000:
                    if request.FILES['video'].content_type[:5]=="video":
                        s3 = boto3.resource('s3')
                        allowed = False
                        try:
                            if request.POST['compilationUse'] == "yes":
                                allowed = True
                        except:
                            pass
                        kv = KillVideo(killerID = killerID, killedID = targetID, gameID = gameID, usable = allowed)
                        try:
                            kv = KillVideo.objects.get(killerID = killerID, killedID = targetID, gameID = gameID)
                            if allowed == False:
                                kv.usable = False
                        except:
                            pass
                        kv.save()
                        s3.meta.client.upload_fileobj(request.FILES['video'], 'videosassassinlive', str(kv.id))
                        del request.FILES['video']
                        template = loader.get_template('db/killConfirmSuccess.html')
                        info = {'signedIn':signedIn(request), 'user':getUser(request),'gameID':gameID}
                        killer.killConfirmed = True
                        killer.save()
                        doubleConf(killerID, targetID, gameID)

                        return HttpResponse(template.render(info,request))
                    else:
                        request.session['error_message'] = "The file you uploaded is not recognized as a video."
                else:
                    request.session['error_message'] = "Video must be less than 10mb (try cutting down the length)"
                return HttpResponseRedirect(reverse('killVideo', kwargs = {'gameID' : game.id, 'killerID' : killerID, 'targetID' : targetID}))
            return HttpResponseRedirect(reverse('login'))
    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('login'))

def deleteKillVideo(id):
    kv = KillVideo.objects.get(id = id)
    s3 = boto3.resource('s3')
    s3.meta.client.delete_object(Bucket = 'videosassassinlive', Key = str(id))
    kv.delete()

def createCompilation(gameID):
    try:
        s3 = boto3.resource('s3')
        v = None
        a = None
        if KillVideo.objects.filter(gameID = gameID,usable=True).count() == 0:
            return False
        for x in KillVideo.objects.filter(gameID = gameID,usable=True):
            try:
                print(str(x.id))
                s3.meta.client.download_file('videosassassinlive', str(x.id),str(x.id)+".mp4")
                if v == None and a == None:
                    inte = ffmpeg.input(str(x.id)+".mp4")
                    a = inte.audio
                    v = inte.video.filter('scale', w=1920,h=1080,force_original_aspect_ratio='decrease').filter('pad',w=1920,h=1080,x='(ow-iw)/2',y='(oh-ih)/2')

                else:
                    inew = ffmpeg.input(str(x.id)+".mp4")
                    anew = inew.audio
                    vnew = inew.video.filter('scale', w=1920,h=1080,force_original_aspect_ratio='decrease').filter('pad',w=1920,h=1080,x='(ow-iw)/2',y='(oh-ih)/2')
                    inte = ffmpeg.concat(v,a,vnew,anew,v=1,a=1).node
                    v = inte[0]
                    a = inte[1]
            except:
                subject = 'Error'
                html_message = render_to_string('mail/player-gameStart.html', {'gameID':traceback.format_exc()})
                plain_message = strip_tags(html_message)
                send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',["evan.coats9@gmail.com"], html_message = html_message, fail_silently=False)

        ffmpeg.output(v,a,str(gameID)+"comp"+".mp4",f="mp4").run()

        for x in KillVideo.objects.filter(gameID = gameID):
            try:
                os.remove(str(x.id)+".mp4")
                obj = s3.Object('videosassassinlive', str(x.id))
                obj.delete()
            except:
                print(traceback.print_exc())

        s3.meta.client.upload_file(str(gameID)+"comp"+".mp4", 'videosassassinlive', "comps/"+str(gameID)+".mp4")
        os.remove(str(gameID)+"comp"+".mp4")
        return True
    except:
        subject = 'Error'
        html_message = render_to_string('mail/player-gameStart.html', {'gameID':traceback.format_exc()})
        plain_message = strip_tags(html_message)
        send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',["evan.coats9@gmail.com"], html_message = html_message, fail_silently=False)

def getToken(request):
    if signedIn(request):
        try:
            del request.session['getToken']
            token,created= Token.objects.get_or_create(user = User.objects.get(id = request.session['user']))
            template = loader.get_template('db/get-token.html')
            info = {'signedIn':signedIn(request), 'user':getUser(request),'discord_code':token.key}
            return HttpResponse(template.render(info,request))
        except:
            print(traceback.print_exc())
        request.session['getToken'] = True
        return HttpResponseRedirect(reverse('index'))
    request.session['getToken'] = True
    return HttpResponseRedirect(reverse('index'))



# @background(schedule=5,queue="videoqueue")
# def startComp(gameID):
#     try:
#         if createCompilation(gameID) == True:
#             g = Game.objects.get(id=gameID)
#             g.compilationDone = True
#             g.save()
#     except:
#         pass

# @background(schedule=5)
# def send_email(temp, info):
#     try:
#         if temp == "gamestart":
#             for x in info:
#                 try:
#                     subject = 'Game ' + convertTo64(gameID) +' has started!'
#                     html_message = render_to_string('mail/player-gameStart.html', {'user':x['username'], 'targetID':x['targetID'], 'targetName':x['targetname'], 'gameID':x['gameID']})
#                     plain_message = strip_tags(html_message)
#                     send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[x['email']], html_message = html_message, fail_silently=False)
#                 except:
#                     pass
#         if temp == "gamefinish":
#             for x in info:
#                 try:
#                     subject = 'Game ' + convertTo64(gameID) +' is finished!'
#                     html_message = render_to_string('mail/player-gameFinish.html', {'gameID':x['gameID'],'champID':x['champID'],'champname':x['champName']})
#                     plain_message = strip_tags(html_message)
#                     send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[x['email']], html_message = html_message, fail_silently=False)
#                 except:
#                     pass
#     except:
#         print(traceback.print_exc())