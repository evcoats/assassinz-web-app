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
from . import extra_views
from . import views_functions
from . import game_functions

from . import rest_api






def startGame(request):
    if views_functions.signedIn(request):
        template = loader.get_template('db/startGame.html')
        none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        try:
            none = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request), 'error_message':request.session['error_message']}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(none,request))

    return HttpResponseRedirect(reverse('login'))


def startGamePost(request):
    if views_functions.signedIn(request):
        if not request.POST['killmethod'] == "":
            if not request.POST['gameName'] == "":
                
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
                if request.POST["teams"] == 'custom':
                    teams = int(request.POST['customteamsize'])
                else:
                    teams = int(request.POST['teams'])

                print(request.POST["teams"])

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
                g = Game(WitnessProtection = witnessProtection, gameString = gameString, gameName = gameName, limit = limit, Safety = safety, SafetyCircumstances = safetyC, KillMethod = killMethod, teams=teams,ExtraRules = extraRules, TimeCreated = datetime.now(),otherContactInfo = other, email = email, phone=phone, killCam = killCam)
                g.save()
                mod = Mod(gameID = g.id, userID = request.session['user'])
                mod.save()
                request.session['error_message'] = "Welcome to your game, moderator! You can get back to this point under the \"Your Games\" tab. Now it's time to invite players!"
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID' : g.id}))
            else:
                request.session['error_message'] = "You must fill out the game name field."
                return HttpResponseRedirect(reverse('startGame'))

        else:
            request.session['error_message'] = "You must fill out the assassination method field."
            return HttpResponseRedirect(reverse('startGame'))
    return HttpResponseRedirect(reverse('login'))

def autoJoin(request,gameID):
    request.session['autoJoinGameID'] = gameID
    if views_functions.signedIn(request):
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
    if views_functions.signedIn(request):
        template = loader.get_template('db/join-game.html')
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contract(request,gameID):
    if views_functions.signedIn(request):
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


        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'gameID':gameID,'id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'gameID':gameID,'id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contractPost(request,gameID):
    if views_functions.signedIn(request):
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
    if views_functions.signedIn(request):
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


        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'gameID':gameID,'id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'gameExtraInfo':game.ExtraUserInfoString}
        try:
            info = {'error_message':request.session['error_message'], 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'gameID':gameID,'id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'gameExtraInfo':game.ExtraUserInfoString}
            del request.session['error_message']
        except:
            pass
        return HttpResponse(template.render(info,request))
    return HttpResponseRedirect(reverse('login'))

def contractExtraInfoPost(request,gameID):
    if views_functions.signedIn(request):
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
    if views_functions.signedIn(request):
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


def game(request, gameID):
    try:
        type = 0
        game = Game.objects.get(id = gameID)
        oldplayers = []
        ids = []
        teams1 = []
        scores = []
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
            for x in game_functions.filterPlayers(Player.objects.filter(gameID = gameID)):
                if x.alive:
                    oldplayers.append([x.kills,"Yes",x.score])
                else:
                    oldplayers.append([x.kills,"No",x.score])

                ids.append([x.userID,x.id])
                scores.append([x.score])
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
                players.append([usernames[x],ids[x],oldplayers[x],scores[x],teams1[x]])
            else:
                players.append([usernames[x],ids[x],oldplayers[x],scores[x]])
            

        info = {'gameString':game.gameString,'id':views_functions.convertTo64(gameID),'players':players, 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'killCam':game.killCam,'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances,'teams':game.teams,'name':game.gameName}

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
                info = {'gameString':game.gameString,'id':gameID,'players': players, 'targetname':targetName, 'playerExtraInfo':targetExtraInfo,'targetID':targetID, 'playerID':p.id, 'alive':p.alive, '64id': views_functions.convertTo64(gameID), 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request), 'extraRules':extraRules,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam, 'killConf':p.killConfirmed,'deathConfirmed':p.deathConfirmed,'targetPlayerID':targetPlayerID,'targetFullName':targetFullName,'name':game.gameName}
                return HttpResponse(template.render(info,request))

## for moderators
        if type == 2:

            if game.phase == 0:
                template = loader.get_template('db/game-mod-setup.html')
                info = None
                try:
                    r = request.session['error_message']
                    info = {'gameString':game.gameString,'id':views_functions.convertTo64(gameID),'players':players, 'postID':gameID, 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'error_message':r,'teams':game.teams,'name':game.gameName}
                    del request.session['error_message']
                except:
                    info = {'gameString':game.gameString,'id':views_functions.convertTo64(gameID),'players':players, 'postID':gameID, 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'teams':game.teams,'name':game.gameName}
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
                        newplayers.append([players[x][0],players[x][1],players[x][2][0],players[x][2][1],targetID,targetname,alive,targetPlayerID, killed,players[x][3],players[x][4] ])
                    else:
                        newplayers.append([players[x][0],players[x][1],players[x][2][0],players[x][2][1],targetID,targetname,alive,targetPlayerID, killed,players[x][3]])

                try:
                    print(players)
                    r = request.session['error_message']
                    info = {'gameString':game.gameString,'id':gameID,'players': newplayers, 'gameID':gameID, '64id': views_functions.convertTo64(gameID), 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'error_message':r,'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam,'teams':game.teams,'name':game.gameName}
                    del request.session['error_message']
                except:
                    info = {'gameString':game.gameString,'id':gameID,'players': newplayers, 'gameID':gameID, '64id': views_functions.convertTo64(gameID), 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'killMethod':game.KillMethod, 'witnessProtection':game.WitnessProtection, 'killCam':game.killCam,'teams':game.teams,'name':game.gameName}
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
                    s3 = boto3.resource('s3',aws_access_key_id='NONE',aws_secret_access_key='NONE')
                    try:
                        response = s3.meta.client.generate_presigned_url('get_object',Params={'Bucket': 'videosassassinlive','Key': "comps/"+str(gameID)+".mp4"},ExpiresIn=300)
                    except:
                        print(traceback.print_exc())
            except:
                print(traceback.print_exc())
            info = {'gameString':game.gameString,'id':views_functions.convertTo64(gameID),'players':players, 'champUserID' : champion.userID, 'champUsername': User.objects.get(id = champion.userID).username, 'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request),'extraRules':extraRules, 'killMethod':game.KillMethod,'safety':game.Safety, 'safetyCircumstances':safetyCircumstances, 'witnessProtection':game.WitnessProtection,'killCam':game.killCam,'mod':access,'comp':game.compilationDone,'link':response,'teams':game.teams,'name':game.gameName}
            template = loader.get_template('db/game-finished.html')
            return HttpResponse(template.render(info,request))

    except Exception:
        print(traceback.print_exc())
        if views_functions.signedIn(request):
            return HttpResponse("not found")
        return HttpResponseRedirect(reverse('login'))
    


def confirmDeath(request, playerID):
    try:
        p = Player.objects.get(id = playerID)
        g = Game.objects.get(id = p.gameID)
        if request.session['user'] == p.userID:
            if p.deathConfirmed == True:
                try:
                    kv = KillVideo.objects.get(killerID = Player.objects.get(targetID = playerID).id, killedID = playerID, gameID = Player.objects.get(id = playerID).gameID)
                    extra_views.deleteKillVideo(kv.id)
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
                    info = {'gameID':g.id,'killedID':playerID,'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
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
    

def startPlaying(request,gameID):
    if views_functions.signedIn(request):
        try:
            game = Game.objects.get(id = views_functions.convertFrom64(str(gameID)))
            if Mod.objects.get(gameID = gameID).userID == request.session['user'] and game.phase == 0 and Player.objects.filter(gameID = gameID).count() > 1:
                playerList = Player.objects.filter(gameID = gameID)

                nl = []
                pl = []

                for x in playerList:
                    pl.append(x)

                if game.teams > 1:
                    print(pl)
                    game_functions.create_random_teams(pl)
                    teams = []
                    for x in Team.objects.filter(gameID = game.id):
                        teams.append(x)
                    
                    print(teams)

                    teams = game_functions.randomize_array(teams)
                    


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
                        game_functions.assign_team_initial_bijection(x.id,x.targetID)

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

                # send_email("gamestart",info)
                try:
                    mod = Mod.objects.get(gameID = gameID)
                    subject = 'Game ' + views_functions.convertTo64(gameID) +' has started!'
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



def modKill(request,assassinPlayerID, assassinatedPlayerID, gameID):
    try:
        Mod.objects.get(gameID = gameID,userID = request.session['user'])
        assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
        assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
        if assassinated.alive and assassin.alive:
            game_functions.completeKill(assassinPlayerID,assassinatedPlayerID,gameID)
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
            game_functions.reverseDeath(assassinPlayerID,assassinatedPlayerID,gameID)
            return HttpResponseRedirect(reverse('game', kwargs={'gameID':gameID}))
        return HttpResponseRedirect(reverse('game', kwargs={'gameID':gameID}))
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
            game_functions.doubleConf(Player.objects.get(targetID = killedID).id, killedID, p.gameID)
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
                game_functions.doubleConf(playerID, p.targetID, p.gameID)
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID':p.gameID}))

            else:
                p.killConfirmed = False
                p.save()
                return HttpResponseRedirect(reverse('game', kwargs = {'gameID':p.gameID}))

    except Exception:
        print(traceback.print_exc())
        return HttpResponseRedirect(reverse('index'))
    
def deletePlayer(request,playerID,gameID):
    if views_functions.signedIn(request):
        try:
            if request.session['user'] == Mod.objects.get(gameID = gameID).userID:
                if (Game.objects.get(id = gameID).phase == 0):
                    Player.objects.get(id = playerID).delete()
                    return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))

            return HttpResponseRedirect(reverse('index'))

        except:
            return HttpResponseRedirect(reverse('index'))

    return HttpResponseRedirect(reverse('login'))


def modHelp(request):
        template = loader.get_template('db/mod-help.html')
        info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
        return HttpResponse(template.render(info,request))

def deleteGame(request,gameID):
    if views_functions.signedIn(request):
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
    if views_functions.signedIn(request):
        try:
            Player.objects.get(userID = request.session['user'],gameID = gameID)
            template = loader.get_template('db/mod-contact.html')
            email = ""
            g = Game.objects.get(id = gameID)
            if g.email:
                email = User.objects.get(id = Mod.objects.get(gameID = gameID).userID).email
            info = {'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request), 'phone':g.phone, 'email':email,'contact':g.otherContactInfo, 'id': views_functions.convertTo64(g.id),'gameID': gameID}
            return HttpResponse(template.render(info,request))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))



def gameSettingsPost(request, gameID):
    if views_functions.signedIn(request):
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



def gameSettings(request, gameID):
    if views_functions.signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            game = Game.objects.get(id = gameID)
            if (game.phase == 0 or game.phase == 1):
                info = {'gameID' : gameID,'witnessProtection': game.WitnessProtection, 'limit':game.limit,'circumstances': game.SafetyCircumstances, 'killMethod': game.KillMethod, 'killCam':game.killCam, 'extraRules': game.ExtraRules, 'contactInfo':game.otherContactInfo, 'email':game.email, 'phone': game.phone, '64id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
                template = loader.get_template('db/game-mod-settings.html')
                return HttpResponse(template.render(info,request))
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))

def duelSubmission(request,gameID):
    if views_functions.signedIn(request):
        try:
            Mod.objects.get(gameID = gameID, userID = request.session['user'])
            game = Game.objects.get(id = gameID)
            if (game.phase == 1):
                info = {'gameID' : gameID,'64id':views_functions.convertTo64(gameID),'signedIn':views_functions.signedIn(request), 'user':views_functions.getUser(request)}
                template = loader.get_template('db/game-mod-duel-submission.html')
                return HttpResponse(template.render(info,request))
            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))
        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login')) 

def duelSubmissionPost(request, gameID):
    if views_functions.signedIn(request):
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

            finished = game_functions.checkFinished(gameID)

            return HttpResponseRedirect(reverse('game', kwargs = {'gameID':gameID}))

        except:
            print(traceback.print_exc())
            return HttpResponseRedirect(reverse('index'))
    return HttpResponseRedirect(reverse('login'))

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
