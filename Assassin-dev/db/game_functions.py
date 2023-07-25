from .models import Game, Player, Mod, Kill, KillVideo, Profile, Team
from django.contrib.auth.models import User
import random
from datetime import *
import traceback
from django.template.loader import render_to_string
from . import extra_views


def randomize_array(array):
    randomArr = []
    for x in range(len(array)):
        randomNum = random.randint(0,len(array)-1)
        randomArr.append(array[randomNum])
        array.pop(randomNum)

    return randomArr

def completeKill(assassinPlayerID, assassinatedPlayerID, gameID):
    assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
    assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
    game = Game.objects.get(id = gameID)
    assassinatedTargetID = assassinated.targetID
    k = Kill(gameID = gameID, killerID = assassin.id, killedID = assassinated.id, timeKilled = datetime.now())
    k.save()

    assassin.kills = assassin.kills + 1
    assassin.score = assassin.score + 100
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
            # send_mail(subject, plain_message,'"Assassin Live" <info@assassin.live>',[User.objects.get(id = assassin.userID).email], html_message = html_message, fail_silently=False)
        except:
            print(traceback.print_exc())



def reverseDeath(assassinPlayerID, assassinatedPlayerID, gameID):
    assassinated = Player.objects.get(id = assassinatedPlayerID, gameID = gameID)
    assassin = Player.objects.get(id = assassinPlayerID, gameID = gameID)
    assassinTargetID = assassin.targetID
    k = Kill.objects.get(gameID = gameID, killerID = assassin.id, killedID = assassinated.id)
    k.delete()
    assassin.targetID = assassinatedPlayerID
    assassin.kills = assassin.kills - 1
    assassin.score = assassin.score - 100
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
            extra_views.deleteKillVideo(kv.id)
        except:
            print(traceback.print_exc())



def assign_team_initial_bijection(attackingTeam,defendingTeam):
    ## initially assigns a bijection from attackingTeam to defendingTeam, unless |defendingTeam| < |attackingTeam|, then assigns a target twice

    defending = []
    attacking = []

    for x in Player.objects.filter(teamID = defendingTeam, alive = True):
        defending.append(x)

    for x in Player.objects.filter(teamID = attackingTeam, alive = True):
        attacking.append(x)

    defending = randomize_array(defending)
    for x in range(len(attacking)):
        if x >= len(defending)-1:
            attacking[x].targetID = defending[len(defending)-1].id
            attacking[x].save()
        else:
            attacking[x].targetID = defending[x].id
            attacking[x].save()

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
    
        if (g.teams > 1):
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
        # startComp(gameID)
        info = []

        for x in Player.objects.filter(gameID = gameID):
            try:
                info.append({'gameID':gameID,'champID':champion.userID,'champName':User.objects.get(id = champion.userID).username,'email':User.objects.get(id = x.userID).email})
            except:
                print(traceback.print_exc())

        try:
            info.append({'gameID':gameID,'champID':champion.userID,'champName':User.objects.get(id = champion.userID).username,'email':User.objects.get(id = mod.userID).email})
            # send_email("gamefinish",info)
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


